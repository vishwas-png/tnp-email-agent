from fastapi import FastAPI, Depends
from sqlmodel import Session
from backend.db.database import get_session
from backend.db.crud import get_verified_notices,to_ist


app = FastAPI()

@app.get("/notices")
def read_notices(session: Session = Depends(get_session)):
    results = get_verified_notices(session)

    notices = []
    for email, extraction in results:
        notices.append({
            "subject": email.subject,
            "received_at": to_ist(email.received_at),
            "company_name": extraction.company_name,
            "deadline": to_ist(extraction.deadline),
            "summary": extraction.summary,
            "action_items": extraction.action_items,
        })

    return notices