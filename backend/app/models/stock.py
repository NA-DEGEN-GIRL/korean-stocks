from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)  # KOSPI or KOSDAQ
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    daily_prices: Mapped[list["DailyPrice"]] = relationship(
        "DailyPrice", back_populates="stock", cascade="all, delete-orphan"
    )
    fundamentals: Mapped[list["MarketFundamentals"]] = relationship(
        "MarketFundamentals", back_populates="stock", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Stock ticker={self.ticker} name={self.name}>"


class DailyPrice(Base):
    __tablename__ = "daily_prices"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_daily_price_ticker_date"),
        Index("ix_daily_prices_date", "date"),
        Index("ix_daily_prices_ticker_date", "ticker", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    open: Mapped[int | None] = mapped_column(Integer, nullable=True)
    high: Mapped[int | None] = mapped_column(Integer, nullable=True)
    low: Mapped[int | None] = mapped_column(Integer, nullable=True)
    close: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    trading_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    stock: Mapped["Stock"] = relationship("Stock", back_populates="daily_prices")

    def __repr__(self) -> str:
        return f"<DailyPrice ticker={self.ticker} date={self.date} close={self.close}>"


class MarketFundamentals(Base):
    __tablename__ = "market_fundamentals"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_fundamentals_ticker_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    per: Mapped[float | None] = mapped_column(Float, nullable=True)
    pbr: Mapped[float | None] = mapped_column(Float, nullable=True)
    div_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    stock: Mapped["Stock"] = relationship("Stock", back_populates="fundamentals")

    def __repr__(self) -> str:
        return f"<MarketFundamentals ticker={self.ticker} date={self.date}>"
