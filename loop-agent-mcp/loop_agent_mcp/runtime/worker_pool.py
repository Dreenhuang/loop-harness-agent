"""Worker 池：管理任务执行线程/进程/子进程。

默认基于守护线程池，兼容现有同步 execute_agent；
预留 process / subprocess 扩展点。
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
import queue
import threading
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable

from loop_agent_mcp.runtime.task import Task

logger = logging.getLogger(__name__)


class _DaemonThreadPool:
    """基于守护线程的轻量级线程池。

    与标准 ThreadPoolExecutor 相比，所有工作线程均为 daemon 线程，
    不会阻塞解释器退出；同时支持对单个任务 future 的取消/超时，
    避免在测试或超时场景下因同步阻塞任务导致整个进程挂起。
    """

    def __init__(self, max_workers: int, thread_name_prefix: str = "loop-agent-worker-") -> None:
        self.max_workers = max_workers
        self._thread_name_prefix = thread_name_prefix
        self._work_queue: queue.Queue[Callable[[], None] | None] = queue.Queue()
        self._threads: set[threading.Thread] = set()
        self._lock = threading.Lock()
        self._shutdown = False
        self._counter = 0

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> concurrent.futures.Future:
        """提交一个可调用对象到线程池，返回 Future。"""
        if self._shutdown:
            future: concurrent.futures.Future = concurrent.futures.Future()
            future.set_exception(RuntimeError("WorkerPool 已关闭"))
            return future

        future = concurrent.futures.Future()

        def wrapper() -> None:
            if future.cancelled():
                return
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                if not future.cancelled():
                    future.set_exception(exc)
                return
            if not future.cancelled():
                future.set_result(result)

        self._work_queue.put(wrapper)
        self._ensure_workers()
        return future

    def _ensure_workers(self) -> None:
        """按需创建守护工作线程。"""
        with self._lock:
            alive = {t for t in self._threads if t.is_alive()}
            self._threads = alive
            while len(self._threads) < self.max_workers:
                self._counter += 1
                t = threading.Thread(
                    target=self._worker_loop,
                    name=f"{self._thread_name_prefix}{self._counter}",
                    daemon=True,
                )
                t.start()
                self._threads.add(t)

    def _worker_loop(self) -> None:
        """工作线程主循环。"""
        while True:
            try:
                work = self._work_queue.get(timeout=1.0)
            except queue.Empty:
                with self._lock:
                    if self._shutdown:
                        break
                continue
            if work is None:
                break
            try:
                work()
            except Exception:
                logger.exception("工作线程执行任务异常")

    def shutdown(self, wait: bool = True) -> None:
        """关闭线程池。"""
        self._shutdown = True
        with self._lock:
            threads = list(self._threads)
        for _ in threads:
            self._work_queue.put(None)
        if wait:
            for t in threads:
                t.join(timeout=5.0)


class WorkerPool:
    """基于守护线程池的 worker 池。"""

    def __init__(
        self,
        max_workers: int | None = None,
        process_workers: int = 2,
    ) -> None:
        self.max_workers = max_workers or min(16, (os.cpu_count() or 1) * 4)
        self._thread_pool = _DaemonThreadPool(self.max_workers)
        self._process_pool: ProcessPoolExecutor | None = None
        self._process_workers = process_workers

        # task_id -> concurrent.futures.Future
        self._running_futures: dict[str, concurrent.futures.Future] = {}
        self._lock = threading.Lock()
        self._shutdown = False

    async def submit(
        self,
        task: Task,
        executor_factory: Callable[[Task], Callable[..., dict[str, Any]]],
    ) -> dict[str, Any]:
        """提交任务到 worker 池并返回结果。

        Args:
            task: 要执行的任务。
            executor_factory: 接收 Task，返回可调用执行器的工厂函数。
                典型用法：lambda t: AgentExecutor(t).run

        Returns:
            执行结果字典。
        """
        if self._shutdown:
            return {
                "status": "error",
                "error": "WorkerPool 已关闭",
            }

        execution_mode = task.task_input.get("execution_mode", "thread")

        if execution_mode == "subprocess":
            return await self._run_in_subprocess(task)
        if execution_mode == "process":
            return await self._run_in_process(task, executor_factory)

        return await self._run_in_thread(task, executor_factory)

    async def cancel(self, task_id: str) -> bool:
        """取消正在运行的任务。"""
        with self._lock:
            future = self._running_futures.get(task_id)
            if future is None or future.done():
                return False
            return future.cancel()

    async def shutdown(self, wait: bool = True) -> None:
        """关闭 worker 池。"""
        self._shutdown = True
        self._thread_pool.shutdown(wait=wait)
        if self._process_pool is not None:
            self._process_pool.shutdown(wait=wait, cancel_futures=not wait)

    async def _run_in_thread(
        self,
        task: Task,
        executor_factory: Callable[[Task], Callable[..., dict[str, Any]]],
    ) -> dict[str, Any]:
        executor_callable = executor_factory(task)

        with self._lock:
            if self._shutdown:
                return {"status": "error", "error": "WorkerPool 已关闭"}
            future = self._thread_pool.submit(executor_callable, task)
            self._running_futures[task.task_id] = future

        wrapped = asyncio.wrap_future(future)
        try:
            result = await wrapped
            return result if isinstance(result, dict) else {"status": "ok", "result": result}
        except asyncio.CancelledError:
            future.cancel()
            raise
        except Exception as e:
            logger.exception("任务 %s 在线程池中执行失败", task.task_id)
            return {
                "status": "error",
                "error": str(e),
                "execution_failed": True,
                "task_id": task.task_id,
            }
        finally:
            with self._lock:
                self._running_futures.pop(task.task_id, None)

    async def _run_in_process(
        self,
        task: Task,
        executor_factory: Callable[[Task], Callable[..., dict[str, Any]]],
    ) -> dict[str, Any]:
        """进程池执行（预留扩展点，当前序列化限制下可能无法传递复杂对象）。"""
        if self._process_pool is None:
            self._process_pool = ProcessPoolExecutor(max_workers=self._process_workers)

        loop = asyncio.get_event_loop()
        executor_callable = executor_factory(task)

        try:
            result = await loop.run_in_executor(self._process_pool, executor_callable, task)
            return result if isinstance(result, dict) else {"status": "ok", "result": result}
        except Exception as e:
            logger.exception("任务 %s 在进程池中执行失败", task.task_id)
            return {
                "status": "error",
                "error": str(e),
                "execution_failed": True,
            }

    async def _run_in_subprocess(self, task: Task) -> dict[str, Any]:
        """外部子进程执行（预留扩展点）。"""
        logger.warning("subprocess 执行模式尚未实现，回退到线程模式: %s", task.task_id)
        return {
            "status": "error",
            "error": "subprocess 模式尚未实现",
            "task_id": task.task_id,
        }

    def running_count(self) -> int:
        """当前运行中的任务数。"""
        with self._lock:
            return sum(1 for f in self._running_futures.values() if not f.done())
