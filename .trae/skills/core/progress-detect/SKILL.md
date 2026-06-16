# Skill: progress-detect 无进展检测

> **Skill ID**: `progress-detect`
> **所属层级**: 第 1 层 - Skill 层（原子能力）
> **调用方**: @Orchestrator
> **调用时机**: 每轮迭代后（自动）

---

## 一、用途

检测 Loop Agent 是否陷入"原地打转"——连续多轮产出相同错误或无实质变化。

**这是 Loop Agent 防止无限循环的关键护栏（3 道硬刹车之一）**。

---

## 二、检测算法

```python
def detect_no_progress(state):
    """
    通过 3 个维度综合判断：
    1. 错误指纹连续性：连续 2 轮相同错误
    2. 文件 diff 相似度：连续 2 轮 diff 相似度 > 95%
    3. 黑板节点变更：连续 2 轮无新节点/状态变更
    """
    error_fingerprint = hash(state.last_errors)
    if error_fingerprint in state.recent_error_fingerprints[-2:]:
        return True  # 错误连续 3 次
    
    if state.last_diff_similarity > 0.95:
        return True  # Diff 高度相似
    
    if state.iterations_since_last_progress > 5:
        return True  # 5 轮无新进展
    
    return False
```

---

## 三、检测维度

| 维度 | 判定标准 | 权重 |
|------|----------|------|
| **错误指纹** | 连续 2 轮相同错误堆栈 | 高 |
| **Diff 相似度** | 连续 2 轮 diff 相似度 > 95% | 高 |
| **节点变更** | 连续 5 轮无新节点/状态变更 | 中 |
| **Token 消耗** | 单轮消耗超过平均 3 倍但无产出 | 中 |

---

## 四、调用方式

```text
@Orchestrator 调用 progress-detect Skill：
- 状态：第 8 轮
- 错误指纹：err-fp-2026-06-15-001
- 上一轮错误：err-fp-2026-06-15-001（相同）
```

---

## 五、输出

```json
{
  "no_progress_detected": true,
  "reason": "连续 3 轮相同错误指纹：err-fp-2026-06-15-001",
  "consecutive_count": 3,
  "recommendation": "STOP_AND_ESCALATE",
  "alternatives": [
    "查询知识库是否有类似问题解决方案",
    "分派 @Bug-Defect-Repairer 深度排查",
    "升级为 Phase 失败，回到 Phase 1 重新澄清需求"
  ]
}
```

---

## 六、Orchestrator 处理动作

| detection 结果 | Orchestrator 行为 |
|----------------|---------------------|
| `no_progress_detected: false` | 继续执行 |
| `no_progress_detected: true` | 输出 `STOP_AND_ESCALATE`，触发应急流程 |
| 连续 2 次 escalate | 立即停止 Loop，输出故障报告，触发人工介入 |

## 分级恢复机制（v1.1 新增）

> **对齐标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md` 第 6.3、8.3 节

### 恢复级别定义

当检测到无进展时，按以下分级执行恢复：

| 级别 | 触发条件 | 恢复动作 | 记录要求 |
|------|----------|----------|----------|
| Level 1: 重试 | 连续 1 轮无进展 | 自动重试当前任务（重置上下文） | 记录重试次数和原因 |
| Level 2: 回退 | 连续 2 轮无进展 | 回退到上一个检查点，重新执行 | 记录回退的 Phase 和检查点 ID |
| Level 3: 降级 | 连续 3 轮无进展 | 降级执行（跳过非关键步骤，保留核心路径） | 记录降级内容和影响范围 |
| Level 4: 人工确认 | 连续 3+ 轮无进展且降级无效 | 暂停 Loop，保存完整状态，等待人工确认 | 记录完整状态快照和决策日志 |

### 恢复动作详细说明

#### Level 1: 重试
```
1. 重置当前 Agent 上下文（Ralph 模式）
2. 从黑板重新读取任务输入
3. 重新执行当前任务
4. 最多重试 3 次
5. 重试成功 → 重置 noProgressCount
6. 重试失败 → 进入 Level 2
```

#### Level 2: 回退
```
1. 加载上一个检查点快照
2. 恢复黑板状态到检查点时刻
3. 从检查点 Phase 重新开始执行
4. 回退成功 → 重置 noProgressCount
5. 回退后仍然无进展 → 进入 Level 3
```

#### Level 3: 降级
```
1. 识别当前任务的核心路径 vs 非关键路径
2. 跳过非关键步骤（如：跳过 UX 审查、跳过文档归档）
3. 仅保留核心功能开发和基础测试
4. 降级执行完成后标记为"降级交付"
5. 降级后仍然无进展 → 进入 Level 4
```

#### Level 4: 人工确认
```
1. 保存完整状态快照到 blackboard/snapshots/
2. 生成"无进展报告"包含：
   - 连续无进展轮次
   - 已尝试的恢复动作
   - 当前 Phase 和任务状态
   - 建议的人工干预方向
3. 暂停 Loop，等待用户输入
4. 用户确认后恢复执行或中止
```

### 恢复记录格式

每次恢复动作必须记录到黑板偏离日志：

```json
{
  "timestamp": "2026-06-16T10:30:00Z",
  "phase": "Phase 5",
  "recovery_level": 2,
  "recovery_action": "回退到检查点 CP-004",
  "trigger_reason": "连续 2 轮无进展",
  "result": "成功恢复 / 仍然无进展",
  "next_action": "继续执行 / 升级到 Level 3"
}
```

### 与融合验收标准的对应

- Level 1-3 对应验收标准 6.3："系统具备无进展检测与自动中止/回退能力"
- Level 4 对应验收标准 8.3："连续 3 轮无有效进展时，系统能自动报警、暂停或回退"
- 所有恢复动作对应验收标准 7.2："自动修复、自动重试、自动回退必须留痕"

---

**【progress-detect · Loop Agent v1.0】**
