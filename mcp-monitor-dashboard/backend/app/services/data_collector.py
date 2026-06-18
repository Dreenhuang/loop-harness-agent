"""
Data Collection Service - collects data from MCP system
"""

import json
import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.config import settings
from app.core.database import SessionLocal
from app.models.database_models import Agent, Log, Project

logger = logging.getLogger(__name__)


class DataCollectorService:
    """Service for collecting data from MCP system."""

    # Default agent definitions (16 agents)
    DEFAULT_AGENTS = [
        {"id": "product-manager", "display_name": "Product Manager", "role_type": "planning", "icon": "📋"},
        {"id": "requirements", "display_name": "Requirements Analyst", "role_type": "planning", "icon": "📝"},
        {"id": "ux-researcher", "display_name": "UX Researcher", "role_type": "design", "icon": "👥"},
        {"id": "ui-designer", "display_name": "UI Designer", "role_type": "design", "icon": "🎨"},
        {"id": "architect", "display_name": "Architect", "role_type": "design", "icon": "🏗️"},
        {"id": "backend", "display_name": "Backend Developer", "role_type": "dev", "icon": "⚙️"},
        {"id": "fullstack-coder", "display_name": "Frontend Developer", "role_type": "dev", "icon": "💻"},
        {"id": "bug-defect-repairer", "display_name": "Bug Fixer", "role_type": "dev", "icon": "🐛"},
        {"id": "code-reviewer", "display_name": "Code Reviewer", "role_type": "quality", "icon": "✅"},
        {"id": "performance", "display_name": "Performance Engineer", "role_type": "quality", "icon": "⚡"},
        {"id": "tester", "display_name": "QA Tester", "role_type": "test", "icon": "🧪"},
        {"id": "documenter", "display_name": "Documenter", "role_type": "docs", "icon": "📄"},
        {"id": "final-reviewer", "display_name": "Final Reviewer", "role_type": "quality", "icon": "🔍"},
        {"id": "devops", "display_name": "DevOps Engineer", "role_type": "ops", "icon": "☁️"},
        {"id": "knowledge-curator", "display_name": "Knowledge Curator", "role_type": "docs", "icon": "📚"},
        {"id": "orchestrator", "display_name": "Orchestrator", "role_type": "management", "icon": "🎯"},
    ]

    def __init__(self):
        self._cache: Dict = {
            "agents": {},
            "project_overview": None,
            "last_update": None,
        }

    def initialize_default_agents(self):
        """Initialize default 16 agents in database."""
        db = SessionLocal()
        try:
            for agent_data in self.DEFAULT_AGENTS:
                existing = db.query(Agent).filter_by(id=agent_data["id"]).first()
                if not existing:
                    agent = Agent(**agent_data)
                    db.add(agent)
            db.commit()
            logger.info(f"✅ Initialized {len(self.DEFAULT_AGENTS)} default agents")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            db.rollback()
        finally:
            db.close()

    def collect_all(self) -> Dict:
        """Collect all data from MCP system."""
        try:
            # Collect agent statuses
            agents_data = self._collect_agent_statuses()

            # Collect project overview
            project_data = self._collect_project_overview()

            # Update cache
            self._cache["agents"] = agents_data
            self._cache["project_overview"] = project_data
            self._cache["last_update"] = datetime.utcnow().isoformat()

            return {
                "agents": agents_data,
                "project_overview": project_data,
                "timestamp": self._cache["last_update"],
            }
        except Exception as e:
            logger.error(f"❌ Data collection failed: {e}")
            return self._cache  # Return cached data on error

    def _collect_agent_statuses(self) -> List[Dict]:
        """Collect current status of all agents."""
        db = SessionLocal()
        try:
            agents = db.query(Agent).all()
            result = []
            for agent in agents:
                agent_dict = agent.to_dict()

                # Simulate real-time status (in production, read from MCP)
                # For MVP, we'll use mock data that simulates activity
                if agent.status == "running":
                    # Simulate progress increment
                    if agent.current_task_progress is not None:
                        agent_dict["current_task_progress"] = min(
                            100.0, agent.current_task_progress + 0.5
                        )
                        # Auto-complete at 100%
                        if agent_dict["current_task_progress"] >= 100.0:
                            agent_dict["status"] = "complete"
                            self._update_agent_status(db, agent.id, "complete")

                result.append(agent_dict)

            return result
        finally:
            db.close()

    def _collect_project_overview(self) -> Dict:
        """Collect project overview statistics."""
        db = SessionLocal()
        try:
            project = db.query(Project).filter_by(name="MCP 实时监控看板系统").first()
            if project:
                return project.to_dict()

            # Create default project if not exists
            project = Project(
                name="MCP 实时监控看板系统",
                current_phase="Phase 3: Architecture Design",
                phase_progress=65.0,
                total_tasks=48,
                completed_tasks=12,
                failed_tasks=2,
                token_used=45000,
                token_total=100000,
                gate1_status="passed",
                gate2_status="pending",
                gate3_status="pending",
                gate4_status="pending",
            )
            db.add(project)
            db.commit()
            return project.to_dict()
        finally:
            db.close()

    def _update_agent_status(self, db, agent_id: str, new_status: str):
        """Update agent status in database."""
        agent = db.query(Agent).filter_by(id=agent_id).first()
        if agent:
            agent.status = new_status
            agent.updated_at = datetime.utcnow()
            db.commit()

    def add_log_entry(self, agent_id: str, level: str, message: str, metadata: dict = None):
        """Add a log entry to the database."""
        db = SessionLocal()
        try:
            log_entry = Log(
                agent_id=agent_id,
                level=level,
                message=message,
                metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
            )
            db.add(log_entry)
            db.commit()
            return log_entry.to_dict()
        except Exception as e:
            logger.error(f"❌ Failed to add log entry: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_logs(
        self,
        agent_id: Optional[str] = None,
        level: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict:
        """Query logs with filtering and pagination."""
        db = SessionLocal()
        try:
            query = db.query(Log)

            if agent_id:
                query = query.filter(Log.agent_id == agent_id)
            if level:
                query = query.filter(Log.level == level)
            if keyword:
                query = query.filter(Log.message.contains(keyword))

            total = query.count()
            logs = (
                query.order_by(Log.timestamp.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            return {
                "items": [log.to_dict() for log in logs],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        finally:
            db.close()

    def get_cached_data(self) -> Dict:
        """Get cached data (for WebSocket init)."""
        return self._cache


# Singleton instance
collector_service = DataCollectorService()
