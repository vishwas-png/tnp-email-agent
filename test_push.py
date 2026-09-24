from sqlmodel import Session
from backend.db.database import engine
from backend.notification.push import send_push_notification

with Session(engine) as session:
    send_push_notification(
        session=session,
        user_id=1,
        title="Test Notification",
        body="This is a test push notification from your backend."
    )