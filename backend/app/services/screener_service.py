"""Stock screening service: top gainers/losers, volume spikes, new highs."""

import logging
from datetime import date, timedelta

from sqlalchemy import desc, func, and_
from sqlalchemy.orm import Session

from app.models.stock import DailyPrice, MarketFundamentals, Stock
from app.models.analysis import VolumeSpike

logger = logging.getLogger(__name__)


def get_top_gainers(
    db: Session,
    market: str | None = None,
    period: str = "1d",
    limit: int = 20,
) -> list[dict]:
    """Get stocks with the highest price change.

    Args:
        period: '1d' for daily, '1w' for weekly, '1m' for monthly
    """
    if period == "1d":
        return _get_daily_movers(db, market, limit, ascending=False)
    else:
        return _get_period_movers(db, market, period, limit, ascending=False)


def get_top_losers(
    db: Session,
    market: str | None = None,
    period: str = "1d",
    limit: int = 20,
) -> list[dict]:
    """Get stocks with the lowest price change."""
    if period == "1d":
        return _get_daily_movers(db, market, limit, ascending=True)
    else:
        return _get_period_movers(db, market, period, limit, ascending=True)


def _get_daily_movers(
    db: Session,
    market: str | None,
    limit: int,
    ascending: bool,
) -> list[dict]:
    """Get top daily movers from the latest trading day's data."""
    latest_date = db.query(func.max(DailyPrice.date)).scalar()
    if not latest_date:
        return []

    query = (
        db.query(DailyPrice, Stock)
        .join(Stock, Stock.ticker == DailyPrice.ticker)
        .filter(
            DailyPrice.date == latest_date,
            DailyPrice.change_pct.isnot(None),
            DailyPrice.close > 0,
            Stock.is_active.is_(True),
        )
    )

    if market:
        query = query.filter(Stock.market == market.upper())

    order = DailyPrice.change_pct.asc() if ascending else DailyPrice.change_pct.desc()
    results = query.order_by(order).limit(limit).all()

    return [_build_screener_item(db, price, stock) for price, stock in results]


def _get_period_movers(
    db: Session,
    market: str | None,
    period: str,
    limit: int,
    ascending: bool,
) -> list[dict]:
    """Get movers over a period (1w or 1m) by comparing close prices."""
    latest_date = db.query(func.max(DailyPrice.date)).scalar()
    if not latest_date:
        return []

    days_back = 7 if period == "1w" else 30
    start_date = latest_date - timedelta(days=days_back)

    # Subquery: earliest close price in period per ticker
    start_sub = (
        db.query(
            DailyPrice.ticker,
            func.min(DailyPrice.date).label("first_date"),
        )
        .filter(DailyPrice.date >= start_date)
        .group_by(DailyPrice.ticker)
        .subquery()
    )

    start_prices = (
        db.query(DailyPrice.ticker, DailyPrice.close.label("start_close"))
        .join(start_sub, and_(
            DailyPrice.ticker == start_sub.c.ticker,
            DailyPrice.date == start_sub.c.first_date,
        ))
        .subquery()
    )

    # Current prices
    end_prices = (
        db.query(DailyPrice.ticker, DailyPrice.close.label("end_close"), DailyPrice.volume)
        .filter(DailyPrice.date == latest_date)
        .subquery()
    )

    # Calculate change %
    change_expr = (
        (end_prices.c.end_close - start_prices.c.start_close)
        * 100.0
        / func.nullif(start_prices.c.start_close, 0)
    ).label("period_change")

    query = (
        db.query(
            Stock,
            end_prices.c.end_close,
            end_prices.c.volume,
            start_prices.c.start_close,
            change_expr,
        )
        .join(end_prices, Stock.ticker == end_prices.c.ticker)
        .join(start_prices, Stock.ticker == start_prices.c.ticker)
        .filter(
            Stock.is_active.is_(True),
            start_prices.c.start_close > 0,
            end_prices.c.end_close > 0,
        )
    )

    if market:
        query = query.filter(Stock.market == market.upper())

    order = change_expr.asc() if ascending else change_expr.desc()
    results = query.order_by(order).limit(limit).all()

    items = []
    for stock, end_close, volume, start_close, period_change in results:
        fund = (
            db.query(MarketFundamentals)
            .filter(MarketFundamentals.ticker == stock.ticker)
            .order_by(desc(MarketFundamentals.date))
            .first()
        )
        items.append({
            "ticker": stock.ticker,
            "name": stock.name,
            "market": stock.market,
            "close": end_close,
            "change_pct": round(period_change, 2) if period_change else 0,
            "volume": volume,
            "volume_ratio": None,
            "momentum_score": None,
            "market_cap": fund.market_cap if fund else None,
        })

    return items


def get_volume_spikes(
    db: Session,
    market: str | None = None,
    min_ratio: float = 2.0,
    limit: int = 30,
) -> list[dict]:
    """Detect stocks with unusual volume (today vs 20-day average).

    Also stores detected spikes in the volume_spikes table.
    """
    latest_date = db.query(func.max(DailyPrice.date)).scalar()
    if not latest_date:
        return []

    # Get all stocks with today's data
    query = (
        db.query(DailyPrice, Stock)
        .join(Stock, Stock.ticker == DailyPrice.ticker)
        .filter(
            DailyPrice.date == latest_date,
            DailyPrice.volume > 0,
            Stock.is_active.is_(True),
        )
    )
    if market:
        query = query.filter(Stock.market == market.upper())

    today_data = query.all()
    results = []

    for price, stock in today_data:
        # Calculate 20-day average volume (excluding today)
        avg_vol = (
            db.query(func.avg(DailyPrice.volume))
            .filter(
                DailyPrice.ticker == stock.ticker,
                DailyPrice.date < latest_date,
                DailyPrice.date >= latest_date - timedelta(days=30),
                DailyPrice.volume > 0,
            )
            .scalar()
        )

        if not avg_vol or avg_vol == 0:
            continue

        ratio = price.volume / avg_vol
        if ratio >= min_ratio:
            results.append({
                "price": price,
                "stock": stock,
                "ratio": ratio,
                "avg_vol": avg_vol,
            })

    # Sort by ratio descending
    results.sort(key=lambda x: x["ratio"], reverse=True)
    results = results[:limit]

    # Store spikes and build response
    items = []
    for r in results:
        price = r["price"]
        stock = r["stock"]

        # Upsert volume spike record
        existing_spike = (
            db.query(VolumeSpike)
            .filter(VolumeSpike.ticker == stock.ticker, VolumeSpike.date == latest_date)
            .first()
        )
        spike_data = {
            "volume": price.volume,
            "avg_volume_20d": int(r["avg_vol"]),
            "spike_ratio": round(r["ratio"], 2),
            "price_change_pct": price.change_pct,
        }
        if existing_spike:
            for k, v in spike_data.items():
                setattr(existing_spike, k, v)
        else:
            db.add(VolumeSpike(ticker=stock.ticker, date=latest_date, **spike_data))

        items.append(_build_screener_item(db, price, stock, volume_ratio=round(r["ratio"], 2)))

    db.commit()
    return items


def get_new_highs(
    db: Session,
    market: str | None = None,
    period_weeks: int = 52,
    limit: int = 30,
) -> list[dict]:
    """Find stocks at or near their period high."""
    latest_date = db.query(func.max(DailyPrice.date)).scalar()
    if not latest_date:
        return []

    start_date = latest_date - timedelta(weeks=period_weeks)

    # Subquery: max high per ticker in period
    max_high_sub = (
        db.query(
            DailyPrice.ticker,
            func.max(DailyPrice.high).label("period_high"),
        )
        .filter(DailyPrice.date >= start_date)
        .group_by(DailyPrice.ticker)
        .subquery()
    )

    # Today's prices that match or are near the period high (within 3%)
    query = (
        db.query(DailyPrice, Stock, max_high_sub.c.period_high)
        .join(Stock, Stock.ticker == DailyPrice.ticker)
        .join(max_high_sub, DailyPrice.ticker == max_high_sub.c.ticker)
        .filter(
            DailyPrice.date == latest_date,
            DailyPrice.high >= max_high_sub.c.period_high * 0.97,
            Stock.is_active.is_(True),
            DailyPrice.close > 0,
        )
    )

    if market:
        query = query.filter(Stock.market == market.upper())

    results = query.order_by(desc(DailyPrice.change_pct)).limit(limit).all()

    return [_build_screener_item(db, price, stock) for price, stock, _ in results]


def _build_screener_item(
    db: Session,
    price: DailyPrice,
    stock: Stock,
    volume_ratio: float | None = None,
    momentum_score: float | None = None,
) -> dict:
    """Build a standard screener item dict."""
    fund = (
        db.query(MarketFundamentals)
        .filter(MarketFundamentals.ticker == stock.ticker)
        .order_by(desc(MarketFundamentals.date))
        .first()
    )

    return {
        "ticker": stock.ticker,
        "name": stock.name,
        "market": stock.market,
        "close": price.close,
        "change_pct": round(price.change_pct, 2) if price.change_pct else 0,
        "volume": price.volume,
        "volume_ratio": volume_ratio,
        "momentum_score": momentum_score,
        "market_cap": fund.market_cap if fund else None,
    }
