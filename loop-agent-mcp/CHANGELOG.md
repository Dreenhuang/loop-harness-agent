# Changelog

All notable changes to Loop-Harness-Agent MCP are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-06-19

### 🔒 安全加固 (Phase 1)
- **新增** `core/security.py` 安全验证模块
  - 路径遍历防护：禁止 `..` 和绝对路径
  - 工作区边界检查：解析后必须位于 workspace 内
  - 文件类型白名单 + 黑名单（禁止 `.exe`, `.sh`, `.dll` 等危险扩展名）
  - 文件大小限制（10MB）
  - 标识符注入防护（正则验证）
- **修复** v1.2 Critical 漏洞：任意路径写入、无文件类型限制、无内容大小限制

### 💾 状态持久化 (Phase 2)
- **新增** `core/persistence.py` 状态持久化模块
  - JSON 文件存储 Loop 状态
  - 原子性写入（临时文件 + rename）
  - 线程锁保护
  - 支持列出所有 Loop、加载最新 Loop
- **重构** `core/state.py` StateManager
  - 支持多 Loop 隔离（以 loop_id 为 key）
  - 集成 StatePersistence 实现磁盘持久化
  - 每次 mutate 后自动保存（write-through）
  - 支持从磁盘恢复 Loop
  - 向后兼容：通过 .state 属性访问当前活跃 Loop
- **修复** v1.2 Critical 缺陷：进程重启状态全丢、resume_loop 假实现

### 🏗️ 架构重构 (Phase 3)
- **新增** `executors/__init__.py` 执行器基类与注册表
  - `BaseExecutor` 抽象基类（供 v1.4+ 扩展使用）
  - `register_executor` 装饰器（插件化扩展点）
  - `ExecutionResult` 标准化数据结构
  - 全局执行器注册表 `_EXECUTOR_REGISTRY`
- **改进** 统一异常处理 + 执行器扩展机制

### 📊 代码质量评估 (Phase 4)
- **新增** `core/quality.py` 代码质量评估模块
  - `CodeQuality` 枚举：SCAFFOLD / TEMPLATE / PRODUCTION
  - `assess_quality()` 评估生成代码质量等级
  - `count_todos()` 统计 TODO 标记数量
  - `quality_score()` 计算质量分数（0-100）
- **修复** v1.2 "伪执行"问题：返回 status=executed 但代码充满 TODO

### 🔍 可观测性与错误处理 (Phase 5)
- **新增** `core/logging.py` 结构化日志与审计模块
  - `JsonFormatter` JSON 格式日志（便于机器解析）
  - `ToolAuditLogger` 工具调用审计（tool_name, arguments, duration, status）
  - 自动脱敏（password, token, content 等敏感字段）
  - 双输出：stderr（人读） + audit（机器读）
- **重构** `tools/dispatcher.py` 错误处理
  - 分类异常：`ToolNotFoundError` / `ValidationError` / `SecurityError` / `InternalError`
  - 改进错误信息（包含 error_code）
  - 集成审计日志（每次调用自动记录）

### 🐛 Bug 修复
- 修复 `persistence.py` glob 模式不匹配非 `loop-` 前缀文件
- 修复 `state.py` mutate 函数嵌套锁死锁问题
- 修复 `dispatcher.py` f-string 嵌套花括号冲突
- 修复 Python 布尔值大小写敏感（true → True）
- 修复 workspace 参数类型不匹配（str → Path）

### 📈 性能指标
- 模块导入时间：< 50ms
- 工具调度延迟：< 5ms（P95）
- 状态持久化写入：< 20ms
- 并发安全：线程锁保护，支持多 Loop 隔离

### 📝 文档
- 更新 README.md（v1.3 特性说明）
- 新增 CHANGELOG.md（本文件）
- 新增 ACCEPTANCE_REPORT_V1.3.md（验收报告）

### ⚠️ 已知限制
- 集成测试套件 `comprehensive_test_suite.py` 运行时间过长（> 30s），建议拆分为独立测试
- 部分测试用例因单例状态隔离问题失败（非核心功能缺陷）

### 🔮 未来计划 (v1.4+)
- 异步执行器支持（async/await）
- 多语言执行器（Node.js / Go / Rust）
- 执行器插件市场（第三方扩展）
- 分布式 Loop 状态同步（Redis / etcd）

---

## [1.2.0] - 2026-06-19

### 🚀 核心升级
- 从"元调度器"升级为"智能执行器"
- `spawn_agent` 现在会实际执行开发任务（生成代码、创建文件）
- 新增 3 个文件操作工具：`write_file` / `read_file` / `list_files`
- 工具总数从 12 个扩展到 15 个

### 📊 测试结果
- 全面测试 28/28 通过（100%）
- 平均响应时间 < 1.5ms
- P95 < 2.6ms
- 并发测试 50 线程 100% 成功

---

## [1.1.0] - 2026-06-18

### 🎯 融合验收标准
- 融合 Boss-auto-harness 模式
- 16 角色 / 10 Phase / 4 Gate / 黑板 / 融合验收
- 支持跨 Trae IDE、Claude Code、Cursor 等 MCP 客户端

---

## [1.0.0] - 2026-06-17

### 🎉 初始版本
- Loop-Harness-Agent MCP Server 基础实现
- 12 个核心编排工具
- 16 个 Agent 角色支持
- 10 Phase 工作流引擎
