"""v1.3 代码生成质量评估模块。

改进 v1.2 的"伪执行"问题：v1.2 返回 status=executed
但生成代码充满 TODO。本模块提供：
1. CodeQuality 等级评估
2. 代码质量评分
3. 质量警告机制
"""
from __future__ import annotations

import re
from enum import Enum


class CodeQuality(Enum):
    """代码质量等级。"""
    SCAFFOLD = "scaffold"      # 脚手架（含TODO，需人工补充）
    TEMPLATE = "template"      # 模板（有基本结构，需少量修改）
    PRODUCTION = "production"  # 生产级（可直接使用）


def assess_quality(code: str) -> CodeQuality:
    """评估生成代码的质量等级。

    Args:
        code: 源代码字符串。

    Returns:
        CodeQuality 枚举值。
    """
    if not code or not code.strip():
        return CodeQuality.SCAFFOLD

    todo_count = count_todos(code)
    line_count = code.count("\n") + 1

    # 无 TODO 且代码行数 > 20 = 生产级
    if todo_count == 0 and line_count > 20:
        return CodeQuality.PRODUCTION

    # TODO 数量少且代码行数合理 = 模板级
    if todo_count <= 2 and line_count > 10:
        return CodeQuality.TEMPLATE

    # 大量 TODO 或代码过短 = 脚手架
    return CodeQuality.SCAFFOLD


def count_todos(code: str) -> int:
    """统计代码中的 TODO 标记数量。"""
    # 匹配 TODO: / TODO / FIXME / XXX 等标记
    pattern = r'\b(TODO|FIXME|XXX|HACK)\b'
    return len(re.findall(pattern, code, re.IGNORECASE))


def quality_score(code: str) -> dict[str, Any]:
    """计算代码质量分数。

    Returns:
        包含 quality/todo_count/line_count/score/grade 的字典。
    """
    todo_count = count_todos(code)
    line_count = code.count("\n") + 1
    quality = assess_quality(code)

    # 分数计算：基础分100，每TODO扣10分
    score = max(0, 100 - todo_count * 10)

    # 等级评定
    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    else:
        grade = "D"

    return {
        "quality": quality.value,
        "grade": grade,
        "todo_count": todo_count,
        "line_count": line_count,
        "score": score,
        "is_production_ready": quality == CodeQuality.PRODUCTION,
    }
