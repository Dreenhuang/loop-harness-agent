"""
Database connection and initialization
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create data directory if not exists
data_dir = os.path.dirname(settings.database_url.replace("sqlite:///", ""))
if data_dir:
    os.makedirs(data_dir, exist_ok=True)

# Use synchronous SQLite for simplicity (can upgrade to async later)
# Handle SQLite URL properly
if settings.database_url.startswith("sqlite:///"):
    # Already has correct format, use as-is
    DATABASE_URL = settings.database_url
else:
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
    # Use sync sessionmaker for sync SQLite engine
    from sqlalchemy.orm import sessionmaker as _sync_sessionmaker
    SessionLocal = _sync_sessionmaker(bind=engine, expire_on_commit=False)

    # Import all models to register them with Base
    from app.models.database_models import Agent, Log, Project  # noqa: F401

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
