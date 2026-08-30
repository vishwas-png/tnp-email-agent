import base64
from datetime import datetime
from backend.auth.gmail_auth import get_gmail_service
from backend.schemas.models import RawEmail
from bs4 import BeautifulSoup
import json
import re

TNP_SENDER = 'tnpcell@nsitonline.in'
MAX_EMAILS = 100  # for testing only 

def fetch_tnp_emails(service,after: datetime | None = None) -> list[RawEmail]:
    results = []
     

    query = f'from:{TNP_SENDER}'
    if after:
        query += f' after:{int(after.timestamp())}'

    response = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=MAX_EMAILS
    ).execute()

    messages = response.get('messages', [])

    if not messages:
        print("No new emails from TNP.")
        return results

    # for each ID, fetch full email content
    for msg in messages:
        message = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        # extract fields from raw API response
        headers = message['payload']['headers']
        subject = next(
            (h['value'] for h in headers if h['name'] == 'Subject'), 
            'No Subject'
        )
        date_str = next(
            (h['value'] for h in headers if h['name'] == 'Date'), 
            None
        )
        received_at = datetime.now()  # fallback
        if date_str:
            try:
                from email.utils import parsedate_to_datetime
                received_at = parsedate_to_datetime(date_str)
            except Exception:
                pass

## ---------------------extraction recursive function to extract threads---------------------------------------------------------------------
        def extract_body(parts):
         plain = ''
         html = ''
    
         for part in parts:
          mime = part.get('mimeType', '')
        
        # if this part has nested parts, search inside recursively
          if 'parts' in part:
            nested_plain, nested_html = extract_body(part['parts'])
            if nested_plain:
                plain = nested_plain
            if nested_html:
                html = nested_html
                
          elif mime == 'text/plain':
            data = part['body'].get('data', '')
            if data:
                plain = base64.urlsafe_b64decode(data).decode('utf-8')
                
          elif mime == 'text/html':
            data = part['body'].get('data', '')
            if data:
                html = base64.urlsafe_b64decode(data).decode('utf-8')
    
         return plain, html
        
##------------------------------------------------------------------------------------------------------------------------------------
        
         # extract body
        body = ''
        payload = message.get('payload', {})
        if 'parts' in payload:
           plain, html = extract_body(payload['parts'])
           if plain:
            body = plain
           elif html:
            body = BeautifulSoup(html, 'html.parser').get_text()
       
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            body = base64.urlsafe_b64decode(data).decode('utf-8')

        
        body= re.split(r"On .+ wrote:",body,flags=re.DOTALL)[0]

        raw_email = RawEmail(
            gmail_message_id=msg['id'],
            subject=subject,
            body=body,
            received_at=received_at
        )
        results.append(raw_email)

    
    return results