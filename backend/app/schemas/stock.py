from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class StockBase(BaseModel):
    ticker: str
    name: str
    market: str
    sector: str | None = None


class StockResponse(StockBase):
    is_active: bool
    latest_price: int | None = None
    change_pct: float | None = None
    trading_value: int | None = None

    model_config = ConfigDict(from_attributes=True)


class StockListResponse(BaseModel):
    items: list[StockResponse]
    total: int
    page: int
    per_page: int


class DailyPriceResponse(BaseModel):
    date: date
    open: int | None = None
    high: int | None = None
    low: int | None = None
    close: int | None = None
    volume: int | None = None
    trading_value: int | None = None
    change_pct: float | None = None

    model_config = ConfigDict(from_attributes=True)


class FundamentalsInfo(BaseModel):
    market_cap: int | None = None
    per: float | None = None
    pbr: float | None = None
    eps: int | None = None
    div_yield: float | None = None

    model_config = ConfigDict(from_attributes=True)


class StockDetailResponse(BaseModel):
    ticker: str
    name: str
    market: str
    sector: str | None = None
    is_active: bool
    latest_price: int | None = None
    change_pct: float | None = None
    fundamentals: FundamentalsInfo | None = None

    model_config = ConfigDict(from_attributes=True)
