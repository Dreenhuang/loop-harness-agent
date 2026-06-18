"""
SQLAlchemy ORM models for database tables
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from app.core.database import Base


class Agent(Base):
    """Agent status table."""
    __tablename__ = "agents"

    id = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    role_type = Column(String(50), nullable=False)
    icon = Column(String(10), default="🤖")
    status = Column(String(20), default="idle", nullable=False)
    current_task_name = Column(String(200))
    current_task_phase = Column(Integer)
    current_task_progress = Column(Float, default=0.0)
    last_activity_time = Column(DateTime)
    error_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    logs = relationship("Log", back_populates="agent", lazy="dynamic")

    __table_args__ = (
        Index("idx_agents_status", "status"),
        Index("idx_agents_updated", "updated_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "display_name": self.display_name,
            "role_type": self.role_type,
            "icon": self.icon,
            "status": self.status,
            "current_task_name": self.current_task_name,
            "current_task_phase": self.current_task_phase,
            "current_task_progress": self.current_task_progress,
            "last_activity_time": self.last_activity_time.isoformat() if self.last_activity_time else None,
            "error_summary": self.error_summary,
        }


class Log(Base):
    """Operation log table."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    level = Column(String(10), default="info", nullable=False)
    message = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="logs")

    __table_args__ = (
        Index("idx_logs_agent", "agent_id"),
        Index("idx_logs_timestamp", "timestamp"),
        Index("idx_logs_level", "level"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "message": self.message,
            "metadata": json.loads(self.metadata_json) if isinstance(self.metadata_json, str) else (self.metadata_json or {}),
        }


class Project(Base):
    """Project information table."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)
    current_phase = Column(String(100))
    phase_progress = Column(Float, default=0.0)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    token_used = Column(Integer, default=0)
    token_total = Column(Integer, default=100000)
    gate1_status = Column(String(20), default="pending")
    gate2_status = Column(String(20), default="pending")
    gate3_status = Column(String(20), default="pending")
    gate4_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "current_phase": self.current_phase,
            "phase_progress": self.phase_progress,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "token_used": self.token_used,
            "token_total": self.token_total,
            "gate1_status": self.gate1_status,
            "gate2_status": self.gate2_status,
            "gate3_status": self.gate3_status,
            "gate4_status": self.gate4_status,
        }


class Alert(Base):
    """Alert records table."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), default="info", nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_alerts_resolved", "resolved"),
        Index("idx_alerts_created", "created_at"),
    )
