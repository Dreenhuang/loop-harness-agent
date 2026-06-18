# PRD 输入区

> **用途**：放置待处理的 PRD 文档
> **路径**：`blackboard/input/`
> **入口文件**：`prd.md`（推荐）

---

## 使用方式

### 1. 准备 PRD

```bash
# 方式 1：直接复制你的 PRD
cp your-prd.md blackboard/input/prd.md

# 方式 2：使用 Loop Agent PRD 模板
# 模板位置：blackboard/templates/prd-template.md（待补充）
```

### 2. 触发 Loop Agent

在 Trae 中：

```text
/loop-agent
# 或
用 Loop Agent 模式开发
```

系统会自动：
1. 读取 `blackboard/input/prd.md`
2. 派发 @Product-Manager + @Requirements 处理
3. 进入 10 相位流水线

---

## PRD 必备要素

为了让 Loop Agent 完整工作，PRD 至少包含：

| 要素 | 说明 | 必需 |
|------|------|------|
| **项目名称** | 用于标识 | ✅ |
| **业务目标** | 要解决什么问题 | ✅ |
| **目标用户** | 谁会用 | ✅ |
| **核心功能列表** | MVP 功能点 | ✅ |
| **验收标准** | 可量化的成功标准 | ✅ |
| **非功能需求** | 性能/安全/可用性 | ⭕ 推荐 |
| **技术栈偏好** | 可选 | ⭕ |

---

## 示例 PRD 结构

```markdown
# PRD: [项目名]

## 1. 业务背景
[为什么做这个]

## 2. 目标用户
[谁会用、解决什么问题]

## 3. 核心功能
### 3.1 [功能 1]
- 描述：
- 验收标准：

### 3.2 [功能 2]
...

## 4. 非功能需求
- 性能：P95 < 300ms
- 安全：1000 并发
- ...

## 5. 技术栈偏好（如有）
- 前端：Vue 3
- 后端：Bun + Hono
- 数据库：PostgreSQL
- 部署：CloudBase
```

---

## 多个 PRD 并行处理

如有多个并行项目，命名规则：

```text
blackboard/input/
├── prd.md                    # 主项目
├── prd-2026-06-15-todo.md    # Todo App
├── prd-2026-06-15-blog.md    # 博客
└── prd-2026-06-15-admin.md   # 后台管理
```

每个 PRD 独立走 10 相位流水线，互不干扰。

---

**【PRD 输入区 · 等待 PRD 投放】**
