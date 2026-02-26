"""Analysis service: why is a stock moving, weekly report generation."""

import logging
from datetime import date, timedelta

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.models.stock import DailyPrice, MarketFundamentals, Stock
from app.models.disclosure import DartDisclosure
from app.models.news import NewsArticle
from app.models.analysis import VolumeSpike
from app.services.dart_service import fetch_disclosures_for_ticker, get_disclosures
from app.services.news_service import fetch_news_for_ticker, get_news

logger = logging.getLogger(__name__)


def analyze_why_moving(
    db: Session,
    ticker: str,
    target_date: date | None = None,
) -> dict:
    """Analyze why a stock is moving by combining price, disclosure, news, and sector data."""
    if target_date is None:
        target_date = date.today()

    stock = db.execute(select(Stock).where(Stock.ticker == ticker)).scalar_one_or_none()
    if not stock:
        return {"error": "Stock not found"}

    # 1. Price & volume analysis
    price_info = _get_price_analysis(db, ticker, target_date)

    # 2. Recent disclosures (3 days window)
    disc_start = target_date - timedelta(days=3)
    disclosures = get_disclosures(db, ticker=ticker, start_date=disc_start, end_date=target_date, limit=20)
    if not disclosures:
        fetch_disclosures_for_ticker(db, ticker, start_date=disc_start, end_date=target_date)
        disclosures = get_disclosures(db, ticker=ticker, start_date=disc_start, end_date=target_date, limit=20)

    # 3. Recent news
    news = get_news(db, ticker=ticker, limit=20)
    if not news:
        fetch_news_for_ticker(db, ticker, pages=2)
        news = get_news(db, ticker=ticker, limit=20)

    # 4. Sector comparison
    sector_info = _get_sector_comparison(db, ticker, stock.sector, target_date)

    # 5. Build summary
    summary = _build_summary(stock.name, price_info, disclosures, news, sector_info)

    return {
        "ticker": ticker,
        "name": stock.name,
        "date": target_date.isoformat(),
        "price_change_pct": price_info.get("change_pct"),
        "volume_spike_ratio": price_info.get("volume_ratio"),
        "disclosures": [
            {
                "report_nm": d.report_nm,
                "rcept_dt": d.rcept_dt.isoformat() if d.rcept_dt else None,
                "disclosure_url": d.disclosure_url,
                "flr_nm": d.flr_nm,
            }
            for d in disclosures[:10]
        ],
        "news": [
            {
                "title": n.title,
                "source": n.source,
                "url": n.url,
                "published_at": n.published_at.isoformat() if n.published_at else None,
            }
            for n in news[:10]
        ],
        "sector_comparison": sector_info,
        "summary": summary,
    }


def _get_price_analysis(db: Session, ticker: str, target_date: date) -> dict:
    """Analyze recent price and volume activity."""
    latest = db.execute(
        select(DailyPrice)
        .where(DailyPrice.ticker == ticker)
        .order_by(DailyPrice.date.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest:
        return {}

    # Get 20-day average volume
    prices_20d = db.execute(
        select(DailyPrice)
        .where(DailyPrice.ticker == ticker)
        .order_by(DailyPrice.date.desc())
        .limit(20)
    ).scalars().all()

    volume_ratio = None
    if len(prices_20d) >= 2:
        avg_vol = sum(p.volume for p in prices_20d[1:]) / max(len(prices_20d) - 1, 1)
        if avg_vol > 0:
            volume_ratio = round(latest.volume / avg_vol, 2)

    return {
        "close": latest.close,
        "change_pct": latest.change_pct,
        "volume": latest.volume,
        "volume_ratio": volume_ratio,
        "date": latest.date.isoformat(),
    }


def _get_sector_comparison(
    db: Session,
    ticker: str,
    sector: str | None,
    target_date: date,
) -> dict:
    """Compare stock performance against its sector peers."""
    if not sector:
        return {"sector": None, "sector_avg_change": None, "is_sector_wide": None}

    sector_stocks = db.execute(
        select(Stock.ticker).where(
            and_(Stock.sector == sector, Stock.is_active == True)
        )
    ).scalars().all()

    if not sector_stocks:
        return {"sector": sector, "sector_avg_change": None, "is_sector_wide": None}

    # Get latest price changes for sector peers
    changes = []
    for t in sector_stocks[:50]:
        price = db.execute(
            select(DailyPrice)
            .where(DailyPrice.ticker == t)
            .order_by(DailyPrice.date.desc())
            .limit(1)
        ).scalar_one_or_none()
        if price and price.change_pct is not None:
            changes.append(price.change_pct)

    if not changes:
        return {"sector": sector, "sector_avg_change": None, "is_sector_wide": None}

    sector_avg = sum(changes) / len(changes)
    positive_ratio = sum(1 for c in changes if c > 1) / len(changes)

    return {
        "sector": sector,
        "sector_avg_change": round(sector_avg, 2),
        "sector_stock_count": len(changes),
        "sector_positive_ratio": round(positive_ratio * 100, 1),
        "is_sector_wide": positive_ratio > 0.6 and sector_avg > 1,
    }


def _build_summary(
    name: str,
    price_info: dict,
    disclosures: list,
    news: list,
    sector_info: dict,
) -> str:
    """Generate a human-readable summary of why the stock is moving."""
    parts = []

    change = price_info.get("change_pct")
    if change is not None:
        direction = "상승" if change > 0 else "하락"
        parts.append(f"{name}이(가) {abs(change):.2f}% {direction}했습니다.")

    vol_ratio = price_info.get("volume_ratio")
    if vol_ratio and vol_ratio > 1.5:
        parts.append(f"거래량이 평소 대비 {vol_ratio:.1f}배로 급증했습니다.")

    if disclosures:
        key_types = [d.report_nm for d in disclosures[:3] if d.report_nm]
        if key_types:
            parts.append(f"최근 공시: {', '.join(key_types[:3])}")

    if news:
        titles = [n.title for n in news[:3] if n.title]
        if titles:
            parts.append(f"관련 뉴스: {titles[0]}")

    if sector_info.get("is_sector_wide"):
        parts.append(
            f"동일 섹터({sector_info['sector']}) 전체가 평균 {sector_info['sector_avg_change']:.1f}% 상승 중입니다."
        )
    elif sector_info.get("sector") and sector_info.get("sector_avg_change") is not None:
        parts.append(
            f"동일 섹터({sector_info['sector']}) 평균 {sector_info['sector_avg_change']:.1f}% 대비 개별 종목 움직임입니다."
        )

    return " ".join(parts) if parts else f"{name}의 변동 원인을 파악할 수 없습니다."
