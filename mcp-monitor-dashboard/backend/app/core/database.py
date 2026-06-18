"""
Database connection and initialization
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create data directory if not exists
os.makedirs("data", exist_ok=True)

# Use synchronous SQLite for simplicity (can upgrade to async later)
DATABASE_URL = settings.database_url.replace("sqlite://", "sqlite:///")

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def init_db():
    """Initialize database - create tables."""
    global engine, SessionLocal

    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL, echo=settings.app_debug)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Import all models to register them with Base
    from app.models import agent, log, project, alert  # noqa: F401

    # Create tables
    Base.metadata.create_all(engine)

    logger.info(f"✅ Database initialized at {DATABASE_URL}")


def get_db():
    """Get database session (dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
