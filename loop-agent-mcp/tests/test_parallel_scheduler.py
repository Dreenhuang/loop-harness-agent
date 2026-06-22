"""并行任务调度器测试。

覆盖：真正并行执行、优先级、依赖、取消、超时、并发写 StateManager、A2A 事件。
"""
from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path

import pytest

from loop_agent_mcp.core.state import StateManager
from loop_agent_mcp.runtime.a2a_bus import A2ABus
from loop_agent_mcp.runtime.scheduler import TaskScheduler
from loop_agent_mcp.runtime.task import TaskStatus
from loop_agent_mcp.tools.dispatcher import async_dispatch, dispatch, get_scheduler, reset_scheduler


@pytest.fixture
async def scheduler(tmp_path: Path):
    """每个测试独立的 TaskScheduler。"""
    StateManager.reset_instance()
    sm = StateManager.get()
    sm.init_persistence(tmp_path)
    sm.mutate(lambda s: setattr(s, "workspace", str(tmp_path)))
    reset_scheduler()
    sch = await get_scheduler()
    # 提升同 agent 并发上限，避免压力测试中 20 个同 agent 任务被默认 limit=2 阻塞
    sch.agent_concurrency_limit = 32
    # 确保持久化 workspace 与 tmp_path 一致
    sch._store = type(sch._store)(tmp_path)
    yield sch
    await sch.close()
    StateManager.reset_instance()


# ---- 1. 真正并行执行 ----


def test_multiple_agents_run_in_parallel(scheduler: TaskScheduler, monkeypatch):
    """多个 agent 同时提交，验证真正并行执行（并发度 > 1）。"""
    concurrent_count = 0
    max_concurrent = 0
    lock = threading.Lock()

    def mock_execute(agent_name: str, task_input: dict):
        nonlocal concurrent_count, max_concurrent
        with lock:
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
        time.sleep(0.3)
        with lock:
            concurrent_count -= 1
        return {"status": "executed", "agent": agent_name, "files_created": []}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        tasks = []
        for i in range(3):
            t = await scheduler.submit_task(
                "backend", {"task_type": "api", "endpoint": f"e{i}"}
            )
            tasks.append(t)

        start = time.time()
        for t in tasks:
            await scheduler._wait_until_terminal(t.task_id)
        duration = time.time() - start

        assert max_concurrent > 1, f"期望并发度 > 1，实际最大并发 {max_concurrent}"
        assert duration < 0.9, f"期望并行执行时间 < 0.9s，实际 {duration:.2f}s"
        for t in tasks:
            assert t.status == TaskStatus.SUCCEEDED

    asyncio.run(run())


# ---- 2. 优先级与依赖 ----


def test_task_priority_and_dependencies(scheduler: TaskScheduler, monkeypatch):
    """高优先级任务先完成；依赖未满足时任务保持 BLOCKED，依赖成功后转为 SUCCEEDED。"""
    execution_order: list[str] = []
    lock = threading.Lock()

    def mock_execute(agent_name: str, task_input: dict):
        time.sleep(0.05)
        with lock:
            execution_order.append(task_input.get("name", agent_name))
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        low = await scheduler.submit_task(
            "backend", {"name": "low"}, priority=9
        )
        high = await scheduler.submit_task(
            "frontend", {"name": "high"}, priority=1
        )

        await scheduler._wait_until_terminal(low.task_id)
        await scheduler._wait_until_terminal(high.task_id)

        assert execution_order[0] == "high", "高优先级任务应先执行"
        assert execution_order[1] == "low"

        # 依赖测试
        dep = await scheduler.submit_task(
            "backend", {"name": "dep"}, priority=5
        )
        dependent = await scheduler.submit_task(
            "frontend", {"name": "dependent"}, priority=5, dependencies=[dep.task_id]
        )

        await scheduler._wait_until_terminal(dependent.task_id)
        assert dep.status == TaskStatus.SUCCEEDED
        assert dependent.status == TaskStatus.SUCCEEDED

    asyncio.run(run())


# ---- 3. 任务取消 ----


def test_task_cancellation(scheduler: TaskScheduler, monkeypatch):
    """提交长时间任务后取消，验证任务状态变为 CANCELLED，只发布 cancelled 事件。"""
    started = threading.Event()

    def mock_execute(agent_name: str, task_input: dict):
        started.set()
        time.sleep(5.0)
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        events: list[str] = []

        def on_event(message):
            events.append(message.topic)

        scheduler._bus.subscribe("task.cancelled", on_event)
        scheduler._bus.subscribe("task.finished", on_event)

        task = await scheduler.submit_task("backend", {"name": "long"})
        while task.status != TaskStatus.RUNNING:
            await asyncio.sleep(0.05)
        started.wait(timeout=2)
        cancelled = await scheduler.cancel_task(task.task_id)

        assert cancelled is True
        await scheduler._wait_until_terminal(task.task_id)

        final_task = scheduler.get_task(task.task_id)
        assert final_task is not None
        assert final_task.status == TaskStatus.CANCELLED
        assert "task.cancelled" in events
        assert "task.finished" not in events, "已取消任务不应发布 task.finished"

    asyncio.run(run())


# ---- 4. 任务超时 ----


def test_task_timeout(scheduler: TaskScheduler, monkeypatch):
    """设置短超时，任务应进入 TIMEOUT 状态。"""
    def mock_execute(agent_name: str, task_input: dict):
        time.sleep(10.0)
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        task = await scheduler.submit_task(
            "backend", {"name": "slow"}, timeout=0.2
        )
        await scheduler._wait_until_terminal(task.task_id)
        assert task.status == TaskStatus.TIMEOUT
        assert task.error is not None
        assert task.error.get("type") == "timeout"

    asyncio.run(run())


# ---- 5. 并发写 StateManager 不冲突 ----


def test_concurrent_state_manager_writes(scheduler: TaskScheduler, monkeypatch):
    """多个任务同时修改 StateManager，验证状态不丢失、不冲突。"""
    def mock_execute(agent_name: str, task_input: dict):
        loop_id = task_input.get("_loop_id", "")
        sm = StateManager.get()
        sm.set_thread_loop(loop_id)
        sm.mutate(lambda s: s.active_tasks.append(task_input.get("_task_id", "")))
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        sm = StateManager.get()
        loop_id = sm.state.loop_id
        task_count = 10
        tasks = []
        for i in range(task_count):
            t = await scheduler.submit_task("backend", {"idx": i})
            tasks.append(t)

        for t in tasks:
            await scheduler._wait_until_terminal(t.task_id)

        sm.set_thread_loop(loop_id)
        active = sm.state.active_tasks
        task_ids = {t.task_id for t in tasks}
        # 至少所有任务都成功写入了自己的 task_id
        assert task_ids.issubset(set(active)), "并发写 StateManager 导致部分 task_id 丢失"

    asyncio.run(run())


# ---- 6. A2A 事件发布 ----


def test_a2a_events_published(scheduler: TaskScheduler, monkeypatch):
    """验证任务生命周期事件通过 A2ABus 正确发布。"""
    def mock_execute(agent_name: str, task_input: dict):
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        events: list[str] = []
        task_ids: list[str] = []

        def on_event(message):
            events.append(message.topic)
            task_ids.append(message.correlation_id)

        for topic in ["task.submitted", "task.started", "task.finished"]:
            scheduler._bus.subscribe(topic, on_event)

        task = await scheduler.submit_task("backend", {"name": "evented"})
        await scheduler._wait_until_terminal(task.task_id)

        assert "task.submitted" in events
        assert "task.started" in events
        assert "task.finished" in events
        assert task.task_id in task_ids

    asyncio.run(run())


# ---- 7. dispatcher async 模式端到端 ----


def test_dispatcher_spawn_agent_async_mode(tmp_path: Path, monkeypatch):
    """通过 dispatcher 以 async=true 提交任务，并通过 get_task_status 查询。"""
    executed = []

    def mock_execute(agent_name: str, task_input: dict):
        time.sleep(0.1)
        executed.append(agent_name)
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        StateManager.reset_instance()
        reset_scheduler()
        await async_dispatch("start_loop", {"workspace": str(tmp_path)})

        res = await async_dispatch(
            "spawn_agent",
            {"agent_name": "backend", "task_input": {"task_type": "api"}, "async": True},
        )
        assert res["status"] == "queued"
        task_id = res["task_id"]

        # 轮询等待完成
        for _ in range(50):
            status = await async_dispatch("get_task_status", {"task_id": task_id})
            if status["task_status"] in ("succeeded", "failed", "timeout", "cancelled"):
                break
            await asyncio.sleep(0.05)

        assert status["task_status"] == "succeeded"
        assert status["result_preview"]["files_count"] == 0

    asyncio.run(run())


# ---- 8. dispatcher 同步兼容模式 ----


def test_dispatcher_spawn_agent_sync_mode(tmp_path: Path, monkeypatch):
    """通过 dispatcher 默认 sync 模式提交任务，验证仍返回完整结果。"""
    def mock_execute(agent_name: str, task_input: dict):
        return {"status": "executed", "agent": agent_name, "output": "done"}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        StateManager.reset_instance()
        reset_scheduler()
        await async_dispatch("start_loop", {"workspace": str(tmp_path)})

        res = await async_dispatch(
            "spawn_agent",
            {"agent_name": "backend", "task_input": {"task_type": "api"}},
        )
        assert res["status"] == "succeeded"
        assert res["task_id"]
        assert res["mode"] == "executed"

    asyncio.run(run())


# ---- 9. 多 agent 角色真正并行 ----


def test_multi_agent_roles_run_concurrently(scheduler: TaskScheduler, monkeypatch):
    """backend 与 frontend 任务同时处于 RUNNING，验证多角色独立并行。"""
    start_times: dict[str, float] = {}
    end_times: dict[str, float] = {}
    lock = threading.Lock()

    def mock_execute(agent_name: str, task_input: dict):
        tid = task_input.get("_task_id", "")
        with lock:
            start_times[tid] = time.time()
        time.sleep(0.4)
        with lock:
            end_times[tid] = time.time()
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        backend_task = await scheduler.submit_task(
            "backend", {"task_type": "api"}, priority=1
        )
        frontend_task = await scheduler.submit_task(
            "frontend", {"task_type": "ui"}, priority=1
        )
        await scheduler._wait_until_terminal(backend_task.task_id)
        await scheduler._wait_until_terminal(frontend_task.task_id)

        assert backend_task.status == TaskStatus.SUCCEEDED
        assert frontend_task.status == TaskStatus.SUCCEEDED

        # 若两角色串行执行，则 backend 结束后 frontend 才开始，started_at 差值应接近 sleep 时长
        # 真正并行时，两者 started_at 几乎相同，且运行时间段存在重叠
        b_start = start_times[backend_task.task_id]
        f_start = start_times[frontend_task.task_id]
        b_end = end_times[backend_task.task_id]
        f_end = end_times[frontend_task.task_id]

        assert abs(b_start - f_start) < 0.3, "backend 与 frontend 未同时启动"
        assert b_start < f_end and f_start < b_end, "backend 与 frontend 运行时间段未重叠"

    asyncio.run(run())


# ---- 10. 任务依赖失败传播 ----


def test_dependency_failure_marks_dependent_task_failed(scheduler: TaskScheduler, monkeypatch):
    """task A 失败后，依赖 A 的 task B 应进入 FAILED，不会错误执行。"""
    executed: list[str] = []
    lock = threading.Lock()

    def mock_execute(agent_name: str, task_input: dict):
        with lock:
            executed.append(task_input.get("name", agent_name))
        if task_input.get("should_fail"):
            return {"status": "error", "error": "intentional failure"}
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        task_a = await scheduler.submit_task(
            "backend", {"name": "a", "should_fail": True}, max_retries=0
        )
        task_b = await scheduler.submit_task(
            "frontend", {"name": "b"}, dependencies=[task_a.task_id]
        )

        await scheduler._wait_until_terminal(task_a.task_id)
        await scheduler._wait_until_terminal(task_b.task_id)

        assert task_a.status == TaskStatus.FAILED
        assert task_b.status == TaskStatus.FAILED
        assert task_b.error is not None
        assert task_b.error.get("type") == "dependency_failed"
        assert "b" not in executed, "依赖失败时 task B 不应执行"

    asyncio.run(run())


# ---- 11. 高并发压力测试 ----


async def test_high_concurrency_stress(scheduler: TaskScheduler, monkeypatch):
    """一次性提交 20 个任务，验证调度器不崩溃、不丢任务、全部成功。

    注意：此测试是 async 的，使用 pytest-asyncio 的事件循环，
    避免 asyncio.run() 在已运行事件循环中或在新循环里使用旧 loop 绑定原语导致的死锁。
    """
    executed_indices: set[int] = set()
    lock = threading.Lock()

    def mock_execute(agent_name: str, task_input: dict):
        idx = task_input.get("idx")
        with lock:
            executed_indices.add(idx)
        time.sleep(0.05)
        return {"status": "executed", "agent": agent_name, "idx": idx}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    tasks = []
    for i in range(20):
        t = await scheduler.submit_task("backend", {"idx": i})
        tasks.append(t)

    for t in tasks:
        await scheduler._wait_until_terminal(t.task_id)

    assert len(tasks) == 20
    assert all(t.status == TaskStatus.SUCCEEDED for t in tasks)
    assert len(executed_indices) == 20, f"丢失任务，仅执行 {len(executed_indices)} 个"
    assert set(range(20)) == executed_indices


# ---- 12. worker 池优雅关闭 ----


def test_worker_pool_graceful_shutdown(tmp_path: Path, monkeypatch):
    """所有任务完成后关闭调度器，验证 shutdown 不挂起、资源正确释放。"""
    def mock_execute(agent_name: str, task_input: dict):
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        StateManager.reset_instance()
        sm = StateManager.get()
        sm.init_persistence(tmp_path)
        sm.mutate(lambda s: setattr(s, "workspace", str(tmp_path)))
        reset_scheduler()
        sch = await get_scheduler()
        sch._store = type(sch._store)(tmp_path)

        tasks = [await sch.submit_task("backend", {"idx": i}) for i in range(4)]
        for t in tasks:
            await sch._wait_until_terminal(t.task_id)

        assert all(t.status == TaskStatus.SUCCEEDED for t in tasks)

        start = time.time()
        await sch.close()
        duration = time.time() - start
        assert duration < 2.0, f"worker 池优雅关闭超时: {duration:.2f}s"
        assert sch._closed is True

    asyncio.run(run())


# ---- 13. A2A 消息事件订阅 ----


def test_a2a_observer_receives_state_change_events(scheduler: TaskScheduler, monkeypatch):
    """observer 订阅后能正确收到任务状态变更事件序列及 payload。"""
    def mock_execute(agent_name: str, task_input: dict):
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        events: list[tuple[str, str, str | None]] = []

        def observer(message):
            events.append((message.topic, message.correlation_id, message.payload.get("status")))

        for topic in ["task.submitted", "task.started", "task.finished"]:
            scheduler._bus.subscribe(topic, observer)

        task = await scheduler.submit_task("backend", {"name": "observed"})
        await scheduler._wait_until_terminal(task.task_id)

        topics = [e[0] for e in events]
        correlation_ids = [e[1] for e in events]

        assert "task.submitted" in topics
        assert "task.started" in topics
        assert "task.finished" in topics
        assert task.task_id in correlation_ids
        # 验证事件顺序
        assert topics.index("task.submitted") < topics.index("task.started")
        assert topics.index("task.started") < topics.index("task.finished")

    asyncio.run(run())


# ---- 14. per-task workspace 隔离 ----


def test_per_task_workspace_isolation(scheduler: TaskScheduler, monkeypatch):
    """两个 agent 在各自 workspace 写入同名文件，验证内容互不覆盖。"""
    def mock_execute(agent_name: str, task_input: dict):
        workspace = task_input.get("_workspace", "")
        file_path = Path(workspace) / "output" / "data.txt"
        file_path.write_text(f"content from {agent_name}", encoding="utf-8")
        return {"status": "executed", "agent": agent_name, "files_created": [str(file_path)]}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        backend_task = await scheduler.submit_task("backend", {"role": "backend"})
        frontend_task = await scheduler.submit_task("frontend", {"role": "frontend"})

        await scheduler._wait_until_terminal(backend_task.task_id)
        await scheduler._wait_until_terminal(frontend_task.task_id)

        assert backend_task.status == TaskStatus.SUCCEEDED
        assert frontend_task.status == TaskStatus.SUCCEEDED

        for task in (backend_task, frontend_task):
            file_path = task.context.workspace / "output" / "data.txt"
            assert file_path.exists(), f"{task.agent_name} 的 workspace 文件不存在"
            content = file_path.read_text(encoding="utf-8")
            assert content == f"content from {task.agent_name}", (
                f"{task.agent_name} 文件内容被覆盖: {content}"
            )

    asyncio.run(run())


# ---- 15. 取消任务后资源释放 ----


def test_cancel_task_releases_resources(scheduler: TaskScheduler, monkeypatch):
    """取消长时间任务后，验证 semaphore 槽位与 worker future 被释放。"""
    started = threading.Event()

    def mock_execute(agent_name: str, task_input: dict):
        started.set()
        time.sleep(10.0)
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        task = await scheduler.submit_task("backend", {"name": "long_running"})
        # 等待任务进入 RUNNING 状态
        while task.status != TaskStatus.RUNNING:
            await asyncio.sleep(0.05)
        started.wait(timeout=2)

        cancelled = await scheduler.cancel_task(task.task_id)
        assert cancelled is True
        await scheduler._wait_until_terminal(task.task_id)

        final_task = scheduler.get_task(task.task_id)
        assert final_task is not None
        assert final_task.status == TaskStatus.CANCELLED

        # 给调度器一点时间完成 finally 块
        for _ in range(50):
            if scheduler._semaphore._value == scheduler.max_concurrent:
                break
            await asyncio.sleep(0.05)

        # 验证资源释放：semaphore 恢复满额、worker future 已清理
        assert scheduler._semaphore._value == scheduler.max_concurrent, (
            f"semaphore 未释放，当前可用槽位: {scheduler._semaphore._value}"
        )
        assert scheduler._pool.running_count() == 0, "worker future 未清理"
        assert task.task_id not in scheduler._pool._running_futures

    asyncio.run(run())


# ---- 16. 超时任务状态为 TIMEOUT 而非 SUCCEEDED ----


def test_timeout_task_state_is_timeout_not_succeeded(scheduler: TaskScheduler, monkeypatch):
    """短超时任务应进入 TIMEOUT，且不会被错误标记为 SUCCEEDED。"""
    def mock_execute(agent_name: str, task_input: dict):
        time.sleep(10.0)
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        task = await scheduler.submit_task(
            "backend", {"name": "slow"}, timeout=0.15
        )
        await scheduler._wait_until_terminal(task.task_id)

        assert task.status == TaskStatus.TIMEOUT
        assert task.status != TaskStatus.SUCCEEDED
        assert task.error is not None
        assert task.error.get("type") == "timeout"

    asyncio.run(run())


# ---- 17. 重试退避不阻塞 semaphore ----


async def test_retry_backoff_does_not_block_semaphore(tmp_path: Path, monkeypatch):
    """任务重试退避期间，semaphore 应被释放，其他任务可继续执行。

    注意：此测试是 async 的，使用 pytest-asyncio 的事件循环，
    避免 asyncio.run() 在新循环里使用旧 loop 绑定原语导致的死锁。
    """
    executed: list[str] = []
    lock = threading.Lock()

    def mock_execute(agent_name: str, task_input: dict):
        name = task_input.get("name", "")
        with lock:
            executed.append(name)
        if name == "failing":
            return {"status": "error", "error": "intentional failure"}
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    StateManager.reset_instance()
    sm = StateManager.get()
    sm.init_persistence(tmp_path)
    sm.mutate(lambda s: setattr(s, "workspace", str(tmp_path)))

    sch = TaskScheduler(max_concurrent=1)
    sch._store = type(sch._store)(tmp_path)

    failing = await sch.submit_task(
        "backend", {"name": "failing"}, max_retries=1
    )
    # 等待 failing 任务进入运行，确保它先占用 semaphore
    while failing.status != TaskStatus.RUNNING:
        await asyncio.sleep(0.05)

    other = await sch.submit_task(
        "backend", {"name": "other"}, priority=1
    )

    # other 应在失败任务首次执行结束、释放 semaphore 后立即运行，
    # 而不是等到 2 秒退避结束后
    start = time.time()
    await sch._wait_until_terminal(other.task_id)
    duration = time.time() - start

    assert other.status == TaskStatus.SUCCEEDED
    assert duration < 1.0, f"重试退避阻塞了 semaphore，other 等待 {duration:.2f}s"
    assert "other" in executed

    await sch.close()
    StateManager.reset_instance()


# ---- 18. dispatch() 在运行事件循环中不抛异常 ----


def test_dispatch_in_running_event_loop():
    """dispatch() 在已运行的事件循环中被调用时应返回明确错误，不抛异常。"""
    async def inner():
        return dispatch("list_agents", {})

    result = asyncio.run(inner())
    assert result.get("status") == "error"
    assert result.get("error_code") == "ASYNC_CONTEXT_ERROR"
    assert "async_dispatch" in result.get("error", "")


# ---- 19. A2ABus.publish_sync 线程安全 ----


def test_a2a_publish_sync_thread_safe():
    """多个线程并发调用 publish_sync，history 数量应正确且无异常。"""
    bus = A2ABus()
    received = []
    bus.subscribe("test.topic", lambda msg: received.append(msg.topic))

    def publish():
        from loop_agent_mcp.runtime.a2a_bus import A2AMessage
        for _ in range(50):
            bus.publish_sync(A2AMessage(topic="test.topic", sender="tester"))

    threads = [threading.Thread(target=publish) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(received) == 200
    assert len(bus.get_history(topic="test.topic", limit=200)) == 200


# ---- 20. 依赖失败后下游任务进入 FAILED ----


def test_dependency_failure_downstream_failed_explicitly(scheduler: TaskScheduler, monkeypatch):
    """显式验证依赖失败后下游任务被标记为 FAILED。"""
    def mock_execute(agent_name: str, task_input: dict):
        if task_input.get("fail"):
            return {"status": "error", "error": "boom"}
        return {"status": "executed", "agent": agent_name}

    monkeypatch.setattr(
        "loop_agent_mcp.runtime.executor_wrapper.execute_agent", mock_execute
    )

    async def run():
        dep = await scheduler.submit_task(
            "backend", {"fail": True}, max_retries=0
        )
        down = await scheduler.submit_task(
            "frontend", {"name": "down"}, dependencies=[dep.task_id]
        )

        await scheduler._wait_until_terminal(dep.task_id)
        await scheduler._wait_until_terminal(down.task_id)

        assert dep.status == TaskStatus.FAILED
        assert down.status == TaskStatus.FAILED
        assert down.error is not None
        assert down.error.get("type") == "dependency_failed"

    asyncio.run(run())
