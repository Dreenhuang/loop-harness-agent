# /spawn-agent - 手动派发 Agent 任务

请执行：

1. 询问用户：
   - 派发哪个 Agent？（列出 16 角色，参考 `CLAUDE.md` §三）
   - 任务输入是什么？
2. 调用 `mcp__loop-agent__spawn_agent` 传入：
   - `agent_type`: 选定的角色
   - `task_input`: 任务输入
3. 输出任务派发结果

**16 角色清单**：
- `orchestrator` - 总控调度
- `product_manager` - 业务决策
- `requirements` - 需求分析
- `ux_researcher` - UX 设计
- `ui_designer` - UI 设计
- `architect` - 架构设计
- `backend` - 后端开发
- `frontend` - 前端开发
- `bug_defect_repairer` - Bug 修复
- `code_reviewer` - 代码审查（Gate 1）
- `professional_performance` - 性能压测（Gate 2）
- `tester` - 全栈测试（Gate 3）
- `knowledge_curator` - 知识沉淀
- `documenter` - 文档生成
- `final_reviewer` - 最终终审（Gate 4）
- `devops` - 部署运维
