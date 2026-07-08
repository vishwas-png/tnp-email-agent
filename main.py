from backend.gmail.fetch import fetch_tnp_emails
import json

if __name__ == "__main__":
    emails = fetch_tnp_emails()
    for email in emails:
        print(json.dumps(email.model_dump(), indent=2, default=str))