# UI Design: MCP 实时监控看板系统 - 视觉设计规范

> **版本**: v1.0.0
> **日期**: 2026-06-19
> **状态**: 设计冻结
> **基于**: PRD.md, Architecture.md, UX-Design.md
> **负责人**: @UI-Designer

---

## 一、设计理念与视觉语言

### 1.1 设计关键词
**专业、高效、实时、科技感**

### 1.2 视觉风格定位
- **风格**: 深色主题为主（Dark Mode First），浅色模式为辅
- **调性**: 类似 Datadog / Grafana 的监控仪表盘风格，但更现代简洁
- **氛围**: 数据密集但不拥挤，信息层级清晰

---

## 二、色彩系统 (Color System)

### 2.1 主色调 (Brand Colors)

| 用途 | 色值 | Hex | RGB | 使用场景 |
|------|------|-----|-----|---------|
| **Primary Blue** | 主品牌色 | `#1677FF` | rgb(22,119,255) | 按钮、链接、选中态 |
| **Primary Hover** | 悬停态 | `#4096FF` | rgb(64,150,255) | 按钮 hover |
| **Primary Active** | 点击态 | `#0958D9` | rgb(9,88,217) | 按钮 active |
| **Primary Light** | 浅背景 | `#E6F4FF` | rgb(230,244,255) | 卡片背景、标签 |

### 2.2 功能语义色 (Semantic Colors)

| 含义 | 色值 | Hex | 使用场景 |
|------|------|-----|---------|
| **Success 成功** | `#52C41A` | 完成态、Gate 通过、正常指标 |
| **Warning 警告** | `#FAAD14` | Token 接近上限、注意提示 |
| **Error 错误** | `#FF4D4F` | 异常 Agent、失败操作、错误日志 |
| **Info 信息** | `#1677FF` | 信息提示、默认链接 |

### 2.3 中性色 (Neutral Colors)

| 层级 | 文字/图标 | 边框 | 填充 | 使用场景 |
|------|----------|------|------|---------|
| **N-1** | `#FFFFFF` | - | `#FFFFFF` | 标题文字（深色模式） |
| **N-2** | `#FAFAFA` | - | `#FAFAFA` | 副标题 |
| **N-3** | `#D9D9D9` | `#D9D9D9` | `#F5F5F5` | 次要文字、分割线 |
| **N-4** | `#BFBFBF` | `#D9D9D9` | `#E8E8E8` | 禁用文字、占位符 |
| **N-5** | `#8C8C8C` | - | - | 辅助说明、时间戳 |
| **N-6** | `#595959` | - | - | 深色模式次要文字 |

### 2.4 状态专用色 (Status Colors)

| Agent 状态 | 边框 | 背景 | Badge 文字 | 进度条 |
|-----------|------|------|-----------|--------|
| **idle** | `#D9D9D9` | `#FAFAFA` | `#8C8C8C` | 不显示 |
| **running** | `#1890FF` | `#E6F7FF` | `#0958D9` | `#1677FF` → `#69B1FF` 渐变 |
| **error** | `#FF4D4F` | `#FFF2F0` | `#CF1322` | `#FF4D4F` → `#FF7875` 渐变 |
| **complete** | `#52C41A` | `#F6FFED` | `#389E0D` | `#52C41A` → `#95DE64` 渐变 |

### 2.5 深色模式色板 (Dark Theme)

| 元素 | 深色值 | 说明 |
|------|--------|------|
| **页面背景** | `#141414` | 最底层背景 |
| **卡片背景** | `#1F1F1F` | 组件容器背景 |
| **卡片边框** | `#303030` | 分割线、边框 |
| **主文字** | `#E8E8E8` | 标题、正文 |
| **次文字** | `#A6A6A6` | 描述、时间戳 |
| **禁用文字** | `#595959` | disabled 态 |
| **主品牌色** | `#4096FF` | 深色模式下提亮 |
| **成功色** | `#73D13D` | 深色模式下提亮 |
| **警告色** | `#FFC53D` | 深色模式下提亮 |
| **错误色** | `#FF7875` | 深色模式下提亮 |

---

## 三、字体系统 (Typography)

### 3.1 字体族 (Font Family)

```css
/* 字体栈 */
--font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
              'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue',
              Helvetica, Arial, sans-serif;

/* 等宽字体（代码/日志） */
--font-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo,
             Courier, monospace;
```

### 3.2 字号阶梯 (Type Scale)

| 层级 | 字号 | 行高 | 字重 | 使用场景 |
|------|------|------|------|---------|
| **Display** | 24px | 32px | 600 | 页面大标题 "MCP Monitor" |
| **H1** | 20px | 28px | 600 | 区域标题 "Agent Status Matrix" |
| **H2** | 16px | 24px | 600 | 子区域标题、卡片标题 |
| **H3** | 14px | 22px | 500 | 列表项标题、Agent 名字 |
| **Body** | 14px | 22px | 400 | 正文内容、描述文字 |
| **Caption** | 12px | 20px | 400 | 时间戳、辅助说明、Footer |
| **Code** | 13px | 20px | 400 | 日志消息、代码片段 |

### 3.3 字重使用规则

| 字重 | 值 | 使用场景 |
|------|-----|---------|
| Regular | 400 | 正文、日志消息 |
| Medium | 500 | 按钮、标签、导航 |
| Semi-Bold | 600 | 标题、重要数据 |
| Bold | 700 | 大数字、关键指标 |

---

## 四、间距与网格系统 (Spacing & Grid)

### 4.1 基础间距单位
基准单位：**4px**

| Token | 值 | 使用场景 |
|-------|-----|---------|
| `space-xs` | 4px | 图标与文字间隙、紧凑元素内边距 |
| `space-sm` | 8px | 小组件内边距、紧密排列元素间距 |
| `space-md` | 12px | 表单元素内边距、列表项间距 |
| `space-lg` | 16px | 卡片内边距、标准模块间距 |
| `space-xl` | 24px | 区域间分隔、大块内容外边距 |
| `space-xxl` | 32px | 页面级外边距、Section 间距离 |
| `space-xxxl` | 48px | 大区块间距 |

### 4.2 网格系统

```
桌面端容器宽度: max-width 1440px, padding 24px
列数: 12 列
列宽: auto (flex)
列间距 (gutter): 16px
行间距: 16px
```

### 4.3 卡片规范

| 属性 | 值 |
|------|-----|
| 圆角 (border-radius) | 8px |
| 内边距 (padding) | 16px |
| 外边距 (margin-bottom) | 16px |
| 阴影 (box-shadow) | `0 1px 2px rgba(0,0,0,0.06)` 默认 |
| 阴影 hover | `0 4px 12px rgba(0,0,0,0.15)` 悬停时 |
| 边框 (border) | `1px solid #F0F0F0` |

---

## 五、组件库规范 (Component Library)

### 5.1 Button 按钮

#### Primary Button（主要操作）
```
┌──────────────────────┐
│      启动 Server      │  ← 高度 36px，padding 0 16px
└──────────────────────┘
  背景: #1677FF        ← 圆角 6px
  文字: #FFFFFF         ← 字号 14px, 字重 500
  hover: #4096FF       ← 阴影加深
  active: #0958D9      ← scale(0.98)
  disabled: #D9D9D9 bg + #FFFFFF text
```

#### Danger Button（危险操作）
```
┌──────────────────────┐
│       停止 Server     │
└──────────────────────┘
  背景: #FF4D4F
  hover: #FF7875
  active: #D9363E
```

#### Ghost Button（次要操作）
```
┌──────────────────────┐
│          重启          │
└──────────────────────┘
  背景: transparent
  边框: 1px solid #D9D9D9
  文字: #1677FF
  hover: 背景填充 #E6F4FF
```

#### Icon Button（图标按钮）
```
  [⚙️]    [🔄]
  尺寸: 32×32px
  圆角: 6px
  hover: #F5F5F5 背景
```

### 5.2 Card 卡片 (AgentCard)

```
┌──────────────────────────────┐
│                              │
│   [🏗️]    Architect           │  ← 第一行：图标(24px) + 名称(H3/Bold)
│                              │
│   ┌──────────┐               │  ← 第二行：StatusBadge
│   │ 🔵 运行中  │               │
│   └──────────┘               │
│                              │
│   ████████████░░░░ 67%       │  ← 第三行：ProgressBar
│                              │
│   编写架构设计文档...         │  ← 第四行：任务名(Caption/截断)
│                              │
└──────────────────────────────┘
  宽度: calc(25% - 12px)      ← 桌面端 4 列
  最小宽度: 200px              ← 响应式下限
  内边距: 16px                 ← space-lg
  圆角: 8px                    ← border-radius
  边框: 2px solid {status}     ← 动态颜色
  transition: all 200ms ease   ← 过渡动画
```

**状态变体**:

Idle 态:
```
┌──────────────────────────────┐
│  [📋]  Product Manager        │
│  ┌──────────┐                │
│  │ ⚪ 空闲    │                │
│  └──────────┘                │
│                              │
└──────────────────────────────┘
  border-color: #D9D9D9
  background: #FAFAFA
  无进度条
```

Running 态:
```
┌──────────────────────────────┐
│  [🏗️]  Architect              │
│  ┌──────────┐                │
│  │ 🔵 运行中  │                │
│  └──────────┘                │
│  ██████████░░░░ 67%          │
│  编写架构设计文档...          │
└──────────────────────────────┘
  border-color: #1890FF
  background: #E6F7FF
  border-left: 4px solid #1890FF  ← 左侧强调条
```

Error 态:
```
┌──────────────────────────────┐
│  ⚠️[🧪] Performance Tester    │
│  ┌──────────┐                │
│  │ 🔴 异常    │                │
│  └──────────┘                │
│  ██████████░░░░ 45%          │
│  ❌ 连接超时，无法获取数据    │
└──────────────────────────────┘
  border-color: #FF4D4F
  background: #FFF2F0
  animation: pulse-border 2s infinite  ← 脉冲动画
```

Complete 态:
```
┌──────────────────────────────┐
│  [✅]  Code Reviewer          │
│  ┌──────────┐                │
│  🟢 已完成                    │
│  └──────────┘                │
│  ██████████████ 100% ✓       │
│  代码审查通过，无 Blocker     │
└──────────────────────────────┘
  border-color: #52C41A
  background: #F6FFED
  左侧强调条: #52C41A
```

### 5.3 StatusBadge 状态徽章

```
┌─────────────┐
│  ● Running   │  ← 高度 22px, padding 0 8px, 圆角 11px (pill shape)
└─────────────┘
  字号: 12px
  字重: 500
  左侧圆点直径: 6px
  圆点右侧间距: 6px
```

**颜色映射**:
| 状态 | 圆点颜色 | 背景色 | 文字颜色 |
|------|---------|--------|---------|
| idle | #D9D9D9 | #F5F5F5 | #8C8C8C |
| running | #1890FF | #E6F7FF | #0958D9 |
| error | #FF4D4F | #FFF2F0 | #CF1322 |
| complete | #52C41A | #F6FFED | #389E0D |

### 5.4 ProgressBar 进度条

```
外框:
  height: 8px                  ← 固定高度
  border-radius: 4px           ← 全圆角
  background: #F0F0F0          ← 轨道色
  overflow: hidden             ← 内容裁剪

内条:
  height: 100%
  border-radius: 4px
  background: linear-gradient(90deg, {start}, {end})  ← 渐变色
  transition: width 300ms ease-out                      ← 平滑过渡

百分比文字:
  position: absolute
  right: -40px (或上方居中)
  font-size: 12px
  color: #595959
  font-weight: 500
```

**渐变色方案**:
| 进度范围 | 渐变起止 | 示意图 |
|---------|---------|--------|
| 0-30% | `#FF4D4F → #FF7875` | 🔴🔴→🔴🟠 |
| 31-70% | `#FAAD14 → #FFC53D` | 🟡🟡→🟡🟡 |
| 71-99% | `#52C41A → #95DE64` | 🟢🟢→🟢💚 |
| 100% | `#1890FF` (纯色+对勾) | 🔵✅ |

### 5.5 LogEntry 日志条目

```
单条日志 (高度自适应):
┌──────────────────────────────────────────────────────────┐
│                                                          │
│ 14:32:15.123  [Architect]  [INFO ]  架构文档已保存到...  │
│ ▓▓▓▓▓▓▓▓▓▓                                               │
│                                                          │
│  ├─ time: 12px, mono, #8C8C8C                           │
│  ├─ agent: 13px, medium, #1677FF (可点击)               │
│  ├─ level: 11px, badge (info=灰底, warn=黄底, error=红底)│
│  └─ message: 13px, regular, #262626                     │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ 底部分割线: 1px solid #F5F5F5                            │
└──────────────────────────────────────────────────────────┘
  padding: 8px 12px                                        ← space-sm ~ space-md
  hover: background #FAFAFA                                ← 微交互
  transition: background 150ms                             ← 过渡动画
```

**ERROR 级别特殊样式**:
```
┌──────────────────────────────────────────────────────────┐
│ █                                                        │  ← 左侧 3px 红色竖线
│ 14:32:10.001  [Frontend]  [ERROR]  TS 类型错误            │
│                                                          │
│ background: #FFF2F0 (浅红背景)                            │
│ left-border: 3px solid #FF4D4F                           │
│ level badge: #FF4D4F bg, white text                      │
└──────────────────────────────────────────────────────────┘
```

### 5.6 MetricCard 指标卡片

```
┌─────────────────────────────────┐
│                                 │
│  📍  当前 Phase                  │  ← 图标(20px) + 标题(Caption/#8C8C8C)
│                                 │
│  Phase 3: Architecture          │  ← 数值(Display/20px/Bold/#262626)
│                                 │
│  ╭────────╮                     │
│  │  65%   │  ← 环形进度图(可选)  │
│  ╰────────╯                     │
│                                 │
└─────────────────────────────────┘
  padding: 16px
  border-radius: 8px
  border: 1px solid #F0F0F0
  box-shadow: 0 1px 2px rgba(0,0,0,0.04)

hover:
  box-shadow: 0 4px 12px rgba(0,0,0,0.08)
  transform: translateY(-2px)
  transition: all 200ms ease-out
```

### 5.7 SearchBar 搜索栏

```
┌─────────────────────────────────────┐
│ 🔍  输入关键词搜索日志...     [×]   │  ← 高度 36px
└─────────────────────────────────────┘
  border-radius: 6px
  border: 1px solid #D9D9D9
  padding: 0 12px
  icon-size: 16px
  placeholder: #BFBFBF

focus:
  border-color: #1677FF
  box-shadow: 0 0 0 2px rgba(22,119,255,0.1)
  outline: none
```

### 5.8 Toast 提示消息

```
成功 Toast:
┌─────────────────────────────────────────────┐
│ ✅  MCP Server 启动成功                   [×] │
│                                             │
│  进程 PID: 12345, 端口: 8000               │
└─────────────────────────────────────────────┘
  background: #F6FFED                          ← 绿底
  border-left: 4px solid #52C41A              ← 左绿条
  icon: #52C41A                               ← 绿勾
  text: #389E0D                                ← 深绿文字
  position: top-right                         ← 右上角
  width: 360px                                ← 固定宽度
  animation: slideInRight 300ms              ← 入场动画
  auto-dismiss: 3000ms                        ← 3秒自动消失

失败 Toast:
  background: #FFF2F0                          ← 红底
  border-left: 4px solid #FF4D4F              ← 左红条
  icon: #FF4D4F                               ← 红叉
  text: #CF1322                                ← 深红文字
  no auto-dismiss (需手动关闭)                 ← 不自动消失
```

### 5.9 Modal 对话框

```
┌─────────────────────────────────────────────┐
│                                             │
│  ⚠️  确认停止                              │  ← Header: H2/16px/Bold
│                                             │
│  即将停止 MCP Server，所有正在运行的         │  ← Body: Body/14px/Regular
│  Agent 将中断。是否继续？                    │
│                                             │
│        [取消]              [确认停止]       │  ← Footer: 按钮
│                                             │
└─────────────────────────────────────────────┘
  width: 480px                                ← 固定宽度
  border-radius: 8px
  padding: 24px
  overlay: rgba(0,0,0,0.45)                  ← 半透明遮罩
  animation: fadeIn + scale(0.95→1)          ← 弹入效果
```

### 5.10 EmptyState 空状态

```
┌─────────────────────────────────────────────┐
│                                             │
│              📝 (48px icon)                 │
│                                             │
│           暂无操作日志                       │  ← H3/14px/Medium/#262626
│                                             │
│      当 Agent 开始执行任务后，              │  ← Caption/12px/#8C8C8C
│      操作日志将在此处实时显示。              │
│                                             │
└─────────────────────────────────────────────┘
  padding: 48px 24px
  text-align: center
  icon opacity: 0.4
```

---

## 六、图标规范 (Iconography)

### 6.1 图标库选择
- **首选**: Ant Design Icons（与 UI 组件库一致）
- **备选**: Lucide Icons（开源、轻量）
- **尺寸**: 16px / 20px / 24px 三档
- **描边**: 1.5px stroke-width（线性图标）

### 6.2 Agent 角色图标映射表

| Agent ID | 显示名称 | 图标 (Ant Design) | Emoji 备用 |
|----------|---------|-------------------|-----------|
| product-manager | Product Manager | `FileTextOutlined` | 📋 |
| requirements | Requirements | `OrderedListOutlined` | 📝 |
| ux-researcher | UX Researcher | `UserSwitchOutlined` | 👥 |
| ui-designer | UI Designer | `BgColorsOutlined` | 🎨 |
| architect | Architect | `ApartmentOutlined` | 🏗️ |
| backend | Backend | `ServerOutlined` | ⚙️ |
| fullstack-coder | Frontend | `CodeOutlined` | 💻 |
| bug-defect-repairer | Bug Fixer | `BugOutlined` | 🐛 |
| code-reviewer | Code Reviewer | `SafetyCertificateOutlined` | ✅ |
| performance | Performance | `ThunderboltOutlined` | ⚡ |
| tester | Tester | `ExperimentOutlined` | 🧪 |
| documenter | Documenter | `FileOutlined` | 📄 |
| final-reviewer | Final Reviewer | `AuditOutlined` | 🔍 |
| devops | DevOps | `CloudServerOutlined` | ☁️ |
| knowledge-curator | Knowledge Curator | `BookOutlined` | 📚 |
| orchestrator | Orchestrator | `ControlOutlined` | 🎯 |

---

## 七、动效规范 (Motion & Animation)

### 7.1 全局缓动曲线 (Easing)

| 名称 | CSS 值 | 使用场景 |
|------|--------|---------|
| `ease-out` | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | 进入动画、展开 |
| `ease-in` | `cubic-bezier(0.55, 0.085, 0.68, 0.53)` | 退出动画、收起 |
| `ease-in-out` | `cubic-bezier(0.42, 0, 0.58, 1)` | 状态切换 |
| `spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 弹性反馈（按钮点击） |

### 7.2 关键动画定义

#### AgentCard Error Pulse（脉冲）
```css
@keyframes pulse-border {
  0%, 100% {
    border-color: #FF4D4F;
    box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.4);
  }
  50% {
    border-color: #FF7875;
    box-shadow: 0 0 0 4px rgba(255, 77, 79, 0);
  }
}
/* 应用于: .agent-card.status-error */
animation: pulse-border 2s ease-in-out infinite;
```

#### Skeleton Shimmer（骨架屏扫光）
```css
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
.skeleton {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e8e8e8 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
```

#### Progress Bar Grow（进度增长）
```css
.progress-bar-fill {
  transition: width 300ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
```

#### Toast Slide In（提示滑入）
```css
@keyframes toast-slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
.toast-enter {
  animation: toast-slide-in 300ms cubic-bezier(0.21, 1.02, 0.73, 1);
}
```

#### Number CountUp（数字滚动）
```javascript
// 使用 react-countup 或自实现
// duration: 500ms
// easing: easeOutQuart
// separator: ','
```

### 7.3 减少动效偏好 (Reduced Motion)
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 八、响应式设计断点详情

### 8.1 断点与布局变化

| 断点 | Agent 矩阵 | 仪表盘 | 日志区 | 进度区 |
|------|-----------|--------|--------|--------|
| **< 480px** | 2列 × 8行 | 折叠卡片 | 全宽 | Top 3 |
| **480-767px** | 2列 × 8行 | 折叠卡片 | 全宽 | Top 3 |
| **768-1023px** | 4列 × 4行 | 2列网格 | 全宽 | Top 5 |
| **1024-1439px** | 4列 × 4行 | 2列网格 | 55%宽 | 45%宽 |
| **≥ 1440px** | 4列 × 4行宽松 | 2列网格宽松 | 55%宽 | 45%宽 |

### 8.2 移动端特殊处理

- Agent 卡片最小宽度: 140px
- 卡片内省略进度条和任务描述
- 日志区固定显示最近 20 条
- 搜索栏置顶 sticky
- 控制按钮横排排列

---

## 九、深色模式适配 (Dark Mode)

### 9.1 CSS 变量切换策略

```css
:root {
  /* Light Mode (Default) */
  --bg-page: #FFFFFF;
  --bg-card: #FAFAFA;
  --border-card: #F0F0F0;
  --text-primary: #262626;
  --text-secondary: #8C8C8C;
}

[data-theme='dark'] {
  /* Dark Mode */
  --bg-page: #141414;
  --bg-card: #1F1F1F;
  --border-card: #303030;
  --text-primary: #E8E8E8;
  --text-secondary: #A6A6A6;
}
```

### 9.2 深色模式特殊调整
- 阴影减弱：`box-shadow: 0 1px 2px rgba(0,0,0,0.2)`
- 卡片边框加深：`border-color: #303030`
- 输入框背景：`#262626`
- 代码块背景：`#1A1A1A`
- 图表配色：提高饱和度和亮度

---

## 十、设计交付物清单

### M1 必需交付物
- [x] 本设计规范文档 (UI-Design.md)
- [x] 色彩系统定义（CSS 变量文件）
- [x] 组件规格说明书（§5 所有组件）
- [x] 响应式断点定义（§8）
- [ ] Tailwind 配置文件（tailwind.config.js 扩展）
- [ ] 全局样式变量文件（styles/globals.css）

### M2 可选交付物
- Figma/Sketch 高保真原型
- 交互动效演示视频
- 移动端独立设计稿
- 深色模式完整截图

---

## 十一、验收标准 (UI)

| # | 验收项 | 标准 | 检查方式 |
|---|--------|------|---------|
| UI-001 | 色彩对比度 | 正文 ≥ 4.5:1 (AA) | Chrome DevTools |
| UI-002 | 组件一致性 | 同类组件样式完全一致 | 视觉走查 |
| UI-003 | 响应式正确 | 5 个断点均无布局崩坏 | 设备模拟器 |
| UI-004 | 动效流畅 | 所有动画 ≥ 60fps | Chrome Performance |
| UI-005 | 深色模式完整 | 所有页面支持深色切换 | 手动测试 |
| UI-006 | 字体渲染清晰 | 中英文混排无异常 | 多浏览器测试 |
| UI-007 | 图标统一 | 仅使用规定图标库 | 代码审查 |

---

**[NOTIFY] 本文档由 @UI-Designer 在第5阶段产出，总控验收通过后流转至开发实现**
