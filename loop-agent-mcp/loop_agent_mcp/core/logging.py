"""v1.3 结构化日志与审计模块。

改进 v1.2 的可观测性问题：
- v1.2 只有 print，调试困难
- 现在使用 logging + JSON 格式 + 工具调用审计

设计：
- 双输出：stderr（人读） + audit（机器读）
- 自动脱敏（密码、token、content 字段）
- 工具调用审计（tool_name, arguments, duration, status）
"""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, ClassVar


# 敏感字段（自动脱敏）
SENSITIVE_FIELDS = frozenset({"content", "password", "token", "secret", "api_key", "authorization"})


class JsonFormatter(logging.Formatter):
    """JSON 格式日志，便于机器解析。"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        # 附加字段
        for key in ("tool_name", "agent_name", "loop_id", "duration_ms", "status"):
            value = getattr(record, key, None)
            if value is not None:
                log_data[key] = value
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO", json_output: bool = True) -> logging.Logger:
    """配置日志系统。

    Args:
        level: 日志级别（DEBUG/INFO/WARNING/ERROR）。
        json_output: 是否使用 JSON 格式（否则人类可读）。

    Returns:
        配置好的 root logger。
    """
    root_logger = logging.getLogger("loop_agent_mcp")
    root_logger.setLevel(level)

    # 避免重复添加 handler
    if root_logger.handlers:
        return root_logger

    handler = logging.StreamHandler(sys.stderr)
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    root_logger.addHandler(handler)
    root_logger.propagate = False

    return root_logger


# 默认 logger
logger = logging.getLogger("loop_agent_mcp.dispatcher")
audit_logger = logging.getLogger("loop_agent_mcp.audit")


def _sanitize_args(arguments: dict[str, Any]) -> dict[str, Any]:
    """脱敏处理：移除敏感字段。"""
    if not isinstance(arguments, dict):
        return arguments
    return {
        k: ("***REDACTED***" if k.lower() in SENSITIVE_FIELDS else v)
        for k, v in arguments.items()
    }


class ToolAuditLogger:
    """工具调用审计日志。"""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def log_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        duration_ms: float,
    ) -> None:
        """记录工具调用。"""
        safe_args = _sanitize_args(arguments)
        safe_result = _sanitize_args(result)

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tool_name": tool_name,
            "arguments": safe_args,
            "result_status": result.get("status", "unknown"),
            "duration_ms": round(duration_ms, 2),
        }
        self.calls.append(entry)

        # 写日志
        audit_logger.info(
            f"tool_call: {tool_name} -> {entry['result_status']} ({entry['duration_ms']}ms)",
            extra={
                "tool_name": tool_name,
                "duration_ms": entry["duration_ms"],
                "status": entry["result_status"],
            },
        )

    def get_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近的调用记录。"""
        return self.calls[-limit:]

    def clear(self) -> None:
        """清空历史。"""
        self.calls.clear()


# 全局审计 logger
_audit_instance: ToolAuditLogger | None = None


def get_audit_logger() -> ToolAuditLogger:
    """获取全局审计 logger。"""
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = ToolAuditLogger()
    return _audit_instance
