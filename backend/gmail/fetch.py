import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from backend.schemas.models import RawEmail
from backend.timeutils import as_utc
from bs4 import BeautifulSoup
import re

TNP_SENDER = 'tnpcell@nsitonline.in'
MAX_EMAILS_PER_RUN = 50     # caps LLM calls per run; the rest are picked up next run
INITIAL_SYNC_DAYS = 30      # a brand-new user only gets the last month, not years of mail

# A reply header like "On Mon, 5 Oct 2026 at 10:00, TNP <x> wrote:" on its own line
# (Gmail sometimes wraps it onto a second line). Everything after it is the quoted thread.
QUOTE_HEADER = re.compile(r"^[ \t]*On\b[^\n]*(?:\n[^\n]*)?\bwrote:[ \t]*$", re.MULTILINE)


def strip_quoted_reply(body: str) -> str:
    match = QUOTE_HEADER.search(body)
    return body[:match.start()] if match else body


def decode_part(data: str) -> str:
    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')


def extract_body(parts):
    plain = ''
    html = ''
    for part in parts:
        mime = part.get('mimeType', '')
        # multipart containers hold more parts, so search inside recursively
        if 'parts' in part:
            nested_plain, nested_html = extract_body(part['parts'])
            if nested_plain:
                plain = nested_plain
            if nested_html:
                html = nested_html
        elif mime == 'text/plain':
            data = part['body'].get('data', '')
            if data:
                plain = decode_part(data)
        elif mime == 'text/html':
            data = part['body'].get('data', '')
            if data:
                html = decode_part(data)
    return plain, html


def get_body(payload) -> str:
    if 'parts' in payload:
        plain, html = extract_body(payload['parts'])
    else:
        data = payload.get('body', {}).get('data', '')
        text = decode_part(data) if data else ''
        is_html = payload.get('mimeType') == 'text/html'
        plain, html = ('', text) if is_html else (text, '')

    if plain:
        return plain
    if html:
        return BeautifulSoup(html, 'html.parser').get_text()
    return ''


def list_message_ids(service, query: str) -> list[str]:
    # Gmail returns at most one page per call, newest first. Follow nextPageToken.
    ids = []
    page_token = None
    while True:
        response = service.users().messages().list(
            userId='me', q=query, pageToken=page_token, maxResults=500
        ).execute()
        ids.extend(m['id'] for m in response.get('messages', []))
        page_token = response.get('nextPageToken')
        if not page_token:
            return ids


def fetch_tnp_emails(service, after: datetime | None = None) -> list[RawEmail]:
    query = f'from:{TNP_SENDER}'
    if after:
        query += f' after:{int(after.timestamp())}'
    else:
        query += f' newer_than:{INITIAL_SYNC_DAYS}d'

    ids = list_message_ids(service, query)
    if not ids:
        print("No new emails from TNP.")
        return []

    # Oldest first, and only the oldest MAX_EMAILS_PER_RUN. The caller's bookmark is the
    # newest saved email, so processing newest first would skip the older ones for good.
    ids = list(reversed(ids))[:MAX_EMAILS_PER_RUN]

    results = []
    for message_id in ids:
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()

        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        date_str = next((h['value'] for h in headers if h['name'] == 'Date'), None)

        received_at = datetime.now(timezone.utc)  # fallback
        if date_str:
            try:
                # "-0000" dates parse as naive, so normalise to UTC
                received_at = as_utc(parsedate_to_datetime(date_str))
            except Exception:
                pass

        results.append(RawEmail(
            gmail_message_id=message_id,
            subject=subject,
            body=strip_quoted_reply(get_body(message.get('payload', {}))),
            received_at=received_at,
        ))

    results.sort(key=lambda e: e.received_at)
    return results
