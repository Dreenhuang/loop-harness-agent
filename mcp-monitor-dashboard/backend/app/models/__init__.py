"""
Pydantic models for data validation and serialization
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enum."""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    COMPLETE = "complete"


class LogLevel(str, Enum):
    """Log level enum."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class GateStatus(str, Enum):
    """Gate status enum."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


# ==================== Agent Models ====================

class AgentBase(BaseModel):
    """Base agent model."""
    id: str = Field(..., description="Agent identifier")
    display_name: str = Field(..., description="Display name")
    role_type: str = Field(..., description="Role type (planning/design/dev/test/ops)")
    icon: str = Field(default="🤖", description="Icon or emoji")


class AgentCreate(AgentBase):
    """Agent creation model."""
    pass


class AgentTask(BaseModel):
    """Current task info for an agent."""
    name: Optional[str] = None
    phase: Optional[int] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    started_at: Optional[datetime] = None
    estimated_end: Optional[datetime] = None


class AgentResponse(AgentBase):
    """Agent response model with full status."""
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    current_task: Optional[AgentTask] = None
    last_activity_time: Optional[datetime] = None
    error_summary: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Log Models ====================

class LogEntryBase(BaseModel):
    """Base log entry model."""
    agent_id: str
    level: LogLevel = Field(default=LogLevel.INFO)
    message: str
    metadata: dict = Field(default_factory=dict)


class LogEntryCreate(LogEntryBase):
    """Log entry creation model."""
    timestamp: Optional[datetime] = None


class LogEntryResponse(LogEntryBase):
    """Log entry response model."""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class LogQueryParams(BaseModel):
    """Log query parameters."""
    agent_id: Optional[str] = None
    level: Optional[LogLevel] = None
    keyword: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ==================== Project Models ====================

class TokenBudget(BaseModel):
    """Token budget information."""
    used: int = 0
    total: int = 100000
    percentage: float = 0.0


class TaskStats(BaseModel):
    """Task statistics."""
    total: int = 0
    completed: int = 0
    in_progress: int = 0
    failed: int = 0
    pending: int = 0


class AgentStats(BaseModel):
    """Agent statistics."""
    total: int = 16
    active: int = 0
    idle: int = 0
    error: int = 0


class GateInfo(BaseModel):
    """Gate status information."""
    gate1_code_review: GateStatus = GateStatus.PENDING
    gate2_performance: GateStatus = GateStatus.PENDING
    gate3_testing: GateStatus = GateStatus.PENDING
    gate4_final_review: GateStatus = GateStatus.PENDING


class ProjectOverviewResponse(BaseModel):
    """Project overview response."""
    project_name: str = "MCP 实时监控看板系统"
    current_phase: str = ""
    phase_progress: float = 0.0
    tasks: TaskStats = Field(default_factory=TaskStats)
    token_budget: TokenBudget = Field(default_factory=TokenBudget)
    agents: AgentStats = Field(default_factory=AgentStats)
    gates: GateInfo = Field(default_factory=GateInfo)
    uptime_seconds: int = 0
    last_update: Optional[datetime] = None


# ==================== System Models ====================

class MCPServerStatus(BaseModel):
    """MCP Server process status."""
    status: str = "stopped"  # running/stopped/error
    pid: Optional[int] = None
    uptime_seconds: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


class MonitorSystemStatus(BaseModel):
    """Monitor system status."""
    version: str = "1.0.0"
    websocket_connections: int = 0
    uptime_seconds: int = 0


class SystemStatusResponse(BaseModel):
    """Combined system status response."""
    mcp_server: MCPServerStatus = Field(default_factory=MCPServerStatus)
    monitor_system: MonitorSystemStatus = Field(default_factory=MonitorSystemStatus)


# ==================== Control Models ====================

class StopRequest(BaseModel):
    """Stop server request."""
    force: bool = False


class OperationResponse(BaseModel):
    """Generic operation response."""
    code: int = 0
    message: str = ""
    data: Optional[dict] = None


# ==================== WebSocket Models ====================

class WSMessageType(str, Enum):
    """WebSocket message types."""
    # Client → Server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    REQUEST_FULL_SYNC = "request_full_sync"

    # Server → Client
    INIT = "init"
    AGENT_STATUS_UPDATE = "agent_status_update"
    LOG_ENTRY = "log_entry"
    PROJECT_OVERVIEW_UPDATE = "project_overview_update"
    PROGRESS_UPDATE = "progress_update"
    ALERT = "alert"
    PONG = "pong"
    ERROR = "error"


class WSMessage(BaseModel):
    """WebSocket message base."""
    type: WSMessageType
    data: Optional[dict | list] = None
    channel: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSSubscribeRequest(BaseModel):
    """Client subscription request."""
    type: str = "subscribe"
    channels: List[str] = Field(default=["agent_status", "logs", "overview"])


# ==================== Alert Models ====================

class AlertType(str, Enum):
    """Alert type enum."""
    DEVIATION = "deviation"
    TOKEN_OVER_BUDGET = "token_over_budget"
    GATE_FAILED = "gate_failed"
    MCP_SERVER_DOWN = "mcp_server_down"


class AlertSeverity(str, Enum):
    """Alert severity enum."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCreate(BaseModel):
    """Alert creation model."""
    type: AlertType
    severity: AlertSeverity
    title: str
    message: Optional[str] = None


class AlertResponse(AlertCreate):
    """Alert response model."""
    id: int
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
