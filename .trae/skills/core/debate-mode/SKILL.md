# Skill: debate-mode 辩论对抗拓扑

> **Skill ID**: `debate-mode`
> **类型**: 拓扑类
> **解决偏差**: D-01（辩论对抗拓扑未实现）
> **蓝皮书**: 第四章 6 种编排拓扑 #6

## 一、用途

**实施辩论对抗拓扑**：两个独立 Agent 持不同观点互相挑战，第三方 Judge 仲裁。用于：
- 安全审计（红蓝对抗）
- 架构决策（多方案 PK）
- Bug 根因分析（多假设辩论）

## 二、辩论结构

```
Topic（议题）
    ↓
┌─ Proponent（正方） ─┐
│  持观点 A            │
│  收集支持证据        │
└──────────┬───────────┘
           ↓
       Rebuttal（互相反驳）
           ↓
┌─ Opponent（反方） ───┐
│  持观点 B            │
│  提出反例            │
└──────────┬───────────┘
           ↓
      Judge（仲裁）
    ├─ 评估双方证据
    ├─ 输出 winner
    └─ 给出 reasoning
```

## 三、典型应用：架构决策

```yaml
debate_topic: "是否采用微服务架构"
agents:
  proponent:
    name: "@Architect-Pro"
    position: "支持微服务"
    evidence_requirements:
      - "可扩展性数据"
      - "团队规模适配"
      - "部署独立性"
  opponent:
    name: "@Architect-Con"
    position: "反对微服务"
    evidence_requirements:
      - "运维复杂度"
      - "数据一致性挑战"
      - "团队学习成本"
  judge:
    name: "@Final-Reviewer"
    decision_criteria:
      - "项目规模适配度"
      - "团队能力匹配度"
      - "业务场景契合度"
max_rounds: 3
consensus_required: false  # 双方可不达成一致
```

## 四、调用方式

```text
@Orchestrator 检测需要辩论场景
    ↓
激活 debate-mode
    ├─ 召集 Proponent + Opponent
    ├─ 设置议题
    └─ 启动 3 轮辩论
    ↓
Judge 仲裁
    ├─ 输赢判定
    ├─ 给出 reasoning
    └─ 写入 blackboard/debates/
```

## 五、输出格式

```json
{
  "debateId": "debate-2026-06-15-001",
  "topic": "微服务 vs 单体",
  "rounds": [
    {
      "round": 1,
      "proponent": "支持微服务，理由...",
      "opponent": "反对，理由..."
    }
  ],
  "judge_decision": {
    "winner": "Opponent",
    "reasoning": "当前项目规模小，单体更合适",
    "confidence": 0.85
  }
}
```
