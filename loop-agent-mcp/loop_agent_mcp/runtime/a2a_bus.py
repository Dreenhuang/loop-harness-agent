"""A2A 消息总线：任务生命周期事件发布/订阅。

提供轻量级内存级 pub/sub，支持任务状态变更事件的发布与订阅。
"""
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Any, Callable

from loop_agent_mcp.runtime.task import Task, TaskStatus


class A2AMessage:
    """A2A 消息实体。"""

    def __init__(
        self,
        topic: str,
        sender: str,
        receiver: str | None = None,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ):
        self.message_id = f"msg-{uuid.uuid4().hex[:12]}"
        self.topic = topic
        self.sender = sender
        self.receiver = receiver
        self.payload = payload or {}
        self.correlation_id = correlation_id
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "topic": self.topic,
            "sender": self.sender,
            "receiver": self.receiver,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }


A2AHandler = Callable[[A2AMessage], Any]


class A2ABus:
    """内存级轻量消息总线，支持 pub/sub。"""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[A2AHandler]] = defaultdict(list)
        # 限制历史长度，避免长期运行内存无界增长
        self._history: deque[A2AMessage] = deque(maxlen=10000)
        self._history_lock = threading.Lock()

    def subscribe(self, topic: str, handler: A2AHandler) -> None:
        """订阅指定 topic。"""
        self._subscribers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: A2AHandler) -> None:
        """取消订阅。"""
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(handler)
            except ValueError:
                pass

    async def publish(self, message: A2AMessage) -> None:
        """发布消息到所有订阅者（异步执行）。"""
        with self._history_lock:
            self._history.append(message)

        handlers = list(self._subscribers.get(message.topic, []))
        if not handlers:
            return

        coros = []
        for handler in handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    coros.append(result)
            except Exception:
                # 订阅者异常不应影响其他订阅者
                continue

        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    def publish_sync(self, message: A2AMessage) -> None:
        """同步发布消息（用于非 async 上下文）。"""
        with self._history_lock:
            self._history.append(message)
        handlers = list(self._subscribers.get(message.topic, []))
        for handler in handlers:
            try:
                handler(message)
            except Exception:
                continue

    def get_history(
        self,
        topic: str | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
    ) -> list[A2AMessage]:
        """获取已发布消息历史。"""
        results: list[A2AMessage] = list(self._history)
        if topic:
            results = [m for m in results if m.topic == topic]
        if correlation_id:
            results = [m for m in results if m.correlation_id == correlation_id]
        return results[-limit:]


# ---- 任务生命周期事件工厂函数 ----


def task_submitted_event(task: Task) -> A2AMessage:
    return A2AMessage(
        topic="task.submitted",
        sender="orchestrator",
        correlation_id=task.task_id,
        payload={
            "task_id": task.task_id,
            "loop_id": task.loop_id,
            "agent_name": task.agent_name,
            "priority": task.priority,
            "dependencies": task.dependencies,
        },
    )


def task_started_event(task: Task) -> A2AMessage:
    return A2AMessage(
        topic="task.started",
        sender=task.agent_name,
        correlation_id=task.task_id,
        payload={
            "task_id": task.task_id,
            "loop_id": task.loop_id,
            "agent_name": task.agent_name,
            "status": task.status.value,
            "started_at": task.started_at,
        },
    )


def task_progress_event(task: Task, progress: dict[str, Any]) -> A2AMessage:
    return A2AMessage(
        topic="task.progress",
        sender=task.agent_name,
        correlation_id=task.task_id,
        payload={
            "task_id": task.task_id,
            "loop_id": task.loop_id,
            "agent_name": task.agent_name,
            **progress,
        },
    )


def task_finished_event(task: Task) -> A2AMessage:
    return A2AMessage(
        topic="task.finished",
        sender=task.agent_name,
        correlation_id=task.task_id,
        payload={
            "task_id": task.task_id,
            "loop_id": task.loop_id,
            "agent_name": task.agent_name,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
            "started_at": task.started_at,
            "finished_at": task.finished_at,
            "duration_ms": _duration_ms(task),
        },
    )


def task_failed_event(task: Task) -> A2AMessage:
    return A2AMessage(
        topic="task.failed",
        sender=task.agent_name,
        correlation_id=task.task_id,
        payload={
            "task_id": task.task_id,
            "loop_id": task.loop_id,
            "agent_name": task.agent_name,
            "status": task.status.value,
            "error": task.error,
            "retry_count": task.retry_count,
        },
    )


def task_cancelled_event(task: Task) -> A2AMessage:
    return A2AMessage(
        topic="task.cancelled",
        sender="orchestrator",
        correlation_id=task.task_id,
        payload={
            "task_id": task.task_id,
            "loop_id": task.loop_id,
            "agent_name": task.agent_name,
            "status": task.status.value,
        },
    )


def task_retry_event(task: Task) -> A2AMessage:
    return A2AMessage(
        topic="task.retry",
        sender="orchestrator",
        correlation_id=task.task_id,
        payload={
            "task_id": task.task_id,
            "loop_id": task.loop_id,
            "agent_name": task.agent_name,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
        },
    )


def _duration_ms(task: Task) -> float | None:
    if task.started_at and task.finished_at:
        return round((task.finished_at - task.started_at) * 1000, 2)
    return None
