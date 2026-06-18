# /loop-agent resume - 接续未完成流程

请执行：

1. 调用 `mcp__loop-agent__get_status` 读取断点
2. 从断点继续执行：
   - 如果 Phase < 10 → 调用 `mcp__loop-agent__start_loop` (resume 模式)
   - 如果 Phase == 10 → 输出"流程已完成，无需接续"
3. 输出恢复信息
