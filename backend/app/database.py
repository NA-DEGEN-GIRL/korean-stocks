from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from collections.abc import Generator

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


def init_db() -> None:
    """Create all tables defined by models that inherit from Base."""
    import app.models  # noqa: F401 -- ensure all models are imported before create_all
    Base.metadata.create_all(bind=engine)
