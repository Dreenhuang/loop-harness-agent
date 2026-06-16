# UI-Design · UI 设计文档

> **工件类型**：强制工件
> **所属 Phase**：Phase 3
> **责任角色**：@UI-Designer
> **状态**：⏳ PENDING → 🔄 IN_PROGRESS → ✅ COMPLETED
> **融合验收标准**：g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md

| 字段 | 值 |
|------|-----|
| **文档版本** | v1.0 |
| **创建日期** | YYYY-MM-DD |
| **最后更新** | YYYY-MM-DD |
| **作者** | @UI-Designer |
| **审核者** | @UX-Researcher |
| **关联工件** | Product-Spec.md / Design-Brief.md |

---

## 1. 设计系统

<!-- 填写指引：定义全局设计系统参数，与 Design-Brief 中的 Token 对齐。 -->

### 1.1 Design Token 总览

| 类别 | Token 数量 | 来源 |
|------|-----------|------|
| 色彩 | | Design-Brief §3 |
| 字体 | | Design-Brief §4 |
| 间距 | | Design-Brief §5 |
| 圆角 | | Design-Brief §6.1 |
| 阴影 | | Design-Brief §6.2 |
| 动效 | | Design-Brief §6.4 |

### 1.2 网格系统

| 参数 | 桌面端 | 平板端 | 移动端 |
|------|--------|--------|--------|
| 断点 | ≥ 1024px | 768px - 1023px | < 768px |
| 列数 | 12 | 8 | 4 |
| 间距 | 24px | 16px | 16px |
| 外边距 | 64px | 32px | 16px |
| 最大宽度 | 1440px | 100% | 100% |

### 1.3 布局模式

| 模式 | 用途 | 说明 |
|------|------|------|
| 居中单列 | 表单/详情 | max-width: 720px, 居中 |
| 双栏 | 列表+详情 | 侧边栏 280px + 主内容区 |
| 全宽 | 仪表盘/数据 | 100% 宽度，内部网格 |

---

## 2. 页面清单

<!-- 填写指引：列出所有页面，标注优先级和状态。每个页面需有唯一编号。 -->

### 2.1 页面总览

| 编号 | 页面名称 | 路由 | 优先级 | 状态 | 设计稿链接 |
|------|----------|------|--------|------|-----------|
| PG-001 | <!-- 首页 --> | / | P0 | ⏳ | |
| PG-002 | | | | ⏳ | |
| PG-003 | | | | ⏳ | |

### 2.2 页面详细说明

#### PG-001：[页面名称]

- **页面目标**：<!-- 用户在此页面完成什么任务 -->
- **关键元素**：
  - <!-- 元素 1 -->
  - <!-- 元素 2 -->
- **页面结构**：
  ```
  ┌─────────────────────────────┐
  │ Header                      │
  ├─────────────────────────────┤
  │ Hero / Main Content         │
  ├─────────────────────────────┤
  │ Secondary Content           │
  ├─────────────────────────────┤
  │ Footer                      │
  └─────────────────────────────┘
  ```
- **关联功能**：F-XXX（来自 Product-Spec）
- **关联组件**：CMP-XXX

<!-- 按相同格式补充 PG-002, PG-003... -->

---

## 3. 组件规范

<!-- 填写指引：定义所有 UI 组件的视觉规范，包括尺寸、状态、变体。 -->

### 3.1 基础组件

| 编号 | 组件名称 | 类型 | 变体数 | 状态数 | 说明 |
|------|----------|------|--------|--------|------|
| CMP-001 | Button | 基础 | 4 | 5 | 主操作按钮 |
| CMP-002 | Input | 基础 | 2 | 4 | 文本输入框 |
| CMP-003 | Select | 基础 | 1 | 4 | 下拉选择器 |
| CMP-004 | Checkbox | 基础 | 1 | 3 | 复选框 |
| CMP-005 | Radio | 基础 | 1 | 3 | 单选框 |
| CMP-006 | Switch | 基础 | 1 | 3 | 开关 |
| CMP-007 | Tag | 基础 | 3 | 2 | 标签 |
| CMP-008 | Badge | 基础 | 2 | 1 | 徽标 |
| CMP-009 | Avatar | 基础 | 2 | 3 | 头像 |
| CMP-010 | Icon | 基础 | — | 2 | 图标 |

### 3.2 复合组件

| 编号 | 组件名称 | 类型 | 包含基础组件 | 说明 |
|------|----------|------|-------------|------|
| CMP-011 | Card | 复合 | Avatar/Tag/Button | 内容卡片 |
| CMP-012 | Modal | 复合 | Button/Input | 模态对话框 |
| CMP-013 | Table | 复合 | Button/Tag/Input | 数据表格 |
| CMP-014 | Form | 复合 | Input/Select/Button | 表单 |
| CMP-015 | Navigation | 复合 | Icon/Button | 导航栏 |
| CMP-016 | Toast | 复合 | Icon/Button | 消息提示 |
| CMP-017 | Dropdown | 复合 | Button/Icon | 下拉菜单 |
| CMP-018 | Tabs | 复合 | Icon/Tag | 标签页 |

### 3.3 组件详细规范（示例：Button）

#### CMP-001：Button

**变体**：

| 变体 | 背景 | 文字色 | 边框 | 用途 |
|------|------|--------|------|------|
| Primary | var(--primary) | #FFFFFF | none | 主操作 |
| Secondary | transparent | var(--primary) | 1px solid var(--primary) | 次要操作 |
| Ghost | transparent | var(--text-primary) | none | 轻量操作 |
| Danger | var(--error) | #FFFFFF | none | 危险操作 |

**尺寸**：

| 尺寸 | 高度 | 内边距 | 字号 | 圆角 |
|------|------|--------|------|------|
| Small | 32px | 8px 16px | 14px | var(--radius-sm) |
| Medium | 40px | 12px 24px | 16px | var(--radius-md) |
| Large | 48px | 16px 32px | 18px | var(--radius-md) |

**状态**：

| 状态 | 视觉表现 |
|------|----------|
| Default | 如上表 |
| Hover | 亮度 +10% |
| Active/Pressed | 亮度 -10% |
| Focus | outline: 2px solid var(--primary), outline-offset: 2px |
| Disabled | opacity: 0.5, cursor: not-allowed |

<!-- 按相同格式补充其他组件 -->

---

## 4. 状态变体

<!-- 填写指引：为每个页面/关键组件定义空状态、错误状态、加载状态的设计。 -->

### 4.1 全局状态

| 状态 | 视觉规范 | 文案规范 | 交互 |
|------|----------|----------|------|
| **空状态** | 插图 + 标题 + 描述 + 操作按钮 | 标题：说明无数据原因<br>描述：引导用户操作 | 提供 CTA 按钮 |
| **加载状态** | Skeleton / Spinner | 骨架屏占位或加载文案 | 禁止交互 |
| **错误状态** | 错误图标 + 标题 + 描述 + 重试 | 标题：发生了什么<br>描述：用户可以做什么 | 提供重试按钮 |
| **无网络** | 断网图标 + 提示 | "网络连接已断开" | 提供重试按钮 |
| **权限不足** | 锁定图标 + 提示 | "您没有权限访问此内容" | 提供申请/返回按钮 |

### 4.2 页面级状态映射

| 页面 | 空状态 | 加载状态 | 错误状态 |
|------|--------|----------|----------|
| PG-001 | | | |
| PG-002 | | | |

---

## 5. 交互规范

<!-- 填写指引：定义通用交互模式、动画规范和反馈机制。 -->

### 5.1 通用交互模式

| 交互类型 | 触发方式 | 反馈 | 时长 |
|----------|----------|------|------|
| 点击 | 鼠标左键/触摸 | 按压态 → 涟漪 | 100ms |
| 悬停 | 鼠标移入 | 背景色变化 + cursor: pointer | 200ms |
| 聚焦 | Tab 键 / 点击 | outline 显示 | 0ms |
| 拖拽 | 鼠标按住移动 | 阴影增强 + 透明度变化 | 200ms |
| 长按 | 触摸 500ms | 震动反馈 + 上下文菜单 | 500ms |

### 5.2 页面转场

| 转场类型 | 动画 | 时长 | 缓动 |
|----------|------|------|------|
| 前进 | slide-left | 300ms | ease-in-out |
| 后退 | slide-right | 300ms | ease-in-out |
| 弹出 | fade-in + scale(0.95→1) | 200ms | ease-out |
| 关闭 | fade-out + scale(1→0.95) | 150ms | ease-in |

### 5.3 反馈机制

| 场景 | 反馈类型 | 规范 |
|------|----------|------|
| 操作成功 | Toast | 绿色图标 + 文案，3s 自动消失 |
| 操作失败 | Toast | 红色图标 + 文案 + 重试按钮，5s 或手动关闭 |
| 表单校验失败 | Inline | 字段下方红色文案 + 边框变红 |
| 删除确认 | Modal | 危险操作二次确认 |
| 批量操作 | Progress | 进度条 + 百分比 + 取消按钮 |

---

## 6. Design Token

<!-- 填写指引：汇总所有 Token 的 CSS 变量定义，供开发直接引用。 -->

### 6.1 Token 导出格式

```css
:root {
  /* === 色彩 === */
  --color-primary: #;
  --color-secondary: #;
  --color-accent: #;
  --color-success: #;
  --color-warning: #;
  --color-error: #;
  --color-info: #;
  --color-text-primary: #;
  --color-text-secondary: #;
  --color-text-disabled: #;
  --color-border: #;
  --color-bg-primary: #;
  --color-bg-secondary: #;
  --color-bg-elevated: #;

  /* === 字体 === */
  --font-family-heading: ;
  --font-family-body: ;
  --font-family-code: ;
  --font-display: 700 48px/1.2 var(--font-family-heading);
  --font-h1: 700 36px/1.3 var(--font-family-heading);
  --font-h2: 600 28px/1.3 var(--font-family-heading);
  --font-h3: 600 22px/1.4 var(--font-family-heading);
  --font-h4: 500 18px/1.4 var(--font-family-heading);
  --font-body: 400 16px/1.6 var(--font-family-body);
  --font-body-sm: 400 14px/1.5 var(--font-family-body);
  --font-caption: 400 12px/1.4 var(--font-family-body);
  --font-overline: 500 12px/1.2 var(--font-family-body);

  /* === 间距 === */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;

  /* === 圆角 === */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* === 阴影 === */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.15);

  /* === 动效 === */
  --duration-micro: 100ms;
  --duration-small: 200ms;
  --duration-medium: 300ms;
  --duration-large: 500ms;
  --easing-default: ease-in-out;
}
```

---

## 7. 响应式策略

<!-- 填写指引：定义各断点下的布局适配策略。 -->

### 7.1 断点定义

| 断点名称 | 宽度范围 | 设备 |
|----------|----------|------|
| xs | 0 - 479px | 小屏手机 |
| sm | 480px - 767px | 大屏手机 |
| md | 768px - 1023px | 平板 |
| lg | 1024px - 1439px | 小桌面 |
| xl | 1440px+ | 大桌面 |

### 7.2 适配策略

| 组件/页面 | 桌面端 (lg+) | 平板端 (md) | 移动端 (sm-) |
|-----------|-------------|-------------|-------------|
| 导航 | 顶部水平导航 | 顶部水平导航（折叠） | 底部标签栏 + 汉堡菜单 |
| 侧边栏 | 固定侧边栏 | 可收起侧边栏 | 隐藏，抽屉弹出 |
| 表格 | 完整表格 | 可横向滚动 | 卡片列表 |
| 表单 | 双列表单 | 单列表单 | 单列表单 |
| 模态框 | 居中弹窗 | 居中弹窗 | 底部抽屉 |

### 7.3 触控适配

| 参数 | 值 | 说明 |
|------|-----|------|
| 最小触控区域 | 44px × 44px | 符合 Apple HIG / Material |
| 触控间距 | ≥ 8px | 防止误触 |
| 手势支持 | 滑动/长按/双击 | 移动端增强 |

---

## 附录

### A. 设计稿索引

| 页面 | 桌面端 | 移动端 | 状态 |
|------|--------|--------|------|
| PG-001 | [链接] | [链接] | ⏳ |

### B. 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| YYYY-MM-DD | v1.0 | 初始版本 | @UI-Designer |
