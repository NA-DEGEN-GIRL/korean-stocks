"""Momentum scoring service for early stock discovery."""

import logging
from datetime import date, timedelta

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.stock import DailyPrice, Stock

logger = logging.getLogger(__name__)


def calculate_momentum_score(db: Session, ticker: str) -> float | None:
    """Calculate composite momentum score (0-100) for a stock.

    Components (weights):
    - 5-day return: 15%
    - 20-day return: 20%
    - 5-day volume ratio vs 20-day avg: 20%
    - Price vs 20-day MA: 15%
    - Price vs 60-day MA: 10%
    - Proximity to 52-week high: 10%
    - Consecutive up days: 10%
    """
    latest_date = db.query(func.max(DailyPrice.date)).filter(
        DailyPrice.ticker == ticker
    ).scalar()
    if not latest_date:
        return None

    # Get recent prices (last 60+ trading days)
    prices = (
        db.query(DailyPrice)
        .filter(
            DailyPrice.ticker == ticker,
            DailyPrice.date >= latest_date - timedelta(days=90),
        )
        .order_by(DailyPrice.date)
        .all()
    )

    if len(prices) < 10:
        return None

    closes = [p.close for p in prices if p.close and p.close > 0]
    volumes = [p.volume for p in prices if p.volume and p.volume > 0]

    if len(closes) < 10 or len(volumes) < 10:
        return None

    current_price = closes[-1]
    score = 0.0

    # 1. 5-day return (15%)
    if len(closes) >= 6:
        ret_5d = (current_price - closes[-6]) / closes[-6] * 100
        score += _normalize(ret_5d, -10, 15) * 0.15

    # 2. 20-day return (20%)
    if len(closes) >= 21:
        ret_20d = (current_price - closes[-21]) / closes[-21] * 100
        score += _normalize(ret_20d, -20, 30) * 0.20

    # 3. Volume ratio: 5-day avg vs 20-day avg (20%)
    if len(volumes) >= 20:
        vol_5d = sum(volumes[-5:]) / 5
        vol_20d = sum(volumes[-20:]) / 20
        vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1
        score += _normalize(vol_ratio, 0.5, 3.0) * 0.20

    # 4. Price vs 20-day MA (15%)
    if len(closes) >= 20:
        ma_20 = sum(closes[-20:]) / 20
        pct_above_ma20 = (current_price - ma_20) / ma_20 * 100
        score += _normalize(pct_above_ma20, -10, 15) * 0.15

    # 5. Price vs 60-day MA (10%)
    if len(closes) >= 60:
        ma_60 = sum(closes[-60:]) / 60
        pct_above_ma60 = (current_price - ma_60) / ma_60 * 100
        score += _normalize(pct_above_ma60, -15, 25) * 0.10

    # 6. Proximity to 52-week high (10%)
    all_prices = (
        db.query(func.max(DailyPrice.high))
        .filter(
            DailyPrice.ticker == ticker,
            DailyPrice.date >= latest_date - timedelta(weeks=52),
        )
        .scalar()
    )
    if all_prices and all_prices > 0:
        high_proximity = current_price / all_prices * 100
        score += _normalize(high_proximity, 60, 100) * 0.10

    # 7. Consecutive up days (10%)
    consecutive = 0
    for i in range(len(closes) - 1, 0, -1):
        if closes[i] > closes[i - 1]:
            consecutive += 1
        else:
            break
    score += _normalize(consecutive, 0, 7) * 0.10

    return round(min(max(score * 100, 0), 100), 1)


def _normalize(value: float, low: float, high: float) -> float:
    """Normalize a value to 0-1 range based on expected low/high bounds."""
    if high == low:
        return 0.5
    normalized = (value - low) / (high - low)
    return min(max(normalized, 0), 1)


def get_momentum_rankings(
    db: Session,
    market: str | None = None,
    min_score: float = 0,
    limit: int = 30,
) -> list[dict]:
    """Calculate momentum scores for all stocks and return top ranked.

    For efficiency, only calculates for stocks with recent price data
    and significant trading volume.
    """
    latest_date = db.query(func.max(DailyPrice.date)).scalar()
    if not latest_date:
        return []

    # Get active stocks with recent prices and minimum volume
    query = (
        db.query(DailyPrice, Stock)
        .join(Stock, Stock.ticker == DailyPrice.ticker)
        .filter(
            DailyPrice.date == latest_date,
            DailyPrice.volume > 10000,
            DailyPrice.close > 1000,
            Stock.is_active.is_(True),
        )
    )
    if market:
        query = query.filter(Stock.market == market.upper())

    candidates = query.all()
    scored = []

    for price, stock in candidates:
        score = calculate_momentum_score(db, stock.ticker)
        if score is not None and score >= min_score:
            from app.models.stock import MarketFundamentals
            fund = (
                db.query(MarketFundamentals)
                .filter(MarketFundamentals.ticker == stock.ticker)
                .order_by(desc(MarketFundamentals.date))
                .first()
            )
            scored.append({
                "ticker": stock.ticker,
                "name": stock.name,
                "market": stock.market,
                "close": price.close,
                "change_pct": round(price.change_pct, 2) if price.change_pct else 0,
                "volume": price.volume,
                "volume_ratio": None,
                "momentum_score": score,
                "market_cap": fund.market_cap if fund else None,
            })

    scored.sort(key=lambda x: x["momentum_score"] or 0, reverse=True)
    return scored[:limit]
