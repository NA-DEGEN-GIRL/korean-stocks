"""DART disclosure endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.models.disclosure import DartDisclosure
from app.schemas.disclosure import DisclosureItem, DisclosureListResponse
from app.services.dart_service import (
    fetch_disclosures_by_date,
    fetch_disclosures_for_ticker,
    get_disclosures,
)


def verify_admin(x_admin_key: str = Header()):
    if not settings.ADMIN_KEY or x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

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


@router.get("/unanalyzed", response_model=DisclosureListResponse)
def list_unanalyzed(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DisclosureListResponse:
    """List disclosures that have not been analyzed by AI yet."""
    items = (
        db.query(DartDisclosure)
        .filter(DartDisclosure.ai_summary.is_(None))
        .order_by(DartDisclosure.rcept_dt.desc())
        .limit(limit)
        .all()
    )
    return DisclosureListResponse(
        items=[DisclosureItem.model_validate(d) for d in items],
        total=len(items),
    )


class AnalysisSubmission(BaseModel):
    ai_summary: str
    ai_impact: str  # "긍정", "부정", "중립"


@router.post("/{disclosure_id}/analysis", dependencies=[Depends(verify_admin)])
def submit_analysis(
    disclosure_id: int,
    body: AnalysisSubmission,
    db: Session = Depends(get_db),
) -> dict:
    """Submit AI analysis for a disclosure."""
    disc = db.query(DartDisclosure).filter(DartDisclosure.id == disclosure_id).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Disclosure not found")

    disc.ai_summary = body.ai_summary
    disc.ai_impact = body.ai_impact
    disc.ai_analyzed_at = datetime.utcnow()
    db.commit()

    return {"status": "ok", "disclosure_id": disclosure_id, "ai_impact": body.ai_impact}
