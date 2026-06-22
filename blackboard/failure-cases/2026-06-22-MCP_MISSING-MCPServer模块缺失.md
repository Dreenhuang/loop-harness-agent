# 失败案例 2026-06-22-MCP_MISSING

## 1. 事件摘要

- **现象**：在 Claude Code 环境中触发 `/loop-harness-agent` 后，`mcp__loop-agent__start_loop` 调用立即失败，错误日志显示 `loop-agent-mcp` 目录下缺少 required module `loop_agent_mcp.server`。整个 Loop 无法进入 Phase 0 初始化。
- **时间**：2026-06-22 09:12
- **触发条件**：Claude Code 调用 MCP Server；本地开发时代码未完整提交；CI 未覆盖 MCP Server 安装测试。

## 2. 影响范围

- **直接损失**：Claude Code 侧无法启动任何 Loop 任务，用户反馈"命令无响应"。
- **影响模块 / 角色**：MCP Server、`loop-agent-mcp/` 模块、@Orchestrator 初始化、Phase 0 黑板创建。
- **阻塞时长**：所有 Claude Code 用户阻塞约 6 小时，直到手动安装缺失依赖并补全 `server.py`。

## 3. 根因分析（5 Whys）

1. **为什么 `start_loop` 调用失败？** 因为 Python 环境找不到 `loop_agent_mcp.server` 模块。
2. **为什么找不到模块？** 因为 `loop-agent-mcp/` 目录下缺少 `server.py`（或等效入口文件），且包未正确安装到当前环境。
3. **为什么缺少入口文件/未安装？** 因为本地开发时只提交了引擎代码，MCP Server 被视为"可选组件"未纳入发布清单。
4. **为什么被视为可选？** 因为部署文档与 CI 流程未将 MCP Server 列为启动 Loop 的必备依赖。
5. **为什么未列入必备依赖？** 因为项目初期以 Trae IDE 为主，未充分评估 Claude Code 路径对 MCP Server 的强依赖。

## 4. 修复措施

- **临时止血**：在 Claude Code 环境手动补全 `loop-agent-mcp/loop_agent_mcp/server.py`，并执行 `pip install -e loop-agent-mcp`。
- **永久修复**：
  - 补全 MCP Server 最小可运行代码，提供 `mcp__loop-agent__start_loop`、`mcp__loop-agent__get_status` 等工具实现。
  - 在 `loop-agent-mcp/` 添加 `pyproject.toml`，支持 `pip install -e .` 一键安装。
  - CI 流水线新增"MCP Server 安装与健康检查"步骤，确保每次提交后模块可导入、工具列表完整。
- **流程补丁**：`CLAUDE.md` 增加"Phase 0 必须先验证 MCP Server 安装完整性"的强制步骤。

## 5. 防御措施代码化（lint / test）

- **lint 规则**：新增 `mcp-server-module-exists` 规则，校验 `loop-agent-mcp/loop_agent_mcp/server.py` 存在且包含 `mcp__loop-agent__start_loop` 函数签名。
- **测试用例**：
  - `tests/test_mcp_server_import.py`：导入 `loop_agent_mcp.server`，断言关键工具函数存在。
  - `tests/test_mcp_health_check.py`：调用 `mcp__loop-agent__list_agents`，断言返回 16 个角色。
- **自动化门禁**：部署脚本在启动后端/前端前，先执行 `python -c "import loop_agent_mcp.server; loop_agent_mcp.server.list_agents()"`。

## 6. 知识库同步

- **更新规则**：`g:\ai-gongju\Loop-agent\CLAUDE.md` 故障排查章节新增"MCP Server 模块缺失诊断清单"。
- **新增知识条目**：`docs/knowledge/mcp-server-module-diagnosis.md` —— 《Claude Code 下 MCP Server 模块缺失排查》。
- **复盘结论**：Loop 的 Claude Code 路径将 MCP Server 作为入口，其安装完整性必须成为 Phase 0 的首要检查项。
