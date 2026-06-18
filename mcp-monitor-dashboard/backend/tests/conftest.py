"""
Shared test fixtures for all test modules
"""

import pytest
import asyncio
import os


@pytest.fixture(scope="session", autouse=True)
def init_database():
    """Initialize database once for all tests."""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    from app.core.database import init_db
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_db())
    loop.close()
    yield
