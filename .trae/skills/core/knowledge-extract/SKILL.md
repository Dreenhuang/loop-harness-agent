# Skill: knowledge-extract 知识提取与沉淀

> **Skill ID**: `knowledge-extract`
> **所属层级**: 第 1 层 - Skill 层（原子能力）
> **调用方**: @Knowledge-Curator / @Bug-Defect-Repairer
> **调用时机**: Bug 修复完成 / 架构决策完成 / 阶段复盘

---

## 一、用途

把开发过程中遇到的问题、解决方案、最佳实践自动沉淀为可复用的知识库条目。

**遵循"问题解决经验文档管理规则"v1.0 的 6 段式模板**。

---

## 二、调用方式

```text
调用 knowledge-extract Skill：
- 触发事件: bug_fix_complete
- 标题: "SQL 注入防护 6 段式教程"
- 分类: 安全 / 后端 / P0 修复
- 证据: src/api/users.ts:42
```

---

## 三、输出（6 段式 Markdown）

```markdown
# 问题解决经验教程-YYYY-MM-DD-<主题关键词>

> **项目名称**：
> **BUG 主题**：
> **修复日期**：
> **修复者**：@Bug-Defect-Repairer
> **审核者**：@Final-Reviewer
> **影响版本**：
> **修复版本**：
> **文档版本**：v1.0
> **关键词**：

---

## 🐛 问题概述

**用户反馈**：""

**截图特征**：

### 问题分析步骤

#### 第 1 步：看症状
- 期望：
- 实际：

#### 第 2 步：查证据

```<语言>
// 关键代码 / 配置
```

#### 第 3 步：对差异

- 维度 1：
- 维度 2：
- **差异**：

#### 第 4 步：追根因

为什么会这样？

---

## 🔍 根因分析

根因是什么 / 为什么之前没发现 / 为什么第一次方案失败

---

## ✅ 解决方案

### 错误做法 ❌

```<语言>
// 不要这样做
```

### 正确做法 ✅

```<语言>
// 应该这样做
```

**关键设计取舍**：

---

## ✔️ 验证清单

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能基线达标
- [ ] 跨平台验证
- [ ] 用户验收通过

---

## 🛡️ 预防措施

### 评审 Checklist

- [ ] 检查项 1
- [ ] 检查项 2
- [ ] 检查项 3

### 自动化检测

- lint 规则 / 单元测试 / E2E 脚本

### 团队规则更新

- 如需更新到哪些规范文档

---

## 💡 经验总结

> 📌 **一句话教训**：
>
> **可复用场景**：

---
```

---

## 四、存储路径

```text
项目根/docs/问题解决经验教程/
├── 问题解决经验教程-YYYY-MM-DD-<主题>.md
├── README.md  ← 索引
└── ...
```

---

## 五、知识库索引

写入 `.blackboard/knowledge_index.json`：

```json
{
  "entries": [
    {
      "id": "KB-2026-06-15-001",
      "title": "SQL 注入防护",
      "category": "security/backend",
      "tags": ["sql-injection", "parameterized-query", "P0"],
      "path": "docs/问题解决经验教程/2026-06-15-sql-injection.md",
      "embedding_hash": "sha256:xxx",
      "created_at": "2026-06-15T14:30:00Z",
      "created_by": "@Knowledge-Curator",
      "applicability_score": 0.95
    }
  ]
}
```

---

## 六、相似度匹配

新问题出现时：

```python
def match_knowledge(new_problem, threshold=0.85):
    # 1. 向量化新问题
    # 2. 与知识库所有条目计算相似度
    # 3. 返回 top-3 高于阈值的结果
    # 4. 推荐给 @Orchestrator / @Bug-Defect-Repairer
```

---

## 七、停止条件

```yaml
stop_condition: |
  is_done = (
    knowledge_entry_written == true
    AND
    knowledge_index_updated == true
    AND
    a2a_message_sent == true
  )

max_attempts: 3
```

## 融合经验沉淀模板（v1.1 新增）

> **对齐标准**：`g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md` 第 7、8 节

### 偏离类型分类模板

知识沉淀时，必须按以下 5 类偏离进行分类记录：

| 偏离类型 | 定义 | 典型场景 |
|----------|------|----------|
| 流程偏离 | 跳过 Phase / 绕过 Gate / 未按依赖顺序执行 | 开发者跳过 Phase 4 直接编码 |
| 角色偏离 | 角色越权 / 角色缺位 / Maker-Checker 未分离 | @Orchestrator 直接写业务代码 |
| 目标偏离 | 输出偏离 PRD / 功能范围蔓延 / demo 级伪装生产级 | 开发过程中不断增加 PRD 外功能 |
| 资源偏离 | Token 超预算 / 时间超预算 / 连续无进展 | 连续 3 轮迭代无有效产出 |
| 结果偏离 | 缺工件 / 缺证据 / 缺部署前提 / 伪完成 | 声称"已完成"但缺少测试证据 |

### 融合经验 6 段式模板（扩展版）

在标准 6 段式模板基础上，增加融合验收维度：

```markdown
# [问题标题]

## 1. 问题背景
- 项目类型：
- Phase 阶段：
- 偏离类型：流程偏离 / 角色偏离 / 目标偏离 / 资源偏离 / 结果偏离

## 2. 问题现象
- 具体表现：
- 影响范围：
- 检测方式：自动检测 / 人工发现 / Gate 拦截

## 3. 根因分析
- 直接原因：
- 系统性原因：
- 是否触发一票否决：是 / 否

## 4. 解决方案
- 立即修复：
- 预防措施：
- 规则/流程改进建议：

## 5. 验证方法
- 验证命令：
- 预期结果：
- 回归测试：

## 6. 融合验收关联
- 关联验收标准章节：
- 工件影响：
- 证据影响：
- 建议新增/修改的规则：
```

### 沉淀触发条件

以下场景必须触发知识沉淀：
1. Gate 失败后修复成功
2. 偏离检测后恢复成功
3. 一票否决触发后解决
4. Token 失控后收敛
5. 无人值守模式异常恢复

---

**【knowledge-extract · Loop Agent v1.0】**
