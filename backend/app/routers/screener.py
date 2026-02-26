"""Screener endpoints: top gainers/losers, volume spikes, new highs, momentum."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.screener import ScreenerItem, ScreenerResponse
from app.services.screener_service import (
    get_top_gainers,
    get_top_losers,
    get_volume_spikes,
    get_new_highs,
)
from app.services.momentum_service import get_momentum_rankings

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.get("/top-gainers", response_model=ScreenerResponse)
def top_gainers(
    market: str | None = Query(None, description="KOSPI, KOSDAQ, or omit for all"),
    period: str = Query("1d", description="1d, 1w, or 1m"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScreenerResponse:
    """Get stocks with the highest price change."""
    items = get_top_gainers(db, market, period, limit)
    return ScreenerResponse(
        items=[ScreenerItem(**i) for i in items],
        total=len(items),
    )


@router.get("/top-losers", response_model=ScreenerResponse)
def top_losers(
    market: str | None = Query(None),
    period: str = Query("1d"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScreenerResponse:
    """Get stocks with the lowest price change."""
    items = get_top_losers(db, market, period, limit)
    return ScreenerResponse(
        items=[ScreenerItem(**i) for i in items],
        total=len(items),
    )


@router.get("/volume-spikes", response_model=ScreenerResponse)
def volume_spikes(
    market: str | None = Query(None),
    min_ratio: float = Query(2.0, ge=1.0, description="Minimum volume spike ratio"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScreenerResponse:
    """Get stocks with unusual volume (today vs 20-day average)."""
    items = get_volume_spikes(db, market, min_ratio, limit)
    return ScreenerResponse(
        items=[ScreenerItem(**i) for i in items],
        total=len(items),
    )


@router.get("/new-highs", response_model=ScreenerResponse)
def new_highs(
    market: str | None = Query(None),
    period_weeks: int = Query(52, description="Period in weeks for high calculation"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScreenerResponse:
    """Get stocks at or near their period high."""
    items = get_new_highs(db, market, period_weeks, limit)
    return ScreenerResponse(
        items=[ScreenerItem(**i) for i in items],
        total=len(items),
    )


@router.get("/momentum", response_model=ScreenerResponse)
def momentum(
    market: str | None = Query(None),
    min_score: float = Query(0, ge=0, le=100),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScreenerResponse:
    """Get stocks ranked by momentum score (0-100).

    Note: This endpoint is slower as it calculates scores on the fly.
    Consider using smaller limits or filtering by market.
    """
    items = get_momentum_rankings(db, market, min_score, limit)
    return ScreenerResponse(
        items=[ScreenerItem(**i) for i in items],
        total=len(items),
    )
