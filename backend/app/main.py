import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.jobs.scheduler import init_scheduler, shutdown_scheduler
from app.routers import stocks, screener, analysis, disclosures, news, system


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize resources on startup, clean up on shutdown."""
    logger.info("Starting Stock Analyzer API -- initializing database...")
    init_db()
    logger.info("Database initialized successfully.")
    init_scheduler()
    logger.info("Scheduler initialized.")
    yield
    shutdown_scheduler()
    logger.info("Shutting down Stock Analyzer API.")


app = FastAPI(
    title="Korean Stock Market Analyzer",
    description="Backend API for Korean stock market analysis, screening, and reporting.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router)
app.include_router(screener.router)
app.include_router(analysis.router)
app.include_router(disclosures.router)
app.include_router(news.router)
app.include_router(system.router)


@app.get("/")
def root() -> dict:
    return {"status": "ok", "name": "Stock Analyzer API"}


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy"}
