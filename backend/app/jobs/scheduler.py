"""APScheduler configuration for automated data collection."""

import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def _job_wrapper(job_name: str, fn, *args):
    """Run a job with its own DB session and error handling."""
    logger.info("Starting scheduled job: %s", job_name)
    db = SessionLocal()
    try:
        result = fn(db, *args)
        logger.info("Completed job %s: %s", job_name, result)
    except Exception:
        logger.exception("Job %s failed", job_name)
    finally:
        db.close()


def job_sync_stocks():
    """Sync KOSPI and KOSDAQ stock lists."""
    from app.services.market_data import sync_stock_list

    _job_wrapper("sync_stocks", sync_stock_list, "ALL")


def job_fetch_daily_prices():
    """Fetch today's OHLCV data."""
    from app.services.market_data import fetch_daily_prices

    _job_wrapper("fetch_daily_prices", fetch_daily_prices, date.today(), "ALL")


def job_detect_volume_spikes():
    """Detect stocks with unusual volume."""
    from app.services.screener_service import get_volume_spikes

    _job_wrapper("detect_volume_spikes", get_volume_spikes, None, 2.0, 100)


def job_fetch_disclosures():
    """Fetch DART disclosures for today."""
    from app.services.dart_service import fetch_disclosures_by_date

    _job_wrapper("fetch_disclosures", fetch_disclosures_by_date, date.today())


def job_fetch_news():
    """Fetch news for top movers (high volume/change stocks)."""
    from app.services.news_service import fetch_news_for_top_movers

    _job_wrapper("fetch_news", fetch_news_for_top_movers)


def init_scheduler():
    """Initialize and start the scheduler with all jobs."""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return

    # Weekdays only (mon-fri)

    # 09:30~15:30 KST - Sync during market hours (every 30 min)
    scheduler.add_job(
        job_sync_stocks,
        CronTrigger(hour="9-15", minute="0,30", day_of_week="mon-fri"),
        id="sync_stocks_market_hours",
        replace_existing=True,
    )

    # 18:30 KST - Final sync after market close
    scheduler.add_job(
        job_sync_stocks,
        CronTrigger(hour=18, minute=30, day_of_week="mon-fri"),
        id="sync_stocks",
        replace_existing=True,
    )

    # 18:45 KST - Fetch daily prices (after market close)
    scheduler.add_job(
        job_fetch_daily_prices,
        CronTrigger(hour=18, minute=45, day_of_week="mon-fri"),
        id="fetch_daily_prices",
        replace_existing=True,
    )

    # 19:00 KST - Detect volume spikes
    scheduler.add_job(
        job_detect_volume_spikes,
        CronTrigger(hour=19, minute=0, day_of_week="mon-fri"),
        id="detect_volume_spikes",
        replace_existing=True,
    )

    # 19:30 KST - Fetch DART disclosures
    scheduler.add_job(
        job_fetch_disclosures,
        CronTrigger(hour=19, minute=30, day_of_week="mon-fri"),
        id="fetch_disclosures",
        replace_existing=True,
    )

    # 20:00 KST - Fetch news for top movers
    scheduler.add_job(
        job_fetch_news,
        CronTrigger(hour=20, minute=0, day_of_week="mon-fri"),
        id="fetch_news",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")


def get_scheduler_status() -> dict:
    """Return scheduler status and job info."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": scheduler.running,
        "jobs": jobs,
    }
