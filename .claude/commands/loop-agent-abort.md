# /loop-agent abort - 中止当前 Loop

请执行：

1. 询问用户确认："确认要中止当前 Loop 吗？此操作不可逆。"
2. 用户确认后 → 调用 `mcp__loop-agent__abort_loop`
3. 输出中止原因和当前状态快照
