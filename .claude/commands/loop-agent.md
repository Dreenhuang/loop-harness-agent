# /loop-agent - 启动 Loop Agent 完整流程

请按以下步骤执行：

1. 调用 `mcp__loop-agent__list_agents` 确认 16 角色就位
2. 调用 `mcp__loop-agent__get_status` 读取当前黑板状态
3. 输出项目当前进度总结
4. 询问用户："请提供 PRD 文档路径或粘贴 PRD 内容"

参数说明：
- 无参数：启动完整流程
- `status`：仅查询状态，不启动
- `resume`：接续上次未完成流程
- `abort`：中止当前 Loop

**参考文档**：
- 触发后行为：见 `CLAUDE.md` §二
- 16 角色：见 `CLAUDE.md` §三
- 10 相位：见 `CLAUDE.md` §四
