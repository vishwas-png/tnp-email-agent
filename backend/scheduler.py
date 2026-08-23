from apscheduler.schedulers.background import BackgroundScheduler
import time
from backend.pipeline import run_pipeline

scheduler = BackgroundScheduler()
scheduler.add_job(run_pipeline, 'interval', minutes=5)
scheduler.start()

print("Scheduler started. Polling every 5 minutes. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    print("Scheduler stopped.")