# Loop-Harness-Agent MCP 并行调度代码审查报告

**审查范围**: `loop_agent_mcp/runtime/` 新增包 + `core/state.py`、`tools/dispatcher.py`、`tools/schemas.py`、`engines/orchestrator.py`、`server.py` 的并行调度相关改动  
**审查时间**: 2026-06-20  
**审查角色**: @Code-Reviewer  
**测试基线**: 53 passed, 30 warnings in 18.65s  
**被测版本**: loop-agent-mcp v1.4+  

---

## 1. 总体结论

本次并行调度实现整体架构清晰，引入了 `TaskScheduler`、`WorkerPool`、`TaskStore`、`A2ABus`、`AgentExecutor`、`TaskContext` 等职责明确的组件，成功将 `spawn_agent` 从同步串行改造为可并发执行，并通过 `async/sync` 双模式保持向后兼容。测试覆盖了并行性、依赖、取消、超时、workspace 隔离、A2A 事件等核心场景。

但代码中存在 **3 项 Critical 级别问题** 与若干 Major/Minor 缺陷，主要集中在：

1. `WorkerPool` 与 `TaskScheduler` 双重超时控制导致超时任务可能被错误标记为 `SUCCEEDED`；
2. 失败重试退避发生在 `semaphore` 保护区内，会阻塞并发槽位；
3. 同步兼容入口 `dispatch()` 在已运行的事件循环中调用会失败，存在向后兼容风险；
4. 事件总线历史记录、任务持久化等模块存在并发安全与性能隐患；
5. 部分测试用例未能真正验证其声称的并发隔离语义。

**门禁结论**: **不通过，需修复 Critical 与 Major 问题后重新审查。**

**总体评分**: **6.8 / 10**

---

## 2. 问题清单

### 2.1 Critical（必须修复，存在生产级故障风险）

#### CR-1: `WorkerPool` 与 `TaskScheduler` 双重超时控制竞态，可能导致超时任务被错误标记为 `SUCCEEDED`

- **问题描述**: `WorkerPool._run_in_thread` 内部使用 `asyncio.wait_for(wrapped, timeout=task.timeout_seconds)` 自行处理超时，而 `TaskScheduler._execute` 外层又通过 `asyncio.wait([submit_task, cancel_wait], timeout=task.timeout_seconds)` 控制超时。当内部超时先于外层触发时，`_run_in_thread` 返回 `{"status": "timeout", ...}`，外层 `submit_task` 完成，`TaskScheduler._execute` 进入 `submit_task in done` 分支，将结果视为非 error 并设置 `task.status = TaskStatus.SUCCEEDED`。
- **代码位置**:
  - [worker_pool.py#L184-L191](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/worker_pool.py#L184-L191)
  - [scheduler.py#L226-L263](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L226-L263)
- **为什么是个问题**: 超时任务被标记为成功属于状态机严重错误，会导致 orchestrator 基于错误状态推进 Phase，掩盖真实失败，破坏融合验收的“生产级交付”与“流程收敛”目标。
- **修复建议**: 移除 `WorkerPool._run_in_thread` 内部的超时逻辑，仅负责在线程池中运行 callable 并返回结果/异常；所有超时、取消、状态转移统一由 `TaskScheduler._execute` 控制。`WorkerPool` 返回的结果中不再包含 `"status": "timeout"`。

#### CR-2: 任务失败重试退避发生在 `semaphore` 保护区内，阻塞并发槽位

- **问题描述**: `_handle_failure` 在 `async with self._semaphore:` 代码块内被调用，且重试路径包含 `await asyncio.sleep(backoff)`（最长 60 秒）。在退避期间，`semaphore` 槽位持续被占用，同 Loop 其他任务无法获得执行机会。
- **代码位置**:
  - [scheduler.py#L208-L325](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L208-L325)
  - 具体见 `_handle_failure` 中的 `await asyncio.sleep(backoff)` 在 `_execute` 的 `async with self._semaphore:` 作用域内。
- **为什么是个问题**: 高并发或失败率较高的场景下，退避会迅速耗尽并发槽，造成 worker 池假性耗尽，后续任务饿死，严重违反调度器“并发度控制”的设计目标。
- **修复建议**: 将重试退避逻辑移出 `semaphore` 保护区：在 `_handle_failure` 中仅更新任务状态为 `PENDING` 并将任务重新入队，由独立的延迟调度任务在 backoff 时间后再触发 `_dispatch()`；或者调整 `_execute` 结构，在释放 semaphore 后再调用 `_handle_failure`。

#### CR-3: 同步兼容入口 `dispatch()` 在已运行的事件循环中调用会失败

- **问题描述**: `dispatch()` 使用 `asyncio.run(coro)` 执行异步逻辑。当调用方已经处于运行中的事件循环时（如某些测试框架、Jupyter、asyncio 服务内部），`asyncio.run` 会抛出 `RuntimeError`。虽然捕获了该异常并尝试 `loop.run_until_complete`，但如果 `loop.is_running()` 则直接返回错误。
- **代码位置**:
  - [tools/dispatcher.py#L97-L119](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/tools/dispatcher.py#L97-L119)
- **为什么是个问题**: `spawn_agent` 的同步兼容入口在异步上下文中不可用，破坏了向后兼容性。旧客户端或在现有 asyncio 服务中集成的调用方可能因此失败。
- **修复建议**: 明确 `dispatch()` 的同步兼容定位，仅在无非运行事件循环时才能使用；在运行中事件循环场景下，应返回清晰的错误信息并建议调用方使用 `async_dispatch()`。同时补充文档与测试覆盖该场景。若需更强兼容，可考虑使用 `asyncio.run_coroutine_threadsafe` 或要求调用方显式提供 loop。

---

### 2.2 Major（重要问题，建议本次迭代修复）

#### MAJ-1: 依赖未满足时 `_dispatch` 无限快速重试，存在 busy-loop 风险

- **问题描述**: `_dispatch` 中当依赖未满足或同 agent 并发达到上限时，任务被标记为 `BLOCKED` 后立即重新 `heappush` 回队列，并通过 `asyncio.create_task(self._dispatch())` 继续调度。若队列中大量任务长期处于阻塞状态，会不断触发空转调度。
- **代码位置**:
  - [scheduler.py#L171-L206](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L171-L206)
- **为什么是个问题**: 无退避的忙等会占用 CPU 与事件循环资源，且依赖任务完成后无法被主动唤醒，只能依赖轮询。
- **修复建议**: 引入依赖完成通知机制（如依赖任务结束时主动唤醒依赖方）或最小重试间隔（如 0.1~0.5 秒），避免无限制快速循环。

#### MAJ-2: `AgentExecutor.run` 的 `finalize` 使用 `self.task.result or {}`，导致审计记录的 `result_status` 始终为 "unknown"

- **问题描述**: `AgentExecutor.run` 在 `finally` 中调用 `self.context.finalize(self.task.result or {})`。但 `self.task.result` 在 `AgentExecutor.run` 执行时仍为空字典（由 `TaskScheduler._execute` 在任务完成后才设置），因此 `finalize` 记录的 `result_status` 几乎总是 "unknown"。
- **代码位置**:
  - [executor_wrapper.py#L75-L77](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/executor_wrapper.py#L75-L77)
- **为什么是个问题**: 任务审计链无法正确反映执行结果，影响故障排查与证据收集。
- **修复建议**: 将 `run` 方法内部得到的实际 `result` 传入 `finalize`，即 `self.context.finalize(result)`。

#### MAJ-3: `TaskStore` 在异步方法中直接使用 `threading.Lock`，阻塞事件循环

- **问题描述**: `TaskStore.save`、`load`、`list_tasks`、`compact` 均为同步方法并使用 `threading.Lock`。虽然实现说明称其为“同步持久化”，但 `TaskScheduler` 在异步上下文中直接 `self._store.save(task)`，会阻塞 asyncio 事件循环。
- **代码位置**:
  - [task_store.py#L44-L109](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/task_store.py#L44-L109)
  - [scheduler.py#L89-L97](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L89-L97)
- **为什么是个问题**: 高频任务状态保存会拖慢整个调度器响应，极端情况下导致事件循环无法及时处理取消/超时信号。
- **修复建议**: 将 `TaskStore` 改造为 `asyncio.Lock` + 异步文件 IO；或在调用处通过 `asyncio.to_thread` 将同步保存委托给线程，避免阻塞事件循环。

#### MAJ-4: `A2ABus.publish_sync` 非线程安全地修改 `_history`

- **问题描述**: `publish` 使用 `_history_lock` 保护 `_history` 的追加操作，而 `publish_sync` 直接 `self._history.append(message)`，未加锁。
- **代码位置**:
  - [a2a_bus.py#L70-L100](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/a2a_bus.py#L70-L100)
- **为什么是个问题**: 当同步与异步发布并发执行时，`_history` 列表可能出现数据竞争、消息丢失或异常状态。
- **修复建议**: 在 `publish_sync` 中也使用 `_history_lock`（注意同步代码中需使用 `asyncio.run` 或避免与异步锁混用）；或统一使用队列/锁机制管理历史记录。

#### MAJ-5: 任务取消后底层 worker 线程仍继续运行，且无法被协作式取消

- **问题描述**: 由于使用 `ThreadPoolExecutor`/`_DaemonThreadPool`，已开始执行的同步 `execute_agent` 无法被 Python `Future.cancel()` 真正中断。`TaskScheduler` 只能在 asyncio 层面释放 semaphore 并标记状态，但底层线程可能继续占用 CPU/IO 资源。
- **代码位置**:
  - [worker_pool.py#L171-L206](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/worker_pool.py#L171-L206)
  - [scheduler.py#L224-L275](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L224-L275)
- **为什么是个问题**: 长时间运行的 agent 任务（如 LLM 调用、大规模代码生成）被取消后仍继续执行，造成资源浪费，且可能继续写文件/改状态。
- **修复建议**: 在 `AgentExecutor` 中暴露取消检查点（如将 `task_input["_cancelled_event"]` 注入执行器，或在执行器内部定期轮询共享取消标志）；文档中明确此为当前限制，并建议对不可信/长时间任务使用未来实现的 `subprocess` 模式。

#### MAJ-6: `_handle_spawn_agent` sync 模式对 `mode` 字段的判断依赖 `execution_result.get("status") == "executed"`，但 `execution_result` 可能为空

- **问题描述**: 当 `execution_result` 为空字典时，`mode` 会被错误设置为 `"hint_only"`，即使任务实际已被执行。
- **代码位置**:
  - [tools/dispatcher.py#L324-L336](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/tools/dispatcher.py#L324-L336)
- **为什么是个问题**: 返回给 MCP 客户端的 `mode` 字段误导调用方，影响结果解析。
- **修复建议**: 将 `mode` 判断逻辑与 orchestrator 返回的 `spawned_to` 或任务实际执行状态解耦，确保只要有 `task_id` 且执行完成即返回 `"executed"`。

#### MAJ-7: `TaskStore` 查询为 O(n) 全文件扫描，长期运行性能差

- **问题描述**: `load`、`list_tasks`、`recover_latest` 每次均读取并解析整个 JSONL 文件。随着任务数量增长，查询耗时线性增加。
- **代码位置**:
  - [task_store.py#L58-L122](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/task_store.py#L58-L122)
- **为什么是个问题**: 高频查询（如 `get_task_status` 轮询）在任务量大时会导致 IO 瓶颈。
- **修复建议**: 在内存中维护 `task_id -> file_offset` 索引，或使用 SQLite 等轻量级持久化方案替换 JSONL。

---

### 2.3 Minor（一般问题，建议修复）

#### MIN-1: `A2ABus._history` 无界增长，存在内存泄漏风险

- **问题描述**: `_history` 持续追加已发布消息，没有清理或容量限制。
- **代码位置**:
  - [a2a_bus.py#L55](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/a2a_bus.py#L55)
- **为什么是个问题**: 长期运行服务中内存持续增长。
- **修复建议**: 设置最大容量（如 10000 条），超出时按 LRU 或时间淘汰。

#### MIN-2: `TaskScheduler._wait_until_terminal` 使用轮询，低效且增加延迟

- **问题描述**: `_wait_until_terminal` 通过 `asyncio.sleep(0.05)` 轮询任务状态。
- **代码位置**:
  - [scheduler.py#L345-L353](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L345-L353)
- **为什么是个问题**: 增加 CPU 开销与响应延迟。
- **修复建议**: 使用 `asyncio.Event` 或 A2A 事件订阅，在任务到达终态时主动唤醒等待者。

#### MIN-3: `TaskContext._resolve_workspace` 与 `_resolve_shared_dir` 代码重复

- **问题描述**: 两个方法逻辑几乎一致，仅返回路径不同。
- **代码位置**:
  - [task.py#L182-L196](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/task.py#L182-L196)
- **修复建议**: 提取公共的 workspace 解析函数。

#### MIN-4: `server.py` 硬编码诊断日志路径

- **问题描述**: `_DIAG_LOG` 硬编码为 `g:\ai-gongju\Loop-agent\loop-agent-mcp\.mcp-server-diag.log`，不适合生产部署或跨平台使用。
- **代码位置**:
  - [server.py#L35-L46](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/server.py#L35-L46)
- **为什么是个问题**: 在 Linux/macOS 或其他部署路径下会失败或写入不可预期位置。
- **修复建议**: 使用环境变量或项目根目录相对路径（如 `Path(__file__).resolve().parent.parent / ".mcp-server-diag.log"`）。

#### MIN-5: `_execute` 中 CANCELLED 状态的任务会同时发布 `task.cancelled` 与 `task.finished` 事件

- **问题描述**: `cancel_task()` 发布 `task.cancelled` 后，`_execute` 的 `finally` 块中因 `task.status` 不属于 SUCCEEDED/FAILED/TIMEOUT，又会发布 `task.finished`。
- **代码位置**:
  - [scheduler.py#L118-L137](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L118-L137)
  - [scheduler.py#L288-L300](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L288-L300)
- **为什么是个问题**: 事件语义不一致，监听 `task.finished` 的订阅者会收到一个已取消任务的“完成”事件。
- **修复建议**: 在 `finally` 中增加对 `CANCELLED` 的分支，发布 `task.cancelled` 而非 `task.finished`。

#### MIN-6: `AgentExecutor.run` 参数 `_task` 命名不规范

- **问题描述**: 公共/半公共方法参数以 `_` 开头，通常表示私有/未使用，但此处实际被使用。
- **代码位置**:
  - [executor_wrapper.py#L22](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/executor_wrapper.py#L22)
- **修复建议**: 重命名为 `task` 或 `task_override`。

#### MIN-7: 依赖失败后下游任务永久 `BLOCKED`，不会主动失败

- **问题描述**: `_dependencies_satisfied` 仅在依赖状态为 `SUCCEEDED` 时返回 True。若依赖 `FAILED`/`CANCELLED`/`TIMEOUT`，下游任务将永远 `BLOCKED` 并不断重试。
- **代码位置**:
  - [scheduler.py#L329-L338](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/scheduler.py#L329-L338)
- **为什么是个问题**: 与架构文档“硬依赖失败则下游进入 BLOCKED”一致，但缺少最终失败传播机制，可能导致任务永远挂起。
- **修复建议**: 增加依赖终态检测，当依赖进入 FAILED/CANCELLED/TIMEOUT 时，将下游任务标记为 FAILED 或 CANCELLED，并发布相应事件。

#### MIN-8: `TaskStore.compact` 在 Windows 上先 `unlink` 再 `rename`，存在竞态窗口

- **问题描述**: Windows 下 `rename` 无法覆盖已存在文件，代码先 `unlink` 原文件再 `rename`。虽然在锁内，但进程崩溃时可能导致数据丢失。
- **代码位置**:
  - [task_store.py#L142-L152](file:///g:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/runtime/task_store.py#L142-L152)
- **修复建议**: 使用原子写入模式：写入 `.tmp` 文件后，在 Unix 直接 `replace`，在 Windows 使用 `os.replace`（Python 3.3+ 支持覆盖）。

---

### 2.4 Nitpick（可选优化）

#### NIT-1: 类型注解可进一步精确

- `TaskScheduler.submit_and_wait` 的 `**kwargs: Any` 可以替换为明确的可选参数字典类型。
- `WorkerPool.submit` 的 `executor_factory` 返回类型可标注为 `Callable[[Task], dict[str, Any]]`。

#### NIT-2: `process` / `subprocess` 执行模式仅为占位实现

- 代码中已明确标注为“预留扩展点”，符合实现说明中的已知限制。建议补充 `NotImplementedError` 或更清晰的文档。

#### NIT-3: `_DaemonThreadPool` 的 `shutdown` 中 `t.join(timeout=5.0)` 超时后未记录未能 joined 的线程

- 建议增加日志记录，便于排查关闭挂起问题。

#### NIT-4: 部分 docstring 中版本号标注为 v1.4，建议统一维护

- 如 `state.py`、`dispatcher.py`、`server.py` 中均出现 v1.4 注释，未来版本升级时容易遗漏。

---

## 3. 测试覆盖评估

### 3.1 已覆盖的正面场景

- 多任务真正并行执行（`test_multiple_agents_run_in_parallel`、`test_multi_agent_roles_run_concurrently`）。
- 优先级调度（`test_task_priority_and_dependencies`）。
- 依赖成功/失败传播（`test_task_priority_and_dependencies`、`test_dependency_failure_blocks_dependent_task`）。
- 任务取消与资源释放（`test_task_cancellation`、`test_cancel_task_releases_resources`）。
- 任务超时（`test_task_timeout`）。
- A2A 事件发布顺序（`test_a2a_events_published`、`test_a2a_observer_receives_state_change_events`）。
- workspace 隔离（`test_per_task_workspace_isolation`）。
- dispatcher async/sync 双模式（`test_dispatcher_spawn_agent_async_mode`、`test_dispatcher_spawn_agent_sync_mode`）。
- 高并发压力（`test_high_concurrency_stress`）。
- worker 池优雅关闭（`test_worker_pool_graceful_shutdown`）。

### 3.2 未覆盖或覆盖不足的场景

1. **CR-1 双重超时竞态**: `test_task_timeout` 因超时时间极短且 mock 睡眠较长，恰好触发外层 wait 超时，未能覆盖内部超时先返回的竞态分支。
2. **CR-2 重试退避阻塞 semaphore**: 无测试验证重试期间 semaphore 是否被释放。
3. **CR-3 `dispatch()` 在运行事件循环中调用**: 无相关测试。
4. **agent 并发上限**: `agent_concurrency_limit` 未在测试中被限制和验证。
5. **跨 Loop 隔离**: 未验证不同 `loop_id` 的任务是否写入不同的 StateManager 状态。
6. **`TaskStore` 崩溃恢复**: `recover_latest` 未测试。
7. **调度器关闭时正在运行的任务**: 未测试 `close()` 在任务执行中时的行为。
8. **`StateManager` 线程局部隔离**: `test_concurrent_state_manager_writes` 中 `mock_execute` 使用 `task_input.get("_loop_id", "")` 为空字符串，未真正触发 `AgentExecutor.run` 中的 `set_thread_loop(task.loop_id)`，因此该测试未能验证线程局部 Loop 上下文的隔离效果。

---

## 4. 必须修复清单（按优先级排序）

| 优先级 | 问题 ID | 文件 | 修复要点 |
|--------|---------|------|----------|
| P0 | CR-1 | `runtime/worker_pool.py`, `runtime/scheduler.py` | 移除 `WorkerPool` 内部超时，统一由 `TaskScheduler` 控制超时与状态转移 |
| P0 | CR-2 | `runtime/scheduler.py` | 将重试退避移出 `semaphore` 保护区，避免阻塞并发槽 |
| P0 | CR-3 | `tools/dispatcher.py` | 修复 `dispatch()` 在运行事件循环中的兼容行为，或明确报错并引导使用 `async_dispatch()` |
| P1 | MAJ-2 | `runtime/executor_wrapper.py` | `finalize` 使用实际 `result` 而非 `self.task.result` |
| P1 | MAJ-3 | `runtime/task_store.py`, `runtime/scheduler.py` | 将 `TaskStore` 改造为异步锁 + 异步 IO，或在调用处使用 `asyncio.to_thread` |
| P1 | MAJ-4 | `runtime/a2a_bus.py` | 统一 `publish` 与 `publish_sync` 对 `_history` 的并发访问保护 |
| P1 | MAJ-5 | `runtime/worker_pool.py`, `runtime/executor_wrapper.py` | 增加协作式取消检查点或文档化限制 |
| P1 | MAJ-6 | `tools/dispatcher.py` | 修正 sync 模式 `mode` 字段判断逻辑 |
| P1 | MAJ-1 | `runtime/scheduler.py` | 依赖阻塞时增加最小重试间隔或主动唤醒机制 |
| P2 | MIN-1 ~ MIN-8 | 多个文件 | 按上述修复建议逐项处理 |

---

## 5. 最终结论

- **评分**: 6.8 / 10
- **门禁状态**: **不通过（Rejected for remediation）**
- **是否可进入测试阶段**: 否，需先修复 Critical 问题并补充相关测试。
- **是否可进入部署阶段**: 否。

本次实现展现了清晰的并行调度架构与较好的测试广度，但存在 3 项 Critical 级别的状态机与并发控制缺陷，可能在高并发、超时、重试等生产场景下引发严重故障。建议在修复上述问题、补充对应测试并通过重新审查后，再进入下一阶段。

---

**报告输出路径**: `g:\ai-gongju\Loop-agent\loop-agent-mcp\docs\CODE_REVIEW_PARALLEL.md`
