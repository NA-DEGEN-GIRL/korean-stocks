from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    id: int
    ticker: str | None = None
    title: str | None = None
    summary: str | None = None
    source: str | None = None
    url: str
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class NewsListResponse(BaseModel):
    items: list[NewsItem]
    total: int
