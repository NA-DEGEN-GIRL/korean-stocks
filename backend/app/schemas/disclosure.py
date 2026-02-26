from datetime import date, datetime

from pydantic import BaseModel


class DisclosureItem(BaseModel):
    id: int
    ticker: str | None = None
    corp_name: str | None = None
    report_nm: str | None = None
    rcept_no: str
    flr_nm: str | None = None
    rcept_dt: date | None = None
    report_type: str | None = None
    disclosure_url: str | None = None

    model_config = {"from_attributes": True}


class DisclosureListResponse(BaseModel):
    items: list[DisclosureItem]
    total: int
