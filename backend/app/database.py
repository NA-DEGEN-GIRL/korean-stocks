import logging

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from collections.abc import Generator

logger = logging.getLogger(__name__)

from app.config import settings


db_url = settings.effective_database_url

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    echo=False,
)


@event.listens_for(engine, "connect")
def set_sqlite_wal_mode(dbapi_connection, connection_record):
    """Enable WAL mode for SQLite to allow concurrent reads during writes."""
    if db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_add_columns() -> None:
    """Add missing columns to existing tables (simple migration)."""
    insp = inspect(engine)
    migrations = {
        "dart_disclosures": {
            "ai_summary": "TEXT",
            "ai_impact": "VARCHAR(20)",
            "ai_analyzed_at": "DATETIME",
        },
    }
    with engine.begin() as conn:
        for table, columns in migrations.items():
            if not insp.has_table(table):
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for col_name, col_type in columns.items():
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                    logger.info("Added column %s.%s", table, col_name)


def init_db() -> None:
    """Create all tables defined by models that inherit from Base."""
    import app.models  # noqa: F401 -- ensure all models are imported before create_all
    Base.metadata.create_all(bind=engine)
    _migrate_add_columns()
