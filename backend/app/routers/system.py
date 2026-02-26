"""System endpoints for data collection, backfill, and status checks."""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, SessionLocal


def verify_admin(x_admin_key: str = Header()):
    """Verify admin key from request header."""
    if not settings.ADMIN_KEY or x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
from app.models.stock import DailyPrice, MarketFundamentals, Stock
from app.models.disclosure import DartDisclosure
from app.models.news import NewsArticle
from app.jobs.scheduler import get_scheduler_status, job_sync_stocks, job_fetch_daily_prices, job_detect_volume_spikes, job_fetch_disclosures, job_fetch_news
from app.services.market_data import (
    backfill_prices,
    fetch_daily_prices,
    sync_stock_list,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def get_system_status(db: Session = Depends(get_db)) -> dict:
    """Return system status including data counts and last update times."""
    stock_count = db.query(func.count(Stock.ticker)).scalar() or 0
    price_count = db.query(func.count(DailyPrice.id)).scalar() or 0
    fund_count = db.query(func.count(MarketFundamentals.id)).scalar() or 0
    disclosure_count = db.query(func.count(DartDisclosure.id)).scalar() or 0
    news_count = db.query(func.count(NewsArticle.id)).scalar() or 0

    latest_price_date = db.query(func.max(DailyPrice.date)).scalar()
    latest_fund_date = db.query(func.max(MarketFundamentals.date)).scalar()

    return {
        "status": "ok",
        "data": {
            "stocks": stock_count,
            "daily_prices": price_count,
            "fundamentals": fund_count,
            "disclosures": disclosure_count,
            "news_articles": news_count,
        },
        "latest_dates": {
            "prices": str(latest_price_date) if latest_price_date else None,
            "fundamentals": str(latest_fund_date) if latest_fund_date else None,
        },
    }


def _run_sync_stocks(market: str):
    """Background task: sync stock list."""
    db = SessionLocal()
    try:
        count = sync_stock_list(db, market)
        logger.info(f"Background sync complete: {count} stocks")
    except Exception as e:
        logger.error(f"Background sync failed: {e}")
    finally:
        db.close()


def _run_daily_prices(target_date: date, market: str):
    """Background task: fetch daily prices."""
    db = SessionLocal()
    try:
        count = fetch_daily_prices(db, target_date, market)
        logger.info(f"Background daily prices complete: {count} records for {target_date}")
    except Exception as e:
        logger.error(f"Background daily prices failed: {e}")
    finally:
        db.close()


def _run_backfill(start_date: date, end_date: date, market: str):
    """Background task: backfill prices, disclosures, and news."""
    from app.services.dart_service import fetch_disclosures_for_ticker
    from app.services.news_service import fetch_news_for_ticker
    import time

    db = SessionLocal()
    try:
        # 1) Backfill prices
        results = backfill_prices(db, start_date, end_date, market)
        logger.info(f"Background backfill prices complete: {results}")

        # 2) Backfill disclosures & news for all active stocks
        stocks = db.query(Stock).filter(Stock.is_active.is_(True)).all()
        disc_count = 0
        news_count = 0

        for i, stock in enumerate(stocks):
            try:
                discs = fetch_disclosures_for_ticker(db, stock.ticker, start_date, end_date)
                disc_count += len(discs)
            except Exception as e:
                logger.error(f"Disclosure backfill failed for {stock.ticker}: {e}")

            try:
                articles = fetch_news_for_ticker(db, stock.ticker, pages=1)
                news_count += len(articles)
            except Exception as e:
                logger.error(f"News backfill failed for {stock.ticker}: {e}")

            if (i + 1) % 50 == 0:
                logger.info(f"Backfill disclosures/news progress: {i + 1}/{len(stocks)}")
            time.sleep(0.5)

        logger.info(f"Background backfill complete: prices={results}, disclosures={disc_count}, news={news_count}")
    except Exception as e:
        logger.error(f"Background backfill failed: {e}")
    finally:
        db.close()


@router.post("/sync-stocks", dependencies=[Depends(verify_admin)])
def trigger_sync_stocks(
    background_tasks: BackgroundTasks,
    market: str = Query("ALL", description="KOSPI, KOSDAQ, or ALL"),
) -> dict:
    """Trigger stock list sync in the background."""
    background_tasks.add_task(_run_sync_stocks, market)
    return {"status": "started", "job": "sync_stocks", "market": market}


@router.post("/fetch-prices", dependencies=[Depends(verify_admin)])
def trigger_fetch_prices(
    background_tasks: BackgroundTasks,
    target_date: str | None = Query(None, description="Date in YYYY-MM-DD format, defaults to today"),
    market: str = Query("ALL"),
) -> dict:
    """Trigger daily price fetch in the background."""
    d = date.fromisoformat(target_date) if target_date else date.today()
    background_tasks.add_task(_run_daily_prices, d, market)
    return {"status": "started", "job": "fetch_prices", "date": str(d), "market": market}


@router.post("/backfill", dependencies=[Depends(verify_admin)])
def trigger_backfill(
    background_tasks: BackgroundTasks,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD, defaults to today"),
    market: str = Query("ALL"),
) -> dict:
    """Trigger price backfill in the background."""
    sd = date.fromisoformat(start_date)
    ed = date.fromisoformat(end_date) if end_date else date.today()
    background_tasks.add_task(_run_backfill, sd, ed, market)
    return {
        "status": "started",
        "job": "backfill",
        "start_date": str(sd),
        "end_date": str(ed),
        "market": market,
    }


@router.get("/scheduler")
def scheduler_status() -> dict:
    """Return scheduler status and job schedule."""
    return get_scheduler_status()


JOB_MAP = {
    "sync_stocks": job_sync_stocks,
    "fetch_daily_prices": job_fetch_daily_prices,
    "detect_volume_spikes": job_detect_volume_spikes,
    "fetch_disclosures": job_fetch_disclosures,
    "fetch_news": job_fetch_news,
}


@router.post("/run-job/{job_name}", dependencies=[Depends(verify_admin)])
def run_job(
    job_name: str,
    background_tasks: BackgroundTasks,
) -> dict:
    """Manually trigger a scheduled job."""
    fn = JOB_MAP.get(job_name)
    if not fn:
        return {"status": "error", "message": f"Unknown job: {job_name}. Available: {list(JOB_MAP.keys())}"}
    background_tasks.add_task(fn)
    return {"status": "started", "job": job_name}
