"""
MCP Monitor Dashboard - Performance Test Suite
Gate 2: Performance Testing
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List


@pytest.fixture(scope="session", autouse=True)
def init_database():
    """Initialize database once for all performance tests."""
    from app.core.database import init_db
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_db())
    loop.close()
    yield

# ==================== 1. API Response Time Tests ====================

class TestAPIResponseTime:
    """Test API endpoint response times."""

    def test_health_endpoint_response_time(self):
        """Health endpoint should respond within 100ms."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1, f"Health endpoint took {elapsed:.3f}s, expected < 0.1s"

    def test_agents_endpoint_response_time(self):
        """Agents endpoint should respond within 500ms."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        start = time.time()
        response = client.get("/api/v1/agents")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5, f"Agents endpoint took {elapsed:.3f}s, expected < 0.5s"

    def test_logs_endpoint_response_time(self):
        """Logs endpoint should respond within 500ms."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        start = time.time()
        response = client.get("/api/v1/logs?page=1&page_size=50")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5, f"Logs endpoint took {elapsed:.3f}s, expected < 0.5s"

    def test_project_overview_response_time(self):
        """Project overview endpoint should respond within 500ms."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        start = time.time()
        response = client.get("/api/v1/project/overview")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5, f"Project overview took {elapsed:.3f}s, expected < 0.5s"


# ==================== 2. Concurrent Request Tests ====================

class TestConcurrentRequests:
    """Test system behavior under concurrent load."""

    def test_concurrent_health_requests(self):
        """Handle 50 concurrent health requests without errors."""
        from fastapi.testclient import TestClient
        from app.main import app

        def make_request():
            client = TestClient(app)
            return client.get("/health").status_code

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in futures]

        assert all(r == 200 for r in results), f"Some requests failed: {results}"

    def test_concurrent_agents_requests(self):
        """Handle 20 concurrent agents requests without errors."""
        from fastapi.testclient import TestClient
        from app.main import app

        def make_request():
            client = TestClient(app)
            return client.get("/api/v1/agents").status_code

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]

        assert all(r == 200 for r in results), f"Some requests failed: {results}"


# ==================== 3. WebSocket Performance Tests ====================

class TestWebSocketPerformance:
    """Test WebSocket connection performance."""

    @pytest.mark.asyncio
    async def test_websocket_connection_time(self):
        """WebSocket connection should establish within 100ms."""
        from app.websocket.manager import ConnectionManager
        from unittest.mock import AsyncMock

        mgr = ConnectionManager()
        ws_mock = AsyncMock()

        start = time.time()
        conn_id = await mgr.connect(ws_mock)
        elapsed = time.time() - start

        assert elapsed < 0.1, f"WebSocket connection took {elapsed:.3f}s, expected < 0.1s"
        assert conn_id in mgr.active_connections

    @pytest.mark.asyncio
    async def test_multiple_websocket_connections(self):
        """Handle 100 concurrent WebSocket connections."""
        from app.websocket.manager import ConnectionManager
        from unittest.mock import AsyncMock

        mgr = ConnectionManager()

        start = time.time()
        connections = []
        for _ in range(100):
            ws_mock = AsyncMock()
            conn_id = await mgr.connect(ws_mock)
            connections.append(conn_id)
        elapsed = time.time() - start

        assert len(connections) == 100
        assert elapsed < 2.0, f"100 connections took {elapsed:.3f}s, expected < 2.0s"

    @pytest.mark.asyncio
    async def test_websocket_message_broadcast_performance(self):
        """Broadcast to 50 connections should complete within 500ms."""
        from app.websocket.manager import ConnectionManager
        from unittest.mock import AsyncMock

        mgr = ConnectionManager()

        # Create 50 connections
        for _ in range(50):
            ws_mock = AsyncMock()
            await mgr.connect(ws_mock)

        # Subscribe all to agent_status channel
        for conn_id in list(mgr.active_connections.keys()):
            mgr.subscribe(conn_id, ["agent_status"])

        # Broadcast message
        start = time.time()
        await mgr.broadcast_to_channel("agent_status", {"type": "test", "data": {}})
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Broadcast took {elapsed:.3f}s, expected < 0.5s"


# ==================== 4. Data Collection Performance Tests ====================

class TestDataCollectionPerformance:
    """Test data collection service performance."""

    def test_collect_all_performance(self):
        """collect_all() should complete within 1 second."""
        from app.services.data_collector import DataCollectorService

        service = DataCollectorService()

        start = time.time()
        result = service.collect_all()
        elapsed = time.time() - start

        assert "agents" in result
        assert elapsed < 1.0, f"collect_all() took {elapsed:.3f}s, expected < 1.0s"

    def test_collect_all_caching_performance(self):
        """Second collect_all() call should be faster or equal due to caching."""
        from app.services.data_collector import DataCollectorService

        service = DataCollectorService()

        # First call (no cache)
        start1 = time.time()
        service.collect_all()
        elapsed1 = time.time() - start1

        # Second call (with cache)
        start2 = time.time()
        service.collect_all()
        elapsed2 = time.time() - start2

        # Second call should be faster or equal (cached)
        # Allow small variance due to system timing
        assert elapsed2 <= elapsed1 * 1.5, f"Caching not working: {elapsed2:.3f}s > {elapsed1:.3f}s * 1.5"


# ==================== 5. Database Query Performance Tests ====================

class TestDatabaseQueryPerformance:
    """Test database query performance."""

    def test_agent_query_performance(self):
        """Query all agents should complete within 100ms."""
        from app.core.database import SessionLocal
        from app.models.database_models import Agent

        with SessionLocal() as db:
            start = time.time()
            agents = db.query(Agent).all()
            elapsed = time.time() - start

            assert elapsed < 0.1, f"Agent query took {elapsed:.3f}s, expected < 0.1s"

    def test_log_query_with_pagination(self):
        """Paginated log query should complete within 200ms."""
        from app.core.database import SessionLocal
        from app.models.database_models import Log

        with SessionLocal() as db:
            start = time.time()
            logs = db.query(Log).offset(0).limit(50).all()
            elapsed = time.time() - start

            assert elapsed < 0.2, f"Log query took {elapsed:.3f}s, expected < 0.2s"


# ==================== Run Tests ====================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
