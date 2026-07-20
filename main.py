from backend.gmail.fetch import fetch_tnp_emails
import json
from backend.graph.nodes.extract import extract_info

if __name__ == "__main__":
    emails = fetch_tnp_emails()
    
    for email in emails:
         extracted_info=extract_info(email)
         print(f"\n--- {email.subject} ---")
         result = extracted_info
         print(result.model_dump_json(indent=2))
         