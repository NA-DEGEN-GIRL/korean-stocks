from datetime import date, datetime
from pydantic import BaseModel


class WhyMovingResponse(BaseModel):
    ticker: str
    name: str
    date: date
    price_change_pct: float | None = None
    volume_spike_ratio: float | None = None
    disclosures: list[dict] = []
    news: list[dict] = []
    sector_comparison: dict = {}
    summary: str = ""


class WeeklyReportResponse(BaseModel):
    week_start: date
    week_end: date
    top_gainers: list[dict] = []
    top_losers: list[dict] = []
    volume_spikes: list[dict] = []
    new_highs: list[dict] = []
    created_at: datetime | None = None
