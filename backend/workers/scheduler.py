"""RQ Scheduler for periodic tasks."""
import logging
from rq_scheduler import Scheduler
from redis import Redis
from datetime import datetime, timedelta
from config import settings
from workers.jobs import (
    sync_google_calendar_job,
    generate_weekly_report_job,
    generate_monthly_report_job,
    nightly_summarizer_job
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_conn = Redis.from_url(settings.redis_url)
scheduler = Scheduler(connection=redis_conn, queue_name="zyana-queue")


def setup_scheduled_jobs():
    """Setup all scheduled jobs."""
    logger.info("Setting up scheduled jobs...")
    
    # Clear existing jobs
    for job in scheduler.get_jobs():
        scheduler.cancel(job)
    
    # Hourly: Google Calendar sync
    scheduler.cron(
        "0 * * * *",  # Every hour at minute 0
        func=sync_google_calendar_job,
        args=[1],  # user_id
        id="google_calendar_sync",
        timeout=300
    )
    logger.info("✓ Scheduled: Google Calendar sync (hourly)")
    
    # Daily 2 AM: Nightly summarizer
    scheduler.cron(
        "0 2 * * *",  # Every day at 2 AM
        func=nightly_summarizer_job,
        args=[1],  # user_id
        id="nightly_summarizer",
        timeout=600
    )
    logger.info("✓ Scheduled: Nightly summarizer (daily 2 AM)")
    
    # Weekly Monday 9 AM: Weekly report
    scheduler.cron(
        "0 9 * * 1",  # Every Monday at 9 AM
        func=generate_weekly_report_job,
        args=[1],  # user_id
        id="weekly_report",
        timeout=300
    )
    logger.info("✓ Scheduled: Weekly report (Monday 9 AM)")
    
    # Monthly 1st at 9 AM: Monthly report
    scheduler.cron(
        "0 9 1 * *",  # 1st of month at 9 AM
        func=generate_monthly_report_job,
        args=[1],  # user_id
        id="monthly_report",
        timeout=600
    )
    logger.info("✓ Scheduled: Monthly report (1st of month, 9 AM)")
    
    logger.info("✅ All scheduled jobs set up successfully")


if __name__ == "__main__":
    setup_scheduled_jobs()
    logger.info("🔄 Scheduler is running...")
    
    # Keep scheduler alive
    while True:
        scheduler.run(burst=False)

