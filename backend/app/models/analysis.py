from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VolumeSpike(Base):
    __tablename__ = "volume_spikes"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_volume_spike_ticker_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    avg_volume_20d: Mapped[int] = mapped_column(BigInteger, nullable=False)
    spike_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    price_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<VolumeSpike ticker={self.ticker} date={self.date} ratio={self.spike_ratio}>"


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (
        UniqueConstraint("week_start", name="uq_weekly_report_week_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    week_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    report_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<WeeklyReport {self.week_start} ~ {self.week_end}>"


class MoverReason(Base):
    __tablename__ = "mover_reasons"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_mover_reason_ticker_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    price_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_spike_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    related_disclosures: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    related_news: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    sector_comparison: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<MoverReason ticker={self.ticker} date={self.date}>"
