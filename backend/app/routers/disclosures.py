"""DART disclosure endpoints."""

from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.schemas.disclosure import DisclosureItem, DisclosureListResponse
from app.services.dart_service import (
    fetch_disclosures_by_date,
    fetch_disclosures_for_ticker,
    get_disclosures,
)

router = APIRouter(prefix="/api/disclosures", tags=["disclosures"])


@router.get("", response_model=DisclosureListResponse)
def list_disclosures(
    ticker: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> DisclosureListResponse:
    """List disclosures from DB with optional filters."""
    items = get_disclosures(db, ticker=ticker, start_date=start_date, end_date=end_date, limit=limit)
    return DisclosureListResponse(
        items=[DisclosureItem.model_validate(d) for d in items],
        total=len(items),
    )


@router.post("/fetch/{ticker}")
def fetch_ticker_disclosures(
    ticker: str,
    background_tasks: BackgroundTasks,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
) -> dict:
    """Trigger fetching disclosures for a specific ticker from DART."""

    def _run():
        db = SessionLocal()
        try:
            fetch_disclosures_for_ticker(db, ticker, start_date, end_date)
        finally:
            db.close()

    background_tasks.add_task(_run)
    return {"status": "fetching", "ticker": ticker}


@router.post("/fetch-date")
def fetch_date_disclosures(
    background_tasks: BackgroundTasks,
    target_date: date | None = Query(None),
) -> dict:
    """Trigger fetching all disclosures for a given date from DART."""

    def _run():
        db = SessionLocal()
        try:
            fetch_disclosures_by_date(db, target_date)
        finally:
            db.close()

    background_tasks.add_task(_run)
    return {"status": "fetching", "date": str(target_date or date.today())}
