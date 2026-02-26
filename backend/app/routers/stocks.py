from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stock import DailyPrice, MarketFundamentals, Stock
from app.schemas.stock import (
    DailyPriceResponse,
    StockDetailResponse,
    StockListResponse,
    StockResponse,
    FundamentalsInfo,
)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("", response_model=StockListResponse)
def list_stocks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    market: str | None = Query(None, description="Filter by market: KOSPI or KOSDAQ"),
    search: str | None = Query(None, description="Search by ticker or name"),
    db: Session = Depends(get_db),
) -> StockListResponse:
    """Return a paginated list of stocks with their latest price data."""
    query = db.query(Stock).filter(Stock.is_active.is_(True))

    if market:
        query = query.filter(Stock.market == market.upper())
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Stock.ticker.ilike(pattern)) | (Stock.name.ilike(pattern))
        )

    total = query.count()
    stocks = query.order_by(Stock.ticker).offset((page - 1) * per_page).limit(per_page).all()

    items: list[StockResponse] = []
    for stock in stocks:
        latest_price_row = (
            db.query(DailyPrice)
            .filter(DailyPrice.ticker == stock.ticker)
            .order_by(desc(DailyPrice.date))
            .first()
        )
        items.append(
            StockResponse(
                ticker=stock.ticker,
                name=stock.name,
                market=stock.market,
                sector=stock.sector,
                is_active=stock.is_active,
                latest_price=latest_price_row.close if latest_price_row else None,
                change_pct=latest_price_row.change_pct if latest_price_row else None,
            )
        )

    return StockListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{ticker}", response_model=StockDetailResponse)
def get_stock_detail(
    ticker: str,
    db: Session = Depends(get_db),
) -> StockDetailResponse:
    """Return detailed information for a single stock including fundamentals."""
    stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    latest_price_row = (
        db.query(DailyPrice)
        .filter(DailyPrice.ticker == stock.ticker)
        .order_by(desc(DailyPrice.date))
        .first()
    )

    latest_fundamentals = (
        db.query(MarketFundamentals)
        .filter(MarketFundamentals.ticker == stock.ticker)
        .order_by(desc(MarketFundamentals.date))
        .first()
    )

    fundamentals_info: FundamentalsInfo | None = None
    if latest_fundamentals:
        fundamentals_info = FundamentalsInfo(
            market_cap=latest_fundamentals.market_cap,
            per=latest_fundamentals.per,
            pbr=latest_fundamentals.pbr,
            eps=latest_fundamentals.eps,
            div_yield=latest_fundamentals.div_yield,
        )

    return StockDetailResponse(
        ticker=stock.ticker,
        name=stock.name,
        market=stock.market,
        sector=stock.sector,
        is_active=stock.is_active,
        latest_price=latest_price_row.close if latest_price_row else None,
        change_pct=latest_price_row.change_pct if latest_price_row else None,
        fundamentals=fundamentals_info,
    )


@router.get("/{ticker}/prices", response_model=list[DailyPriceResponse])
def get_stock_prices(
    ticker: str,
    days: int = Query(90, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db),
) -> list[DailyPriceResponse]:
    """Return daily price history for a stock.

    If the database has insufficient data, automatically fetches from
    FinanceDataReader and caches the results.
    """
    stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    cutoff_date = date.today() - timedelta(days=days)
    prices = (
        db.query(DailyPrice)
        .filter(DailyPrice.ticker == stock.ticker, DailyPrice.date >= cutoff_date)
        .order_by(DailyPrice.date)
        .all()
    )

    # Auto-fetch if we have less than 5 days of data
    if len(prices) < 5:
        from app.services.market_data import fetch_prices_bulk
        count = fetch_prices_bulk(db, stock.ticker, cutoff_date, date.today())
        if count > 0:
            prices = (
                db.query(DailyPrice)
                .filter(DailyPrice.ticker == stock.ticker, DailyPrice.date >= cutoff_date)
                .order_by(DailyPrice.date)
                .all()
            )

    return [
        DailyPriceResponse(
            date=p.date,
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close,
            volume=p.volume,
            trading_value=p.trading_value,
            change_pct=p.change_pct,
        )
        for p in prices
    ]
