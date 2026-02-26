"""Analysis endpoints: why-moving, weekly report."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analysis import WhyMovingResponse, WeeklyReportResponse
from app.services.analysis_service import analyze_why_moving

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/why-moving/{ticker}", response_model=WhyMovingResponse)
def why_is_stock_moving(
    ticker: str,
    target_date: date | None = Query(None, description="Date to analyze (default: today)"),
    db: Session = Depends(get_db),
) -> WhyMovingResponse:
    """Analyze why a stock is moving -- correlate price action with news and disclosures."""
    result = analyze_why_moving(db, ticker, target_date)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return WhyMovingResponse(
        ticker=result["ticker"],
        name=result["name"],
        date=date.fromisoformat(result["date"]),
        price_change_pct=result.get("price_change_pct"),
        volume_spike_ratio=result.get("volume_spike_ratio"),
        disclosures=result.get("disclosures", []),
        news=result.get("news", []),
        sector_comparison=result.get("sector_comparison", {}),
        summary=result.get("summary", ""),
    )


@router.get("/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    week_start: date | None = Query(None, description="Monday of the target week"),
    db: Session = Depends(get_db),
) -> WeeklyReportResponse:
    """Return the weekly market summary report."""
    # TODO: implement weekly report generation / retrieval in Phase 5
    raise HTTPException(status_code=501, detail="Weekly report engine not yet implemented")
