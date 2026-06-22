"""多 Agent 任务调度器。

提供优先级队列、依赖检查、并发度控制、超时/取消、结果聚合。
"""
from __future__ import annotations

import asyncio
import heapq
import logging
import time
from typing import Any

from loop_agent_mcp.core.state import StateManager
from loop_agent_mcp.runtime.a2a_bus import (
    A2ABus,
    task_cancelled_event,
    task_failed_event,
    task_finished_event,
    task_retry_event,
    task_started_event,
    task_submitted_event,
)
from loop_agent_mcp.runtime.executor_wrapper import AgentExecutor
from loop_agent_mcp.runtime.task import Task, TaskStatus, new_task_id
from loop_agent_mcp.runtime.task_store import TaskStore
from loop_agent_mcp.runtime.worker_pool import WorkerPool

logger = logging.getLogger(__name__)


class TaskScheduler:
    """多 agent 任务调度器。"""

    def __init__(
        self,
        max_concurrent: int = 4,
        default_timeout: float = 600.0,
        agent_concurrency_limit: int = 2,
    ) -> None:
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.agent_concurrency_limit = agent_concurrency_limit

        # 优先级队列：heapq，按 (priority, created_at, task_id) 排序
        self._queue: list[tuple[int, float, str]] = []
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._pool = WorkerPool()
        self._bus = A2ABus()
        self._store = TaskStore()

        # 运行中任务统计（按 agent_name）
        self._agent_running: dict[str, set[str]] = {}
        # task_id -> asyncio.Event，用于通知 _execute 提前释放 semaphore
        self._cancel_events: dict[str, asyncio.Event] = {}
        # task_id -> asyncio.Event，任务到达终态时唤醒等待者
        self._terminal_events: dict[str, asyncio.Event] = {}
        # 调度请求句柄，用于合并同一事件循环周期内的多次 dispatch 请求
        self._dispatch_handle: asyncio.Handle | None = None
        self._closed = False

    # ---- 公共 API ----

    async def submit_task(
        self,
        agent_name: str,
        task_input: dict[str, Any],
        *,
        loop_id: str | None = None,
        priority: int = 5,
        dependencies: list[str] | None = None,
        timeout: float | None = None,
        max_retries: int = 2,
    ) -> Task:
        """提交新任务。"""
        if self._closed:
            raise RuntimeError("TaskScheduler 已关闭")

        loop_id = loop_id or StateManager.get().active_loop_id or ""
        task = Task(
            task_id=new_task_id(),
            loop_id=loop_id,
            agent_name=agent_name,
            task_input=task_input,
            priority=max(1, min(10, priority)),
            dependencies=dependencies or [],
            timeout_seconds=timeout or self.default_timeout,
            max_retries=max_retries,
        )
        task.context = AgentExecutor(task).context

        # 持久化在后台执行，避免阻塞提交路径；任务状态以内存为准。
        asyncio.create_task(self._persist(task))
        async with self._lock:
            heapq.heappush(self._queue, (task.priority, task.created_at, task.task_id))
            self._tasks[task.task_id] = task
            task.status = TaskStatus.QUEUED
            task.add_audit("queued")

        await self._bus.publish(task_submitted_event(task))
        self._request_dispatch()
        return task

    async def submit_and_wait(
        self,
        agent_name: str,
        task_input: dict[str, Any],
        *,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Task:
        """提交任务并等待完成（同步兼容模式）。"""
        task = await self.submit_task(
            agent_name=agent_name,
            task_input=task_input,
            timeout=timeout,
            **kwargs,
        )
        await self._wait_until_terminal(task.task_id)
        return task

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务。"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.is_terminal():
                return False
            # 触发取消事件，通知 _execute 提前释放 semaphore
            if task_id not in self._cancel_events:
                self._cancel_events[task_id] = asyncio.Event()
            self._cancel_events[task_id].set()

            # 从队列中移除，避免 _dispatch 重复处理
            self._queue = [
                entry for entry in self._queue if entry[2] != task_id
            ]
            heapq.heapify(self._queue)

            # 非运行态任务直接终态化，由本方法发布取消事件
            if task.status != TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.finished_at = time.time()
                task.add_audit("cancelled")
                await self._persist(task)
                terminal_event = self._terminal_events.pop(task_id, None)
                if terminal_event:
                    terminal_event.set()
                await self._bus.publish(task_cancelled_event(task))
                self._request_dispatch()
                return True

        # 运行中任务由 _execute 感知取消信号并发布事件
        await self._pool.cancel(task_id)
        self._request_dispatch()
        return True

    def get_task(self, task_id: str) -> Task | None:
        """获取任务（从内存）。"""
        return self._tasks.get(task_id)

    async def load_task(self, task_id: str) -> Task | None:
        """获取任务（内存优先，否则从持久化加载）。"""
        task = self._tasks.get(task_id)
        if task is not None:
            return task
        return await asyncio.to_thread(self._store.load, task_id)

    def list_tasks(
        self,
        *,
        loop_id: str | None = None,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """列出任务。"""
        tasks = list(self._tasks.values())
        if loop_id:
            tasks = [t for t in tasks if t.loop_id == loop_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    async def close(self) -> None:
        """关闭调度器。"""
        self._closed = True
        await self._pool.shutdown(wait=True)

    async def _persist(self, task: Task) -> bool:
        """异步持久化任务状态，避免阻塞事件循环。"""
        return await asyncio.to_thread(self._store.save, task)

    # ---- 内部调度 ----

    def _request_dispatch(self) -> None:
        """请求一次调度，合并同一事件循环周期内的多次 dispatch 请求。"""
        if self._dispatch_handle is not None or self._closed:
            return
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return
        self._dispatch_handle = loop.call_soon(self._dispatch_now)

    def _dispatch_now(self) -> None:
        """执行调度（由事件循环回调触发）。"""
        self._dispatch_handle = None
        if not self._closed:
            asyncio.create_task(self._dispatch_coalesced())

    async def _dispatch_coalesced(self) -> None:
        """让出一次事件循环，使同一批 submit_task 全部入队后再统一调度。"""
        await asyncio.sleep(0)
        await self._dispatch()

    async def _dispatch(self) -> None:
        """从队列中循环取出可调度任务并执行，直到无可用槽或无就绪任务。"""
        # 限制本轮处理的任务数，防止全部任务都被阻塞时 busy-loop
        max_rounds = max(1, len(self._queue))
        for _ in range(max_rounds):
            async with self._lock:
                if self._closed or not self._queue:
                    return
                if self._semaphore.locked():
                    return

                _, _, task_id = self._queue[0]
                task = self._tasks.get(task_id)
                if task is None or task.is_terminal():
                    heapq.heappop(self._queue)
                    continue

                # 取出候选任务
                heapq.heappop(self._queue)

                # 检查依赖失败传播
                dep_reason = await self._check_dependency_failure(task)
                if dep_reason:
                    task.status = TaskStatus.FAILED
                    task.error = {"type": "dependency_failed", "message": dep_reason}
                    task.add_audit("failed", reason=dep_reason)
                    await self._persist(task)
                    terminal_event = self._terminal_events.pop(task.task_id, None)
                    if terminal_event:
                        terminal_event.set()
                    await self._bus.publish(task_failed_event(task))
                    self._request_dispatch()
                    continue

                # 检查依赖是否已满足
                if not await self._dependencies_satisfied(task):
                    task.status = TaskStatus.BLOCKED
                    task.add_audit("blocked", reason="dependencies_not_satisfied")
                    await self._persist(task)
                    heapq.heappush(self._queue, (task.priority, time.time(), task.task_id))
                    asyncio.create_task(self._delayed_dispatch(0.1))
                    continue

                # 检查同 agent 并发上限
                if not self._check_agent_concurrency(task):
                    task.status = TaskStatus.BLOCKED
                    task.add_audit("blocked", reason="agent_concurrency_limit")
                    await self._persist(task)
                    heapq.heappush(self._queue, (task.priority, time.time(), task.task_id))
                    asyncio.create_task(self._delayed_dispatch(0.1))
                    continue

                # 占用 agent 运行槽位
                self._agent_running.setdefault(task.agent_name, set()).add(task.task_id)

            # 在锁外获取 semaphore，确保并发槽不被超额占用
            await self._semaphore.acquire()
            asyncio.create_task(self._execute(task))

    async def _execute(self, task: Task) -> None:
        """真正执行一个任务。调用前必须已占用 semaphore。"""
        try:
            async with self._lock:
                if task.is_terminal():
                    return
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                task.add_audit("running")
                self._agent_running.setdefault(task.agent_name, set()).add(task.task_id)
                cancel_event = self._cancel_events.setdefault(task.task_id, asyncio.Event())

            # 先将任务提交到 worker 池，再完成持久化与事件发布，
            # 保证高优先级任务优先占用 worker 线程。
            submit_task = asyncio.create_task(
                self._pool.submit(task, lambda t: AgentExecutor(t).run)
            )
            cancel_wait = asyncio.create_task(cancel_event.wait())

            await self._persist(task)
            await self._bus.publish(task_started_event(task))

            try:

                # 同时等待任务完成、取消信号或超时（超时统一由外层控制）
                done, pending = await asyncio.wait(
                    [submit_task, cancel_wait],
                    timeout=task.timeout_seconds,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for p in pending:
                    p.cancel()
                    try:
                        await p
                    except asyncio.CancelledError:
                        pass

                if cancel_wait in done:
                    # 收到取消信号：立即释放 semaphore，避免占用并发槽
                    task.status = TaskStatus.CANCELLED
                    task.error = {"type": "cancelled", "message": "任务被取消"}
                    task.add_audit("cancelled_by_scheduler")
                    if submit_task and not submit_task.done():
                        submit_task.cancel()
                        try:
                            await submit_task
                        except asyncio.CancelledError:
                            pass
                    await self._pool.cancel(task.task_id)
                elif submit_task in done:
                    result = await submit_task
                    task.result = result
                    if result.get("status") == "error":
                        await self._handle_failure(task, result)
                    else:
                        task.status = TaskStatus.SUCCEEDED
                else:
                    # 超时
                    task.status = TaskStatus.TIMEOUT
                    task.error = {"type": "timeout", "limit": task.timeout_seconds}
                    task.add_audit("timeout")
                    if submit_task and not submit_task.done():
                        submit_task.cancel()
                        try:
                            await submit_task
                        except asyncio.CancelledError:
                            pass
                    await self._pool.cancel(task.task_id)

            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                task.add_audit("cancelled_by_scheduler")
                raise
            except Exception as e:
                logger.exception("调度器执行任务 %s 异常", task.task_id)
                await self._handle_failure(task, {"error": str(e)})
        finally:
            task.finished_at = time.time()
            async with self._lock:
                self._agent_running.get(task.agent_name, set()).discard(task.task_id)
                self._cancel_events.pop(task.task_id, None)

            # 只有到达终态才持久化并发布事件；PENDING 表示已安排重试
            if task.is_terminal():
                await self._persist(task)

                terminal_event = self._terminal_events.pop(task.task_id, None)
                if terminal_event:
                    terminal_event.set()

                if task.status == TaskStatus.SUCCEEDED:
                    await self._bus.publish(task_finished_event(task))
                elif task.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT):
                    await self._bus.publish(task_failed_event(task))
                elif task.status == TaskStatus.CANCELLED:
                    await self._bus.publish(task_cancelled_event(task))

            # 任务结束或重试安排后，触发下一次调度以填充空闲槽位
            self._request_dispatch()
            self._semaphore.release()

    async def _handle_failure(self, task: Task, result: dict[str, Any]) -> None:
        """处理任务失败与重试（退避逻辑在释放 semaphore 后由延迟任务执行）。"""
        task.retry_count += 1
        task.error = {
            "type": "execution_error",
            "message": result.get("error", "unknown error"),
            "retry_count": task.retry_count,
        }
        task.add_audit("failed", error=task.error)

        if task.retry_count <= task.max_retries:
            # 指数退避：先释放状态为 PENDING，再由独立协程在 backoff 后入队
            backoff = min(2 ** task.retry_count, 60)
            task.status = TaskStatus.PENDING
            task.add_audit("retry_scheduled", backoff=backoff)
            await self._persist(task)
            await self._bus.publish(task_retry_event(task))
            asyncio.create_task(self._delayed_retry(task, backoff))
        else:
            task.status = TaskStatus.FAILED

    async def _delayed_retry(self, task: Task, backoff: float) -> None:
        """延迟指定时间后将重试任务重新入队。"""
        await asyncio.sleep(backoff)
        async with self._lock:
            if not task.is_terminal():
                heapq.heappush(self._queue, (task.priority, time.time(), task.task_id))
        self._request_dispatch()

    async def _delayed_dispatch(self, delay: float) -> None:
        """延迟一段时间后触发调度，避免依赖/并发阻塞时忙等。"""
        await asyncio.sleep(delay)
        self._request_dispatch()

    async def _check_dependency_failure(self, task: Task) -> str | None:
        """检查是否有依赖已进入 FAILED/CANCELLED/TIMEOUT 等失败终态。"""
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if dep is None:
                dep = await asyncio.to_thread(self._store.load, dep_id)
            if dep is None:
                continue
            if dep.is_terminal() and dep.status != TaskStatus.SUCCEEDED:
                return f"dependency {dep_id} {dep.status.value}"
        return None

    async def _dependencies_satisfied(self, task: Task) -> bool:
        """检查硬依赖是否已满足。"""
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if dep is None:
                dep = await asyncio.to_thread(self._store.load, dep_id)
            if dep is None:
                # 依赖任务不存在，视为未满足
                return False
            if dep.status != TaskStatus.SUCCEEDED:
                return False
        return True

    def _check_agent_concurrency(self, task: Task) -> bool:
        """检查同一 agent 角色的并发数是否超过限制。"""
        running = self._agent_running.get(task.agent_name, set())
        return len(running) < self.agent_concurrency_limit

    async def _wait_until_terminal(
        self,
        task_id: str,
        poll_interval: float = 0.05,
        timeout: float = 60.0,
    ) -> None:
        """等待任务到达终态，优先通过 asyncio.Event 唤醒，保留轮询兜底。"""
        deadline = time.time() + timeout
        event = self._terminal_events.setdefault(task_id, asyncio.Event())
        while True:
            task = self._tasks.get(task_id)
            if task is None:
                task = await asyncio.to_thread(self._store.load, task_id)
            if task is None or task.is_terminal():
                return
            remaining = deadline - time.time()
            if remaining <= 0:
                return
            try:
                await asyncio.wait_for(event.wait(), timeout=min(poll_interval, remaining))
                # Event 被设置后任务已终态
                return
            except asyncio.TimeoutError:
                continue
