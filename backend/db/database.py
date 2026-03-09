"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import get_settings


def get_sync_engine():
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.APP_ENV == "development",
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        echo=settings.APP_ENV == "development",
    )


# Use sync engine with sync sessions for simplicity
engine = get_sync_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
