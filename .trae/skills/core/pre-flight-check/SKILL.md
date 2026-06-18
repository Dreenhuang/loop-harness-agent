# Skill: pre-flight-check 起飞前检查

> **Skill ID**: `pre-flight-check`
> **类型**: 守卫类
> **解决偏差**: D-08（蓝皮书第九章 Step 5 自动化）
> **触发时机**: Loop Agent 启动 Phase 0 末尾 / Phase 1 启动前

## 一、用途

**Phase 0 完成后自动跑 8 项检查，确保 Phase 1 启动前所有前置条件就位**。

## 二、8 项检查清单

```yaml
checks:
  - id: PFC-1
    name: "黑板已创建"
    check: "项目进度记录.md 存在且含 12 区块"
    
  - id: PFC-2
    name: "PRD 已就位"
    check: "docs/prd.md 存在"
    
  - id: PFC-3
    name: "时间预算已设置"
    check: "项目进度记录.md 含 max_duration_hours"
    
  - id: PFC-4
    name: "4 级封装资产完整"
    check: ".trae/skills/ .trae/agents/ .trae/workflows/ domain-chips/ 全部存在"
    
  - id: PFC-5
    name: "Ralph 模式 100% 覆盖"
    check: "16 Agent Profile 全部有 reset_context_each_turn = true"
    
  - id: PFC-6
    name: "门禁角色就位"
    check: "4 道门禁（code-review/performance/tester/final-reviewer）配置完整"
    
  - id: PFC-7
    name: "MCP 工具链可用"
    check: "mcp/*.mcp.json 4 个配置文件存在"
    
  - id: PFC-8
    name: "决策日志路径已配置"
    check: "decision_log.json 路径已写入项目进度记录"
```

## 三、执行流程

```
Loop Agent 触发
    ↓
Phase 0: 加载资产 + 初始化黑板
    ↓
【v1.2 新增】pre-flight-check 自动执行
    ├─ PFC-1 ~ PFC-8 逐项检查
    ├─ 通过 → 输出"✅ 起飞前检查全通过，进入 Phase 1"
    └─ 不通过 → 输出失败项 + 修复建议
         ├─ 阻断型（PFC-1/2/3/4）→ 强制修复
         └─ 警告型（PFC-5/6/7/8）→ 提示但可继续
```

## 四、输出格式

```json
{
  "taskId": "preflight-2026-06-15-001",
  "passed": true,
  "checks": {
    "PFC-1": { "name": "黑板已创建", "passed": true, "details": "12 区块齐全" },
    "PFC-2": { "name": "PRD 已就位", "passed": true, "details": "docs/prd.md 存在" },
    "PFC-3": { "name": "时间预算已设置", "passed": true, "details": "9 小时" },
    "PFC-4": { "name": "4 级封装资产完整", "passed": true, "details": "全部就位" },
    "PFC-5": { "name": "Ralph 模式 100% 覆盖", "passed": true, "details": "16/16 满足" },
    "PFC-6": { "name": "门禁角色就位", "passed": true, "details": "4/4" },
    "PFC-7": { "name": "MCP 工具链可用", "passed": true, "details": "4 MCP" },
    "PFC-8": { "name": "决策日志路径已配置", "passed": true, "details": "就位" }
  },
  "blocking_failures": [],
  "warnings": [],
  "next_action": "进入 Phase 1 需求基线"
}
```

## 五、失败处理

- **阻断型失败**：Loop 必须停止，等待用户修复
- **警告型失败**：输出警告但可继续
- **自动修复**：能自动修的（如 Ralph 模式缺失）自动补
