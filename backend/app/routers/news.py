"""News endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.schemas.news import NewsItem, NewsListResponse
from app.services.news_service import fetch_news_for_ticker, get_news

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=NewsListResponse)
def list_news(
    ticker: str | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> NewsListResponse:
    """List news articles from DB."""
    items = get_news(db, ticker=ticker, limit=limit)
    return NewsListResponse(
        items=[NewsItem.model_validate(n) for n in items],
        total=len(items),
    )


@router.post("/fetch/{ticker}")
def fetch_ticker_news(
    ticker: str,
    background_tasks: BackgroundTasks,
    pages: int = Query(3, ge=1, le=10),
) -> dict:
    """Trigger scraping news for a specific ticker from Naver Finance."""

    def _run():
        db = SessionLocal()
        try:
            fetch_news_for_ticker(db, ticker, pages=pages)
        finally:
            db.close()

    background_tasks.add_task(_run)
    return {"status": "fetching", "ticker": ticker}
