from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .utils import fetch_and_save_news
import atexit

def start():
    scheduler = BackgroundScheduler()
    # Schedule the job every day at midnight or e.g. every hour (for demo let's say every hour)
    trigger = CronTrigger(minute="0", hour="*")
    scheduler.add_job(
        fetch_and_save_news,
        trigger=trigger,
        id="fetch_daily_news",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
