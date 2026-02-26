from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DartDisclosure(Base):
    __tablename__ = "dart_disclosures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    corp_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    corp_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ticker: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("stocks.ticker"), nullable=True
    )
    report_nm: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rcept_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    flr_nm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rcept_dt: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    report_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    disclosure_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_impact: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<DartDisclosure rcept_no={self.rcept_no} corp_name={self.corp_name}>"
