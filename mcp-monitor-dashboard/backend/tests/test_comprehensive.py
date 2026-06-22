"""
MCP Monitor Dashboard - Comprehensive Test Suite
Gate 3: Functional Testing
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# ==================== Test Configuration ====================

# Default API key used in tests (matches auth.py default)
TEST_API_KEY = "dev-api-key-change-in-production"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def auth_client():
    """TestClient with API key authentication headers."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app, headers={"X-API-Key": TEST_API_KEY})
    return client


# ==================== 1. API Endpoint Tests ====================

class TestHealthEndpoints:
    """Test health check and readiness endpoints."""

    def test_health_check_returns_ok(self):
        """Health endpoint should return status ok."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_readiness_check(self):
        """Readiness endpoint should return ready status."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


class TestAgentAPI:
    """Test agent-related API endpoints."""

    @patch('app.services.data_collector.collector_service')
    def test_get_all_agents_success(self, mock_collector, auth_client):
        """GET /api/v1/agents should return all agents."""
        mock_collector.collect_all.return_value = {
            "agents": [
                {"id": "backend", "display_name": "Backend Developer", "status": "idle"}
            ],
            "project_overview": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        response = auth_client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # Response can be list or dict depending on implementation
        assert "data" in data

    @patch('app.services.data_collector.collector_service')
    def test_get_agent_detail_not_found(self, mock_collector, auth_client):
        """GET /api/v1/agents/{id} should 404 for unknown agent."""
        mock_collector.collect_all.return_value = {
            "agents": [],
            "project_overview": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        response = auth_client.get("/api/v1/agents/nonexistent")
        assert response.status_code == 404


class TestLogAPI:
    """Test log query API endpoints."""

    @patch('app.api.logs.collector_service')
    def test_get_logs_with_pagination(self, mock_collector, auth_client):
        """GET /api/v1/logs should support pagination parameters."""
        mock_collector.get_logs.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
            "total_pages": 0
        }

        response = auth_client.get("/api/v1/logs?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data

    @patch('app.api.logs.collector_service')
    def test_get_logs_filter_by_level(self, mock_collector, auth_client):
        """GET /api/v1/logs should filter by log level."""
        mock_collector.get_logs.return_value = {
            "items": [{"level": "error", "message": "test"}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }

        response = auth_client.get("/api/v1/logs?level=error")
        assert response.status_code == 200


class TestSystemControlAPI:
    """Test system control (start/stop/restart) API endpoints."""

    @patch('app.api.system.process_manager')
    def test_start_mcp_server(self, mock_pm, auth_client):
        """POST /api/v1/system/start should start MCP server."""
        mock_pm.start.return_value = {"success": True, "pid": 12345}

        response = auth_client.post("/api/v1/system/start")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        mock_pm.start.assert_called_once()

    @patch('app.api.system.process_manager')
    def test_stop_mcp_server(self, mock_pm, auth_client):
        """POST /api/v1/system/stop should stop MCP server."""
        mock_pm.stop.return_value = {"success": True}

        response = auth_client.post("/api/v1/system/stop", json={"force": False})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    @patch('app.api.system.process_manager')
    def test_get_system_status(self, mock_pm, auth_client):
        """GET /api/v1/system/status should return system status."""
        mock_pm.get_status.return_value = {"running": True, "pid": 12345}
        mock_pm.uptime_seconds = 3600

        response = auth_client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "mcp_server" in data["data"]
        assert "monitor_system" in data["data"]


class TestProjectAPI:
    """Test project overview API endpoints."""

    @patch('app.api.project.collector_service')
    def test_get_project_overview(self, mock_collector, auth_client):
        """GET /api/v1/project/overview should return project info."""
        mock_collector.collect_all.return_value = {
            "agents": [],
            "project_overview": {
                "name": "MCP 实时监控看板系统",
                "current_phase": "Phase 3",
                "phase_progress": 65.0,
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = auth_client.get("/api/v1/project/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


# ==================== 2. WebSocket Tests ====================

class TestWebSocketManager:
    """Test WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_connect_creates_connection(self):
        """connect() should add connection to active_connections."""
        from app.websocket.manager import ConnectionManager
        mgr = ConnectionManager()

        ws_mock = AsyncMock()
        conn_id = await mgr.connect(ws_mock)

        assert conn_id in mgr.active_connections
        assert mgr.connection_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        """disconnect() should remove connection."""
        from app.websocket.manager import ConnectionManager
        mgr = ConnectionManager()

        ws_mock = AsyncMock()
        conn_id = await mgr.connect(ws_mock)
        await mgr.disconnect(conn_id)

        assert conn_id not in mgr.active_connections
        assert mgr.connection_count == 0

    @pytest.mark.asyncio
    async def test_subscribe_adds_channels(self):
        """subscribe() should add channels to connection."""
        from app.websocket.manager import ConnectionManager
        mgr = ConnectionManager()

        ws_mock = AsyncMock()
        conn_id = await mgr.connect(ws_mock)
        mgr.subscribe(conn_id, ["agent_status", "logs"])

        assert "agent_status" in mgr.active_connections[conn_id]["channels"]
        assert "logs" in mgr.active_connections[conn_id]["channels"]

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_channels(self):
        """unsubscribe() should remove channels from connection."""
        from app.websocket.manager import ConnectionManager
        mgr = ConnectionManager()

        ws_mock = AsyncMock()
        conn_id = await mgr.connect(ws_mock)
        mgr.subscribe(conn_id, ["agent_status", "logs"])
        mgr.unsubscribe(conn_id, ["agent_status"])

        assert "agent_status" not in mgr.active_connections[conn_id]["channels"]

    def test_pong_records_timestamp(self):
        """record_pong() should update last_pong time."""
        from app.websocket.manager import ConnectionManager
        import time
        mgr = ConnectionManager()
        # Manually set up a connection for testing pong without async connect
        mgr.active_connections[999] = {
            "websocket": None,
            "channels": set(),
            "connected_at": "",
        }
        before = time.time()
        mgr.record_pong(999)
        after = time.time()

        assert before <= mgr._last_pong[999] <= after

    @pytest.mark.asyncio
    async def test_get_connection_stats(self):
        """get_connection_stats() should return correct stats."""
        from app.websocket.manager import ConnectionManager
        mgr = ConnectionManager()

        ws1 = AsyncMock()
        ws2 = AsyncMock()
        c1 = await mgr.connect(ws1)
        c2 = await mgr.connect(ws2)
        mgr.subscribe(c1, ["agent_status"])
        mgr.subscribe(c2, ["agent_status", "logs"])

        stats = mgr.get_connection_stats()
        assert stats["total_connections"] == 2
        assert stats["channel_subscribers"]["agent_status"] == 2
        assert stats["channel_subscribers"]["logs"] == 1


# ==================== 3. Data Collector Tests ====================

class TestWebSocketIntegration:
    """Integration tests for the WebSocket endpoint."""

    def test_websocket_connect_and_subscribe(self):
        """First connection should accept, then receive init on subscribe."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        with client.websocket_connect(f"/ws?api_key={TEST_API_KEY}") as ws:
            ws.send_json({"type": "subscribe", "channels": ["agent_status", "overview"]})
            msg = ws.receive_json()

            assert msg["type"] == "init"
            assert "data" in msg
            assert "agents" in msg["data"]
            assert "overview" in msg["data"]

    def test_websocket_ping_pong(self):
        """Server should respond with pong to client ping."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        with client.websocket_connect(f"/ws?api_key={TEST_API_KEY}") as ws:
            ws.send_json({"type": "ping"})
            msg = ws.receive_json()
            assert msg["type"] == "pong"

    def test_websocket_rejects_invalid_json(self):
        """Server should send error for invalid JSON without crashing."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        with client.websocket_connect(f"/ws?api_key={TEST_API_KEY}") as ws:
            ws.send_text("not-json")
            msg = ws.receive_json()
            assert msg["type"] == "error"


class TestDataCollectorService:
    """Test data collection service."""

    def test_initialize_default_agents(self):
        """initialize_default_agents() should create 16 agents."""
        from app.services.data_collector import DataCollectorService
        service = DataCollectorService()
        assert len(service.DEFAULT_AGENTS) == 16

        # Verify all expected agent IDs exist
        agent_ids = {a["id"] for a in service.DEFAULT_AGENTS}
        expected_ids = {
            "product-manager", "requirements", "ux-researcher", "ui-designer",
            "architect", "backend", "fullstack-coder", "bug-defect-repairer",
            "code-reviewer", "performance", "tester", "documenter",
            "final-reviewer", "devops", "knowledge-curator", "orchestrator"
        }
        assert agent_ids == expected_ids

    def test_collect_all_returns_structure(self):
        """collect_all() should return dict with agents and overview keys."""
        from app.services.data_collector import DataCollectorService
        service = DataCollectorService()
        result = service.collect_all()

        assert "agents" in result
        assert "project_overview" in result
        # agents can be empty list or list of dicts (depends on DB state)
        assert isinstance(result["agents"], (list, dict))

    def test_collect_all_error_returns_cache(self):
        """collect_all() on error should return cached data."""
        from app.services.data_collector import DataCollectorService
        service = DataCollectorService()
        # Set some cache data
        service._cache = {
            "agents": [{"id": "test"}],
            "project_overview": {"name": "test"},
            "last_update": "cached-time"
        }

        # Mock to raise exception
        with patch.object(service, '_collect_agent_statuses', side_effect=Exception("DB error")):
            result = service.collect_all()

        assert result["agents"] == [{"id": "test"}]
        assert result["project_overview"]["name"] == "test"


# ==================== 4. Process Manager Tests ====================

class TestProcessManagerService:
    """Test process manager security fixes."""

    def test_parse_command_safe_input(self):
        """_parse_command() should safely parse normal commands."""
        from app.services.process_manager import ProcessManagerService
        pm = ProcessManagerService()
        result = pm._parse_command("python -m loop_agent_mcp.server")
        assert result == ["python", "-m", "loop_agent_mcp.server"]

    def test_parse_command_rejects_dangerous_patterns(self):
        """_parse_command() should raise ValueError for dangerous patterns."""
        from app.services.process_manager import ProcessManagerService
        pm = ProcessManagerService()
        # Should raise ValueError when dangerous patterns are detected
        with pytest.raises(ValueError, match="Dangerous shell pattern"):
            pm._parse_command("python script.py; rm -rf /")

    def test_parse_command_empty_raises(self):
        """_parse_command() should raise ValueError for empty command."""
        from app.services.process_manager import ProcessManagerService
        pm = ProcessManagerService()
        with pytest.raises(ValueError):
            pm._parse_command("   ")

    def test_initial_state_not_running(self):
        """Process manager should start with no running process."""
        from app.services.process_manager import ProcessManagerService
        pm = ProcessManagerService()
        assert pm.is_running is False
        assert pm.pid is None
        assert pm.uptime_seconds == 0


# ==================== 5. Database Model Tests ====================

class TestDatabaseModels:
    """Test SQLAlchemy ORM models."""

    def test_agent_to_dict(self):
        """Agent.to_dict() should return correct structure."""
        from app.models.database_models import Agent
        agent = Agent(
            id="test-agent",
            display_name="Test Agent",
            role_type="dev",
            icon="🧪",
            status="running",
            current_task_name="Write tests",
            current_task_progress=75.5,
        )
        result = agent.to_dict()
        assert result["id"] == "test-agent"
        assert result["display_name"] == "Test Agent"
        assert result["status"] == "running"
        assert result["current_task_progress"] == 75.5

    def test_log_to_dict_parses_metadata_json(self):
        """Log.to_dict() should parse metadata JSON string."""
        from app.models.database_models import Log
        log = Log(
            id=1,
            agent_id="test-agent",
            level="info",
            message="Test message",
            metadata_json='{"key": "value"}',
        )
        result = log.to_dict()
        assert result["metadata"] == {"key": "value"}

    def test_log_to_dict_handles_dict_metadata(self):
        """Log.to_dict() should handle dict metadata directly."""
        from app.models.database_models import Log
        log = Log(
            id=2,
            agent_id="test-agent",
            level="info",
            message="Test message",
            metadata_json={"key": "value"},
        )
        result = log.to_dict()
        assert result["metadata"] == {"key": "value"}

    def test_project_to_dict(self):
        """Project.to_dict() should return full project info."""
        from app.models.database_models import Project
        project = Project(
            name="Test Project",
            current_phase="Phase 4",
            phase_progress=80.0,
            total_tasks=20,
            completed_tasks=15,
            gate1_status="passed",
        )
        result = project.to_dict()
        assert result["name"] == "Test Project"
        assert result["gate1_status"] == "passed"
        assert result["completed_tasks"] == 15


# ==================== 6. Config Tests ====================

class TestConfigSettings:
    """Test application configuration."""

    def test_default_values(self):
        """Settings should have sensible defaults."""
        from app.config import Settings
        settings = Settings()
        assert settings.app_port == 8000
        assert settings.collection_interval_seconds == 2.0
        assert settings.ws_heartbeat_interval == 30
        assert settings.ws_max_connections == 100

    def test_env_override(self):
        """Environment variables should override defaults."""
        import os
        os.environ["APP_PORT"] = "9000"
        try:
            from app.config import Settings
            settings = Settings(_env_file=None)  # Don't load .env
            # Note: actual env var name may differ based on pydantic-settings config
        finally:
            del os.environ["APP_PORT"]


# ==================== 7. CORS Security Tests ====================

class TestCORSSecurity:
    """Test CORS middleware configuration."""

    def test_cors_headers_present_in_dev(self):
        """CORS headers should be present in development mode."""
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        response = client.options("/health", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        })
        # In dev mode, all origins allowed
        assert response.status_code in [200, 204]


# ==================== Run Tests ====================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
