import json
import os
from dotenv import load_dotenv
from pywebpush import webpush
from sqlmodel import Session, select
from backend.db.models import PushSubscriptionDB

load_dotenv()

VAPID_PRIVATE_KEY_PATH = os.getenv("VAPID_PRIVATE_KEY_PATH")

def send_push_notification(session,user_id,title,body):
        subscriptions = session.exec(
        select(PushSubscriptionDB).where(PushSubscriptionDB.user_id == user_id)).all()

        for sub in subscriptions:
          subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
        }
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=VAPID_PRIVATE_KEY_PATH,
            vapid_claims={"sub": "mailto:you@example.com"}
        )