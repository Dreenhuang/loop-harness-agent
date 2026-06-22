# 并行 Agent 调度实现说明

## 1. 实现目标

为 Loop-Harness-Agent MCP Server 提供真正独立并行的多 agent 任务调度能力：

- 多个 agent 任务可同时运行，互不阻塞。
- 任务支持优先级、依赖、取消、超时与重试。
- 每个任务拥有独立工作区，避免文件冲突。
- 任务生命周期事件通过 A2A 消息总线发布。
- 任务状态持久化到 JSONL，支持崩溃恢复。
- 与现有 `execute_agent` 执行器保持兼容， Frontend / MCP 工具层改动最小。

## 2. 新增模块

所有新模块位于 `loop_agent_mcp/runtime/` 包下。

| 文件 | 职责 |
|------|------|
| `runtime/__init__.py` | 导出运行时公共接口。 |
| `runtime/task.py` | `TaskStatus` 枚举、`Task` 数据类、`TaskContext` 隔离上下文。 |
| `runtime/task_store.py` | 任务级 JSONL 持久化，支持按 task_id / loop_id 查询与恢复。 |
| `runtime/a2a_bus.py` | 内存级 A2A 消息总线及任务生命周期事件工厂。 |
| `runtime/worker_pool.py` | 基于守护线程的 worker 池，支持超时、取消与 thread/process/subprocess 扩展。 |
| `runtime/executor_wrapper.py` | `AgentExecutor` 包装现有 `execute_agent`，注入任务隔离与线程局部 Loop 上下文。 |
| `runtime/scheduler.py` | `TaskScheduler`：优先级队列、依赖检查、并发控制、超时/取消/重试。 |

## 3. 改造模块

| 文件 | 改造点 |
|------|--------|
| `core/state.py` | 新增线程局部 `loop_id`（`set_thread_loop` / `get_thread_loop`），修复 `snapshot()` 同线程死锁。 |
| `tools/dispatcher.py` | `spawn_agent` 支持 `async=true/false` 双模式；新增 `cancel_task`、`get_task_status` 工具。 |
| `tools/schemas.py` | 扩展工具 schema，增加新工具与任务相关字段。 |
| `engines/orchestrator.py` | `spawn_agent` 仅负责状态更新，实际执行交由 `TaskScheduler`。 |
| `server.py` | 工具调用改为异步分发，支持并发任务处理。 |

## 4. 核心类用法

### 4.1 TaskScheduler

```python
from loop_agent_mcp.runtime.scheduler import TaskScheduler
from loop_agent_mcp.runtime.task import TaskStatus

scheduler = TaskScheduler(max_concurrent=4, default_timeout=600.0)

# 异步提交（立即返回任务对象）
task = await scheduler.submit_task(
    agent_name="backend",
    task_input={"phase": 5, "task_type": "api"},
    priority=3,
    dependencies=[dep_task_id],  # 依赖任务须先成功
    timeout=60.0,
)

# 同步兼容：提交并等待完成
task = await scheduler.submit_and_wait(
    agent_name="frontend",
    task_input={"phase": 5},
)

# 取消任务
cancelled = await scheduler.cancel_task(task.task_id)

# 查询任务
task = scheduler.get_task(task.task_id)
assert task.status == TaskStatus.SUCCEEDED

# 关闭调度器
await scheduler.close()
```

### 4.2 A2ABus 事件订阅

```python
from loop_agent_mcp.runtime.a2a_bus import A2ABus

bus = A2ABus()

def on_task_finished(message):
    print(message.topic, message.payload["task_id"])

bus.subscribe("task.finished", on_task_finished)
```

### 4.3 TaskStore 崩溃恢复

```python
from loop_agent_mcp.runtime.task_store import TaskStore

store = TaskStore(workspace="/path/to/workspace")
store.save(task)
recovered = store.recover_latest(loop_id="loop-xxx", only_incomplete=True)
```

## 5. 测试运行结果

执行命令：

```bash
$env:PYTHONPATH="D:\DevCache\site-packages"
python -m pytest tests/ --tb=short -q
```

结果：

```text
46 passed, 30 warnings in 11.89s
```

- `tests/test_engines.py`：38 个原有测试全部通过。
- `tests/test_parallel_scheduler.py`：8 个新增并发测试全部通过，覆盖：
  - 多 agent 真正并行执行
  - 优先级与依赖
  - 任务取消与事件发布
  - 任务超时
  - 并发写 StateManager 不冲突
  - A2A 事件发布
  - dispatcher async / sync 双模式端到端

Lint 检查：项目未配置 `ruff`，已尝试安装但当前环境无法获得可用二进制，故跳过；代码已通过 Python 3.14 语法与运行时测试。

## 6. 关键设计决策

1. **守护线程池**：使用自定义 `_DaemonThreadPool` 替代 `ThreadPoolExecutor`，工作线程为 daemon，避免同步阻塞任务在超时/取消后继续占用解释器退出。
2. **直接包装 concurrent Future**：`WorkerPool._run_in_thread` 使用 `asyncio.wrap_future` 等待底层 Future，不再占用 asyncio 默认 executor 线程，解决超时场景下 `asyncio.run` 关闭挂起的问题。
3. **同步持久化**：`TaskStore.save/load` 为同步方法，由调用方在异步方法中直接调用（不加 `await`），避免无意义的协程包装；JSONL 追加写保证崩溃后可恢复。
4. **线程局部 Loop 上下文**：`StateManager.set_thread_loop` 让每个执行线程独立切换 Loop，避免并行任务同时修改全局活跃 Loop 产生冲突。
5. **最小侵入**：`AgentExecutor.run` 仍调用原有 `execute_agent`，仅注入 `_task_id`、`_workspace` 等字段与任务级日志。

## 7. 已知限制

- `process` / `subprocess` 执行模式为预留扩展点，当前未完整实现；生产高隔离场景建议后续补齐。
- 任务取消依赖底层执行函数可被 Python Future 取消机制中断；若执行函数内部是长时间 C 扩展阻塞调用（如某些 IO），取消可能无法立即生效，但任务状态会正确标记为 `CANCELLED`/`TIMEOUT`。
- `TaskStore.compact` 目前非自动调用，长期运行后 JSONL 文件会增长，建议按策略（如每完成 100 个任务）调用压缩。
- 当前 `ruff` 未纳入项目依赖，后续建议在 `pyproject.toml` 的 `dev` 依赖中加入 `ruff` 并配置规则。

## 8. 主要文件清单

- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\__init__.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\task.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\task_store.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\a2a_bus.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\worker_pool.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\executor_wrapper.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\scheduler.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\core\state.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\tools\dispatcher.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\tools\schemas.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\engines\orchestrator.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\server.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\tests\test_parallel_scheduler.py`
- `g:\ai-gongju\Loop-agent\loop-agent-mcp\docs\IMPLEMENTATION_NOTES_PARALLEL.md`
