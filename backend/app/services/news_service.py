"""News scraping service for Naver Finance."""

import logging
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.news import NewsArticle

logger = logging.getLogger(__name__)

NAVER_NEWS_URL = "https://finance.naver.com/item/news_news.naver"
NAVER_NEWS_READ_URL = "https://finance.naver.com"
NAVER_ARTICLE_URL = "https://n.news.naver.com/mnews/article/{office_id}/{article_id}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def fetch_news_for_ticker(
    db: Session,
    ticker: str,
    pages: int = 3,
) -> list[NewsArticle]:
    """Scrape recent news from Naver Finance for a ticker and store in DB."""
    new_articles = []
    seen_urls: set[str] = set()

    for page in range(1, pages + 1):
        params = {
            "code": ticker,
            "page": page,
            "sm": "title_entity_id.basic",
            "clusterId": "",
        }
        headers = {
            **HEADERS,
            "Referer": f"https://finance.naver.com/item/news.naver?code={ticker}",
        }

        try:
            resp = requests.get(NAVER_NEWS_URL, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.error("Failed to fetch news page %d for %s: %s", page, ticker, e)
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table.type5 tr")

        for row in rows:
            tds = row.select("td")
            if len(tds) < 3:
                continue

            title_td = tds[0]
            a_tag = title_td.select_one("a")
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            if not title:
                continue

            href = a_tag.get("href", "")
            if not href:
                continue

            if href.startswith("/"):
                article_url = NAVER_NEWS_READ_URL + href
            else:
                article_url = href

            source = tds[1].get_text(strip=True) if len(tds) > 1 else ""
            published_at = None
            if len(tds) > 2:
                date_text = tds[2].get_text(strip=True)
                for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d"):
                    try:
                        published_at = datetime.strptime(date_text, fmt)
                        break
                    except ValueError:
                        continue

            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)

            existing = db.execute(
                select(NewsArticle).where(NewsArticle.url == article_url)
            ).scalar_one_or_none()
            if existing:
                continue

            article = NewsArticle(
                ticker=ticker,
                title=title,
                source=source,
                url=article_url,
                published_at=published_at,
            )
            db.add(article)
            new_articles.append(article)

        time.sleep(settings.SCRAPE_DELAY_SECONDS)

    if new_articles:
        db.commit()
        logger.info("Saved %d new news articles for %s", len(new_articles), ticker)

    return new_articles


def get_news(
    db: Session,
    ticker: str | None = None,
    limit: int = 30,
) -> list[NewsArticle]:
    """Read news articles from DB."""
    stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc().nullslast())

    if ticker:
        stmt = stmt.where(NewsArticle.ticker == ticker)

    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())
