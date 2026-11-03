import json
import os
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException
from sqlmodel import select
from backend.db.models import PushSubscriptionDB

load_dotenv()

VAPID_PRIVATE_KEY_PATH = os.getenv("VAPID_PRIVATE_KEY_PATH")

# 404/410 from the push service means the subscription is gone for good
# (user revoked permission, cleared site data, or the browser rotated it).
DEAD_SUBSCRIPTION_CODES = (404, 410)


def send_push_notification(session, user_id, title, body):
    subscriptions = session.exec(
        select(PushSubscriptionDB).where(PushSubscriptionDB.user_id == user_id)
    ).all()

    sent = 0
    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        # One failing device must not stop the others.
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps({"title": title, "body": body}),
                vapid_private_key=VAPID_PRIVATE_KEY_PATH,
                vapid_claims={"sub": "mailto:you@example.com"},
            )
            sent += 1
        except WebPushException as e:
            if e.status_code in DEAD_SUBSCRIPTION_CODES:
                print(f"Removing dead push subscription {sub.id} (HTTP {e.status_code})")
                session.delete(sub)
            else:
                print(f"Push failed for subscription {sub.id}: HTTP {e.status_code}")
        except Exception as e:
            print(f"Push failed for subscription {sub.id}: {e}")

    session.commit()
    return sent
