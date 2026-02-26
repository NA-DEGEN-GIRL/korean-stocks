"""Market data service using FinanceDataReader for KRX stock data collection."""

import logging
import re
import time
from datetime import date, datetime, timedelta

import FinanceDataReader as fdr
import requests
from sqlalchemy.orm import Session

from app.models.stock import DailyPrice, MarketFundamentals, Stock

logger = logging.getLogger(__name__)

REQUEST_DELAY = 0.5


def _sleep():
    time.sleep(REQUEST_DELAY)


def sync_stock_list(db: Session, market: str = "ALL") -> int:
    """Sync the full stock list from KRX into the database.

    Uses FinanceDataReader.StockListing which returns current day's data
    including price, market cap, etc.

    Returns:
        Number of stocks synced
    """
    markets_to_sync = []
    if market in ("ALL", "KOSPI"):
        markets_to_sync.append("KOSPI")
    if market in ("ALL", "KOSDAQ"):
        markets_to_sync.append("KOSDAQ")

    count = 0
    for mkt in markets_to_sync:
        try:
            df = fdr.StockListing(mkt)
            _sleep()
        except Exception as e:
            logger.error(f"Failed to get stock listing for {mkt}: {e}")
            continue

        if df.empty:
            logger.warning(f"No stocks found for {mkt}")
            continue

        today = date.today()

        for _, row in df.iterrows():
            ticker = str(row.get("Code", "")).strip()
            name = str(row.get("Name", "")).strip()
            if not ticker or not name:
                continue

            # Upsert stock
            existing = db.query(Stock).filter(Stock.ticker == ticker).first()
            if existing:
                existing.name = name
                existing.market = mkt
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
            else:
                db.add(Stock(ticker=ticker, name=name, market=mkt, is_active=True))

            # Also store today's price data from the listing
            close_price = int(row.get("Close", 0)) if row.get("Close") else None
            if close_price and close_price > 0:
                existing_price = (
                    db.query(DailyPrice)
                    .filter(DailyPrice.ticker == ticker, DailyPrice.date == today)
                    .first()
                )
                price_data = {
                    "open": int(row.get("Open", 0)) or None,
                    "high": int(row.get("High", 0)) or None,
                    "low": int(row.get("Low", 0)) or None,
                    "close": close_price,
                    "volume": int(row.get("Volume", 0)) or None,
                    "trading_value": int(row.get("Amount", 0)) or None,
                    "change_pct": float(row.get("ChagesRatio", 0)) if row.get("ChagesRatio") else None,
                }
                if existing_price:
                    for k, v in price_data.items():
                        setattr(existing_price, k, v)
                else:
                    db.add(DailyPrice(ticker=ticker, date=today, **price_data))

            # Store market cap (PER/PBR/EPS are fetched separately from Naver)
            marcap = int(row.get("Marcap", 0)) if row.get("Marcap") else None
            if marcap and marcap > 0:
                existing_fund = (
                    db.query(MarketFundamentals)
                    .filter(MarketFundamentals.ticker == ticker, MarketFundamentals.date == today)
                    .first()
                )
                if existing_fund:
                    existing_fund.market_cap = marcap
                else:
                    db.add(MarketFundamentals(ticker=ticker, date=today, market_cap=marcap))

            count += 1

        logger.info(f"Synced {len(df)} stocks for {mkt}")

    db.commit()
    logger.info(f"Total stocks synced: {count}")
    return count


def fetch_daily_prices(db: Session, target_date: date, market: str = "ALL") -> int:
    """Fetch OHLCV data for all stocks in a market for a date range ending at target_date.

    Uses FinanceDataReader.StockListing for current data, and per-stock DataReader
    for historical data.

    Returns:
        Number of price records upserted
    """
    # For today's data, StockListing is more efficient (one call)
    if target_date >= date.today():
        return _fetch_prices_from_listing(db, market)

    # For historical data, we need to query per-stock
    return _fetch_historical_prices(db, target_date, market)


def _fetch_prices_from_listing(db: Session, market: str) -> int:
    """Fetch today's prices using StockListing (single API call per market)."""
    markets = []
    if market in ("ALL", "KOSPI"):
        markets.append("KOSPI")
    if market in ("ALL", "KOSDAQ"):
        markets.append("KOSDAQ")

    count = 0
    today = date.today()

    for mkt in markets:
        try:
            df = fdr.StockListing(mkt)
            _sleep()
        except Exception as e:
            logger.error(f"Failed to get listing for {mkt}: {e}")
            continue

        for _, row in df.iterrows():
            ticker = str(row.get("Code", "")).strip()
            if not ticker:
                continue

            close_price = int(row.get("Close", 0)) if row.get("Close") else None
            if not close_price or close_price <= 0:
                continue

            existing = (
                db.query(DailyPrice)
                .filter(DailyPrice.ticker == ticker, DailyPrice.date == today)
                .first()
            )

            price_data = {
                "open": int(row.get("Open", 0)) or None,
                "high": int(row.get("High", 0)) or None,
                "low": int(row.get("Low", 0)) or None,
                "close": close_price,
                "volume": int(row.get("Volume", 0)) or None,
                "trading_value": int(row.get("Amount", 0)) or None,
                "change_pct": float(row.get("ChagesRatio", 0)) if row.get("ChagesRatio") else None,
            }

            if existing:
                for k, v in price_data.items():
                    setattr(existing, k, v)
            else:
                db.add(DailyPrice(ticker=ticker, date=today, **price_data))
            count += 1

        logger.info(f"Fetched {count} prices for {mkt}")

    db.commit()
    return count


def _fetch_historical_prices(db: Session, target_date: date, market: str) -> int:
    """Fetch historical prices for a specific date using per-stock queries.

    This is slower but works for any historical date.
    """
    # Get all active stocks for the given market
    query = db.query(Stock).filter(Stock.is_active.is_(True))
    if market != "ALL":
        query = query.filter(Stock.market == market)
    stocks = query.all()

    if not stocks:
        logger.warning("No stocks found in database. Run sync-stocks first.")
        return 0

    count = 0
    start_str = target_date.strftime("%Y-%m-%d")
    end_str = target_date.strftime("%Y-%m-%d")

    for i, stock in enumerate(stocks):
        try:
            df = fdr.DataReader(stock.ticker, start_str, end_str)
        except Exception as e:
            logger.debug(f"Failed to get price for {stock.ticker}: {e}")
            continue

        if df.empty:
            continue

        row = df.iloc[0]
        actual_date = df.index[0].date() if hasattr(df.index[0], 'date') else target_date

        existing = (
            db.query(DailyPrice)
            .filter(DailyPrice.ticker == stock.ticker, DailyPrice.date == actual_date)
            .first()
        )

        price_data = {
            "open": int(row.get("Open", 0)),
            "high": int(row.get("High", 0)),
            "low": int(row.get("Low", 0)),
            "close": int(row.get("Close", 0)),
            "volume": int(row.get("Volume", 0)),
            "change_pct": float(row.get("Change", 0)) * 100 if row.get("Change") else None,
        }

        if existing:
            for k, v in price_data.items():
                setattr(existing, k, v)
        else:
            db.add(DailyPrice(ticker=stock.ticker, date=actual_date, **price_data))
        count += 1

        # Rate limit and progress logging
        if (i + 1) % 100 == 0:
            db.commit()
            logger.info(f"Progress: {i + 1}/{len(stocks)} stocks processed for {target_date}")
            _sleep()

    db.commit()
    logger.info(f"Fetched {count} historical prices for {target_date}")
    return count


def fetch_prices_bulk(db: Session, ticker: str, start_date: date, end_date: date) -> int:
    """Fetch price history for a single stock over a date range.

    More efficient than calling fetch_daily_prices for each date.

    Returns:
        Number of records upserted
    """
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    try:
        df = fdr.DataReader(ticker, start_str, end_str)
    except Exception as e:
        logger.error(f"Failed to get bulk prices for {ticker}: {e}")
        return 0

    if df.empty:
        return 0

    count = 0
    for idx, row in df.iterrows():
        row_date = idx.date() if hasattr(idx, 'date') else idx

        existing = (
            db.query(DailyPrice)
            .filter(DailyPrice.ticker == ticker, DailyPrice.date == row_date)
            .first()
        )

        price_data = {
            "open": int(row.get("Open", 0)),
            "high": int(row.get("High", 0)),
            "low": int(row.get("Low", 0)),
            "close": int(row.get("Close", 0)),
            "volume": int(row.get("Volume", 0)),
            "change_pct": float(row.get("Change", 0)) * 100 if row.get("Change") else None,
        }

        if existing:
            for k, v in price_data.items():
                setattr(existing, k, v)
        else:
            db.add(DailyPrice(ticker=ticker, date=row_date, **price_data))
        count += 1

    db.commit()
    return count


def backfill_prices(db: Session, start_date: date, end_date: date, market: str = "ALL") -> dict:
    """Backfill daily prices for all stocks over a date range.

    Uses per-stock bulk fetch (one API call per stock for the whole range)
    instead of per-date fetch, which is much more efficient.

    Returns:
        Dict with summary of backfill results
    """
    query = db.query(Stock).filter(Stock.is_active.is_(True))
    if market != "ALL":
        query = query.filter(Stock.market == market)
    stocks = query.all()

    if not stocks:
        return {"error": "No stocks in database. Run sync-stocks first."}

    results = {"stocks_processed": 0, "records_inserted": 0, "errors": []}

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    for i, stock in enumerate(stocks):
        try:
            df = fdr.DataReader(stock.ticker, start_str, end_str)
        except Exception as e:
            results["errors"].append(f"{stock.ticker}: {str(e)}")
            continue

        if df.empty:
            continue

        for idx, row in df.iterrows():
            row_date = idx.date() if hasattr(idx, 'date') else idx

            existing = (
                db.query(DailyPrice)
                .filter(DailyPrice.ticker == stock.ticker, DailyPrice.date == row_date)
                .first()
            )

            price_data = {
                "open": int(row.get("Open", 0)),
                "high": int(row.get("High", 0)),
                "low": int(row.get("Low", 0)),
                "close": int(row.get("Close", 0)),
                "volume": int(row.get("Volume", 0)),
                "change_pct": float(row.get("Change", 0)) * 100 if row.get("Change") else None,
            }

            if existing:
                for k, v in price_data.items():
                    setattr(existing, k, v)
            else:
                db.add(DailyPrice(ticker=stock.ticker, date=row_date, **price_data))
            results["records_inserted"] += 1

        results["stocks_processed"] += 1

        # Commit and rate limit periodically
        if (i + 1) % 50 == 0:
            db.commit()
            logger.info(
                f"Backfill progress: {i + 1}/{len(stocks)} stocks, "
                f"{results['records_inserted']} records"
            )
            _sleep()

    db.commit()
    logger.info(
        f"Backfill complete: {results['stocks_processed']} stocks, "
        f"{results['records_inserted']} records"
    )
    return results


def fetch_fundamentals_naver(db: Session, ticker: str) -> dict | None:
    """Fetch PER/PBR/EPS/BPS/배당금 from Naver Finance API and save to DB.

    Returns:
        Dict with fundamental data, or None on failure.
    """
    url = f"https://m.stock.naver.com/api/stock/{ticker}/finance/annual"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://m.stock.naver.com/",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.debug(f"Failed to fetch Naver fundamentals for {ticker}: {e}")
        return None

    rows = data.get("financeInfo", {}).get("rowList", [])
    if not rows:
        return None

    def _parse_number(value_str: str) -> float | None:
        """Parse a Korean-formatted number string like '33.21' or '6,564'."""
        if not value_str or value_str == "-":
            return None
        cleaned = re.sub(r"[^\d.\-]", "", value_str)
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    # Find the latest non-consensus column key
    tr_titles = data.get("financeInfo", {}).get("trTitleList", [])
    latest_key = None
    for tr in reversed(tr_titles):
        if tr.get("isConsensus") == "N":
            latest_key = tr.get("key")
            break

    if not latest_key:
        return None

    # Extract values by row title
    values = {}
    for row in rows:
        title = row.get("title", "")
        col_data = row.get("columns", {}).get(latest_key, {})
        val = _parse_number(col_data.get("value", ""))
        if val is not None:
            values[title] = val

    per = values.get("PER")
    pbr = values.get("PBR")
    eps = int(values["EPS"]) if "EPS" in values else None
    bps = int(values["BPS"]) if "BPS" in values else None
    dps = int(values["주당배당금"]) if "주당배당금" in values else None

    if not any([per, pbr, eps]):
        return None

    # Calculate div_yield from dps and latest close price
    div_yield = None
    if dps and dps > 0:
        latest_price = (
            db.query(DailyPrice)
            .filter(DailyPrice.ticker == ticker)
            .order_by(DailyPrice.date.desc())
            .first()
        )
        if latest_price and latest_price.close and latest_price.close > 0:
            div_yield = round(dps / latest_price.close * 100, 2)

    today = date.today()
    fund_data = {
        "per": per,
        "pbr": pbr,
        "eps": eps,
        "bps": bps,
        "dps": dps,
        "div_yield": div_yield,
    }

    existing = (
        db.query(MarketFundamentals)
        .filter(MarketFundamentals.ticker == ticker, MarketFundamentals.date == today)
        .first()
    )
    if existing:
        for k, v in fund_data.items():
            if v is not None:
                setattr(existing, k, v)
    else:
        # Check if there's any recent record we can update instead
        recent = (
            db.query(MarketFundamentals)
            .filter(MarketFundamentals.ticker == ticker)
            .order_by(MarketFundamentals.date.desc())
            .first()
        )
        if recent:
            for k, v in fund_data.items():
                if v is not None:
                    setattr(recent, k, v)
        else:
            db.add(MarketFundamentals(ticker=ticker, date=today, **fund_data))

    db.commit()
    logger.info(f"Fetched Naver fundamentals for {ticker}: PER={per}, PBR={pbr}, EPS={eps}")
    return fund_data
