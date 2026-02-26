from pydantic import BaseModel


class ScreenerItem(BaseModel):
    ticker: str
    name: str
    market: str
    close: int | None = None
    change_pct: float | None = None
    volume: int | None = None
    volume_ratio: float | None = None
    momentum_score: float | None = None
    market_cap: int | None = None


class ScreenerResponse(BaseModel):
    items: list[ScreenerItem]
    total: int
