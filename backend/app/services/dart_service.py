"""DART (Data Analysis, Retrieval and Transfer) disclosure service using OpenDartReader."""

import logging
from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.disclosure import DartDisclosure

logger = logging.getLogger(__name__)

DART_BASE_URL = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="


def _get_dart():
    """Lazy-initialize OpenDartReader."""
    import OpenDartReader

    if not settings.DART_API_KEY:
        raise RuntimeError("DART_API_KEY is not set")
    return OpenDartReader(settings.DART_API_KEY)


def fetch_disclosures_for_ticker(
    db: Session,
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[DartDisclosure]:
    """Fetch and store DART disclosures for a specific ticker."""
    dart = _get_dart()

    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=90)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    try:
        result = dart.list(corp=ticker, start=start_str, end=end_str)
    except Exception as e:
        logger.error("Failed to fetch DART disclosures for %s: %s", ticker, e)
        return []

    if not isinstance(result, pd.DataFrame) or result.empty:
        return []

    new_items = []
    for _, row in result.iterrows():
        rcept_no = str(row.get("rcept_no", ""))
        if not rcept_no:
            continue

        existing = db.execute(
            select(DartDisclosure).where(DartDisclosure.rcept_no == rcept_no)
        ).scalar_one_or_none()
        if existing:
            continue

        disclosure = DartDisclosure(
            corp_code=str(row.get("corp_code", "")),
            corp_name=str(row.get("corp_name", "")),
            ticker=ticker,
            report_nm=str(row.get("report_nm", "")),
            rcept_no=rcept_no,
            flr_nm=str(row.get("flr_nm", "")),
            rcept_dt=datetime.strptime(str(row["rcept_dt"]), "%Y%m%d").date()
            if row.get("rcept_dt")
            else None,
            report_type=str(row.get("corp_cls", "")),
            disclosure_url=DART_BASE_URL + rcept_no,
        )
        db.add(disclosure)
        new_items.append(disclosure)

    if new_items:
        db.commit()
        logger.info("Saved %d new disclosures for %s", len(new_items), ticker)

    return new_items


def fetch_disclosures_by_date(
    db: Session,
    target_date: date | None = None,
    kind: str = "",
) -> int:
    """Fetch all disclosures for a given date. kind: A=정기보고, B=주요사항, C=발행공시, D=지분공시, E=기타공시, empty=전체."""
    dart = _get_dart()

    if target_date is None:
        target_date = date.today()

    date_str = target_date.strftime("%Y-%m-%d")

    try:
        result = dart.list_date(date_str, date_str)
    except Exception as e:
        logger.error("Failed to fetch DART disclosures for date %s: %s", date_str, e)
        return 0

    if not isinstance(result, pd.DataFrame) or result.empty:
        return 0

    count = 0
    for _, row in result.iterrows():
        rcept_no = str(row.get("rcept_no", ""))
        stock_code = str(row.get("stock_code", "")).strip()
        if not rcept_no or not stock_code:
            continue

        existing = db.execute(
            select(DartDisclosure).where(DartDisclosure.rcept_no == rcept_no)
        ).scalar_one_or_none()
        if existing:
            continue

        disclosure = DartDisclosure(
            corp_code=str(row.get("corp_code", "")),
            corp_name=str(row.get("corp_name", "")),
            ticker=stock_code,
            report_nm=str(row.get("report_nm", "")),
            rcept_no=rcept_no,
            flr_nm=str(row.get("flr_nm", "")),
            rcept_dt=datetime.strptime(str(row["rcept_dt"]), "%Y%m%d").date()
            if row.get("rcept_dt")
            else None,
            report_type=str(row.get("corp_cls", "")),
            disclosure_url=DART_BASE_URL + rcept_no,
        )
        db.add(disclosure)
        count += 1

    if count:
        db.commit()
        logger.info("Saved %d new disclosures for date %s", count, date_str)

    return count


def get_disclosures(
    db: Session,
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 50,
) -> list[DartDisclosure]:
    """Read disclosures from DB, optionally filtered by ticker and date range."""
    stmt = select(DartDisclosure).order_by(DartDisclosure.rcept_dt.desc())

    if ticker:
        stmt = stmt.where(DartDisclosure.ticker == ticker)
    if start_date:
        stmt = stmt.where(DartDisclosure.rcept_dt >= start_date)
    if end_date:
        stmt = stmt.where(DartDisclosure.rcept_dt <= end_date)

    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())
