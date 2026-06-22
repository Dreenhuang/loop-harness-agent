# Loop-Harness-Agent MCP 并行调度引擎测试报告

**报告日期**: 2026-06-20  
**测试角色**: @全栈测试员  
**测试范围**: `loop_agent_mcp/runtime/` 并行调度引擎 + `tests/test_parallel_scheduler.py`  
**被测版本**: loop-agent-mcp v1.4+  

---

## 1. 测试目标

验证 Backend 新增的并行调度引擎是否满足架构设计目标：

1. 真正独立并行：多个 agent 任务可同时运行，互不阻塞。
2. 任务支持优先级、依赖、取消、超时与重试。
3. 每个任务拥有独立工作区，避免文件冲突。
4. 任务生命周期事件通过 A2A 消息总线正确发布。
5. Worker 池支持优雅关闭，不挂起、不泄漏资源。
6. 高并发场景下调度器稳定、不丢任务。

---

## 2. 测试环境

| 项目 | 值 |
|------|-----|
| 操作系统 | Windows Server (Tencent Cloud) |
| Python 版本 | 3.14.4 |
| pytest 版本 | 7.x+ |
| 工作目录 | `g:\ai-gongju\Loop-agent\loop-agent-mcp` |
| 运行命令 | `python -m pytest tests/ --tb=short -q` |

---

## 3. 测试覆盖的功能点

本次在保留原有 8 个测试的基础上，新增 7 个测试，覆盖以下关键场景：

| 场景 | 测试函数 | 覆盖说明 |
|------|----------|----------|
| 多 agent 角色真正并行 | `test_multi_agent_roles_run_concurrently` | backend 与 frontend 同时处于 RUNNING，验证运行时间段重叠 |
| 任务依赖失败传播 | `test_dependency_failure_blocks_dependent_task` | task A 失败时，依赖 A 的 task B 被阻塞（BLOCKED），不会误执行 |
| 高并发压力测试 | `test_high_concurrency_stress` | 一次性提交 20 个任务，验证不崩溃、不丢任务、全部成功 |
| Worker 池优雅关闭 | `test_worker_pool_graceful_shutdown` | 所有任务完成后 `scheduler.close()` 不挂起 |
| A2A 消息事件订阅 | `test_a2a_observer_receives_state_change_events` | observer 收到 `task.submitted` / `task.started` / `task.finished` 序列及 payload |
| per-task workspace 隔离 | `test_per_task_workspace_isolation` | 两个 agent 写入同名 `output/data.txt`，内容互不覆盖 |
| 取消任务后资源释放 | `test_cancel_task_releases_resources` | 取消后 semaphore 槽位与 worker future 被释放 |
| 原有测试 | `test_multiple_agents_run_in_parallel` 等 8 个 | 并发度、优先级、依赖成功、取消、超时、StateManager 并发写、A2A 事件、dispatcher async/sync 双模式 |

---

## 4. 测试结果

### 4.1 全量测试结果

```text
$ python -m pytest tests/ --tb=short -q
.....................................................                                       [100%]
53 passed, 30 warnings in 18.84s
```

- **通过数**: 53 / 53（100%）
- **失败数**: 0
- **警告**: 30 条，均为 `datetime.utcnow()` 弃用警告，位于 `loop_agent_mcp/core/logging.py:111`，不影响功能。

### 4.2 并行调度专项测试结果

```text
$ python -m pytest tests/test_parallel_scheduler.py --tb=short -q
...............                                                                             [100%]
15 passed, 7 warnings in 18.30s
```

---

## 5. 发现的缺陷与修复

### 5.1 缺陷：任务取消后 semaphore 未立即释放（已修复）

**严重程度**: 高（阻塞性 bug）  
**影响**: 取消长时间运行的任务后，并发槽位被持续占用，后续任务无法调度，可能导致 worker 池耗尽。  
**根因**: 原 `_execute` 直接使用 `asyncio.wait_for(self._pool.submit(...))` 等待任务完成。由于底层 `execute_agent` 在线程池中同步运行，Python `concurrent.futures.Future.cancel()` 无法中断已开始执行的线程；`cancel_task` 仅标记任务状态为 `CANCELLED`，但 `_execute` 仍持有 `async with self._semaphore:` 块直至线程函数返回，导致 semaphore 无法释放。  
**修复方案**: 在 `TaskScheduler` 中引入 `self._cancel_events: dict[str, asyncio.Event]`。

- `cancel_task()` 被调用时触发对应 task_id 的 `asyncio.Event.set()`。
- `_execute()` 将 `self._pool.submit(...)` 包装为 `asyncio.Task`，并同时等待：
  - 任务执行完成；
  - 取消信号；
  - 超时。
- 一旦收到取消信号，立即标记任务为 `CANCELLED`，取消底层 submit task，并退出 `async with self._semaphore:`，释放并发槽位。

**修复文件**:

- [loop_agent_mcp/runtime/scheduler.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py)
  - 新增 `self._cancel_events`（第 56 行）
  - 修改 `cancel_task()`（第 124-127 行）
  - 修改 `_execute()`（第 224-275 行）

**修复验证**: `test_cancel_task_releases_resources` 通过，取消后 `semaphore._value` 恢复为 `max_concurrent`，`worker_pool.running_count() == 0`。

---

## 6. 已知限制

1. **线程级任务无法被硬中断**：
   - 取消信号能让调度器立即释放 semaphore 并标记任务为 `CANCELLED`，但底层 worker 线程中的同步 `execute_agent` 仍会继续运行直到自然结束。
   - 建议：未来对长时间运行的执行函数引入协作式取消检查点（如在 `AgentExecutor.run` 中轮询取消标志）。

2. **`process` / `subprocess` 执行模式为预留扩展点**：
   - 当前未完整实现，生产环境需要更强隔离时建议后续补齐。

3. **`TaskStore.compact` 非自动调用**：
   - 长期运行后 JSONL 文件会增长，建议按策略（如每完成 100 个任务）调用压缩。

4. **依赖失败时下游任务保持 BLOCKED 而非 FAILED**：
   - 当前实现符合架构文档（硬依赖失败则下游进入 `BLOCKED`），但用户描述中期望"跳过/失败"。
   - 如需更激进的失败传播策略，可在 `_dependencies_satisfied` 中检测依赖是否 `FAILED`，并直接置下游为 `FAILED`。

5. **弃用警告**：
   - `datetime.utcnow()` 在 `loop_agent_mcp/core/logging.py:111` 产生弃用警告，建议替换为 `datetime.now(datetime.UTC)`。

---

## 7. 测试工件

| 工件 | 路径 |
|------|------|
| 测试源码 | [g:\ai-gongju\Loop-agent\loop-agent-mcp\tests\test_parallel_scheduler.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/tests/test_parallel_scheduler.py) |
| 调度器实现 | [g:\ai-gongju\Loop-agent\loop-agent-mcp\loop_agent_mcp\runtime\scheduler.py](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py) |
| 架构文档 | [g:\ai-gongju\Loop-agent\loop-agent-mcp\docs\architecture\parallel-agent-scheduling-architecture.md](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/docs/architecture/parallel-agent-scheduling-architecture.md) |
| 实现说明 | [g:\ai-gongju\Loop-agent\loop-agent-mcp\docs\IMPLEMENTATION_NOTES_PARALLEL.md](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/docs/IMPLEMENTATION_NOTES_PARALLEL.md) |
| 本报告 | [g:\ai-gongju\Loop-agent\loop-agent-mcp\docs\TEST_REPORT_PARALLEL.md](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/docs/TEST_REPORT_PARALLEL.md) |

---

## 8. 结论

本次测试对 `loop-agent-mcp` 并行调度引擎进行了系统性审查与增强：

- 原有 8 个测试全部保留并通过。
- 新增 7 个测试，覆盖多角色并行、依赖失败、高并发压力、优雅关闭、A2A observer、workspace 隔离、取消资源释放等关键场景。
- 发现并修复了 1 个阻塞性 bug：任务取消后 semaphore 未释放。
- 全量测试 53/53 通过，无失败。

**质量结论**: 并行调度引擎在当前测试覆盖范围内功能正确、并发行为符合架构设计，可进入下一阶段。建议后续补齐 process/subprocess 隔离、协作式取消检查点、TaskStore 自动压缩等增强点。
