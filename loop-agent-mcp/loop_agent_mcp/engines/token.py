"""Token 治理引擎：估算、预算跟踪、摘要策略、增量策略。

融合 v1.2 优化原则：
- 黑板优先（不在 LLM 上下文中重复装载）
- 工件优先（不复制主体内容，只传索引）
- 摘要优先（长报告先摘要再传）
- 增量优先（只传变更部分）
"""
from __future__ import annotations

import time
from typing import Any

from loop_agent_mcp.core.state import StateManager

# 经验值：每 1K token ≈ $0.002（不同模型差异较大，此为占位）
USD_PER_1K_TOKENS = 0.002
BUDGET_LIMIT_USD = 100.0
WARNING_THRESHOLD = 0.8
HALT_THRESHOLD = 0.95


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：英文 4 字符/token，中文 1.5 字符/token，取较小值。"""
    if not text:
        return 0
    # 简单启发式：长度 / 2
    return max(1, len(text) // 2)


def record_usage(text: str, label: str = "unspecified") -> dict[str, Any]:
    """登记一次 Token 使用并累加预算。"""
    tokens = estimate_tokens(text)
    cost = tokens / 1000.0 * USD_PER_1K_TOKENS

    def _op(s):
        s.budget_used_usd += cost
        s.last_action = f"record_usage:{label}"
    StateManager.get().mutate(_op)

    snapshot = get_budget_status()
    return {
        "label": label,
        "tokens_estimated": tokens,
        "cost_usd": round(cost, 6),
        "cumulative": snapshot,
    }


def get_budget_status() -> dict[str, Any]:
    """获取当前预算状态。"""
    state = StateManager.get().snapshot()
    used = state["budget_used_usd"]
    return {
        "used_usd": round(used, 4),
        "limit_usd": BUDGET_LIMIT_USD,
        "usage_percent": round(used / BUDGET_LIMIT_USD * 100, 2),
        "remaining_usd": round(BUDGET_LIMIT_USD - used, 4),
        "warning": used >= BUDGET_LIMIT_USD * WARNING_THRESHOLD,
        "halt": used >= BUDGET_LIMIT_USD * HALT_THRESHOLD,
    }


def should_summarize(text: str, threshold_tokens: int = 2000) -> bool:
    """是否应该摘要后传输。"""
    return estimate_tokens(text) > threshold_tokens


def summarize_for_orchestrator(text: str, max_lines: int = 20) -> str:
    """为 Orchestrator 生成摘要（保留前 max_lines 行 + 末尾 N 行）。"""
    lines = text.splitlines()
    if len(lines) <= max_lines * 2:
        return text
    head = lines[:max_lines]
    tail = lines[-max_lines:]
    omitted = len(lines) - max_lines * 2
    return "\n".join(head + [f"...（省略 {omitted} 行）..."] + tail)


def token_efficiency_check() -> dict[str, Any]:
    """Token 效率整体检查。"""
    state = StateManager.get().snapshot()
    used = state["budget_used_usd"]
    iterations = state["iterations"]
    cost_per_iter = used / max(iterations, 1)
    return {
        "budget_status": get_budget_status(),
        "iterations": iterations,
        "avg_cost_per_iteration_usd": round(cost_per_iter, 6),
        "convergence_ok": used < BUDGET_LIMIT_USD,
        "fusion_target_token_efficiency_ok": used < BUDGET_LIMIT_USD * HALT_THRESHOLD,
        "timestamp": time.time(),
    }
