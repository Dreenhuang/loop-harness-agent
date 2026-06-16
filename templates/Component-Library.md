# Component-Library · 组件库文档

> **工件类型**：强制工件
> **所属 Phase**：Phase 3
> **责任角色**：@UI-Designer / @Fullstack-Coder
> **状态**：⏳ PENDING → 🔄 IN_PROGRESS → ✅ COMPLETED
> **融合验收标准**：g:\ai-gongju\Loop-agent\docs\integration\融合验收标准.md

| 字段 | 值 |
|------|-----|
| **文档版本** | v1.0 |
| **创建日期** | YYYY-MM-DD |
| **最后更新** | YYYY-MM-DD |
| **作者** | @Fullstack-Coder |
| **审核者** | @UI-Designer / @Code-Reviewer |
| **关联工件** | UI-Design.md / Design-Brief.md |

---

## 1. 组件清单

<!-- 填写指引：列出所有组件，按类型分组，标注优先级、状态和实现位置。 -->

### 1.1 基础组件（Atoms）

| 编号 | 组件名称 | 文件路径 | 优先级 | 实现状态 | 依赖 |
|------|----------|----------|--------|----------|------|
| CMP-001 | Button | `src/components/ui/Button.tsx` | P0 | ⏳ | — |
| CMP-002 | Input | `src/components/ui/Input.tsx` | P0 | ⏳ | — |
| CMP-003 | Select | `src/components/ui/Select.tsx` | P0 | ⏳ | — |
| CMP-004 | Checkbox | `src/components/ui/Checkbox.tsx` | P1 | ⏳ | — |
| CMP-005 | Radio | `src/components/ui/Radio.tsx` | P1 | ⏳ | — |
| CMP-006 | Switch | `src/components/ui/Switch.tsx` | P1 | ⏳ | — |
| CMP-007 | Tag | `src/components/ui/Tag.tsx` | P1 | ⏳ | — |
| CMP-008 | Badge | `src/components/ui/Badge.tsx` | P2 | ⏳ | — |
| CMP-009 | Avatar | `src/components/ui/Avatar.tsx` | P1 | ⏳ | — |
| CMP-010 | Icon | `src/components/ui/Icon.tsx` | P0 | ⏳ | — |
| CMP-011 | Spinner | `src/components/ui/Spinner.tsx` | P0 | ⏳ | — |
| CMP-012 | Tooltip | `src/components/ui/Tooltip.tsx` | P2 | ⏳ | — |

### 1.2 复合组件（Molecules）

| 编号 | 组件名称 | 文件路径 | 优先级 | 实现状态 | 包含基础组件 |
|------|----------|----------|--------|----------|-------------|
| CMP-013 | Card | `src/components/ui/Card.tsx` | P0 | ⏳ | Avatar/Tag/Button |
| CMP-014 | Modal | `src/components/ui/Modal.tsx` | P0 | ⏳ | Button/Icon |
| CMP-015 | Drawer | `src/components/ui/Drawer.tsx` | P1 | ⏳ | Button/Icon |
| CMP-016 | Dropdown | `src/components/ui/Dropdown.tsx` | P1 | ⏳ | Button/Icon |
| CMP-017 | Toast | `src/components/ui/Toast.tsx` | P0 | ⏳ | Icon/Button |
| CMP-018 | Alert | `src/components/ui/Alert.tsx` | P1 | ⏳ | Icon/Button |
| CMP-019 | Tabs | `src/components/ui/Tabs.tsx` | P1 | ⏳ | Icon |
| CMP-020 | Breadcrumb | `src/components/ui/Breadcrumb.tsx` | P2 | ⏳ | Icon |

### 1.3 业务组件（Organisms）

| 编号 | 组件名称 | 文件路径 | 优先级 | 实现状态 | 包含组件 |
|------|----------|----------|--------|----------|----------|
| CMP-021 | Navigation | `src/components/Navigation.tsx` | P0 | ⏳ | Icon/Button/Dropdown |
| CMP-022 | DataTable | `src/components/DataTable.tsx` | P0 | ⏳ | Button/Input/Tag/Spinner |
| CMP-023 | Form | `src/components/Form.tsx` | P0 | ⏳ | Input/Select/Button/Checkbox |
| CMP-024 | SearchBar | `src/components/SearchBar.tsx` | P1 | ⏳ | Input/Button/Icon |
| CMP-025 | FileUpload | `src/components/FileUpload.tsx` | P1 | ⏳ | Button/Icon/Spinner |

---

## 2. 组件 API

<!-- 填写指引：为每个组件定义 Props 接口，包含属性名、类型、默认值、是否必填和描述。 -->

### 2.1 Button API

```typescript
interface ButtonProps {
  /** 按钮变体 */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  /** 按钮尺寸 */
  size?: 'small' | 'medium' | 'large';
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否加载中 */
  loading?: boolean;
  /** 是否占满宽度 */
  fullWidth?: boolean;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 点击事件 */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** 子元素 */
  children: React.ReactNode;
}
```

**默认值**：

| 属性 | 默认值 |
|------|--------|
| variant | 'primary' |
| size | 'medium' |
| disabled | false |
| loading | false |
| fullWidth | false |

### 2.2 Input API

```typescript
interface InputProps {
  /** 输入类型 */
  type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'url';
  /** 输入值 */
  value?: string;
  /** 占位文本 */
  placeholder?: string;
  /** 标签文本 */
  label?: string;
  /** 辅助文本 */
  helperText?: string;
  /** 错误信息 */
  error?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否只读 */
  readOnly?: boolean;
  /** 是否必填 */
  required?: boolean;
  /** 最大长度 */
  maxLength?: number;
  /** 前缀图标 */
  prefixIcon?: React.ReactNode;
  /** 后缀图标 */
  suffixIcon?: React.ReactNode;
  /** 值变更回调 */
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  /** 聚焦回调 */
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  /** 失焦回调 */
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
}
```

### 2.3 Modal API

```typescript
interface ModalProps {
  /** 是否打开 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 标题 */
  title: string;
  /** 尺寸 */
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  /** 是否显示关闭按钮 */
  showCloseButton?: boolean;
  /** 点击遮罩是否关闭 */
  closeOnOverlayClick?: boolean;
  /** 按 ESC 是否关闭 */
  closeOnEsc?: boolean;
  /** 底部操作区 */
  footer?: React.ReactNode;
  /** 子元素 */
  children: React.ReactNode;
}
```

### 2.4 [组件名称] API

<!-- 按相同格式补充其他组件 -->

---

## 3. 组件状态

<!-- 填写指引：定义每个组件的所有视觉状态和状态转换逻辑。 -->

### 3.1 通用状态矩阵

| 状态 | 视觉表现 | 交互行为 | 适用组件 |
|------|----------|----------|----------|
| Default | 默认样式 | 正常交互 | 所有 |
| Hover | 背景色变化 | cursor: pointer | Button/Card/Link |
| Active/Pressed | 按压态 | 触发 onClick | Button/Card |
| Focus | outline 显示 | 键盘可达 | Button/Input/Select |
| Disabled | opacity: 0.5 | 不可交互 | Button/Input/Select |
| Loading | Spinner 替换内容 | 不可交互 | Button/Table |
| Error | 红色边框 + 错误文案 | 显示错误信息 | Input/Select/Form |
| Success | 绿色边框/图标 | 确认成功 | Input/Form |
| Empty | 空状态插图 | 引导操作 | Table/List/Card |

### 3.2 状态转换规则

```
Default ──(hover)──→ Hover ──(leave)──→ Default
Default ──(focus)──→ Focus ──(blur)──→ Default
Default ──(press)──→ Active ──(release)──→ Hover
Default ──(disable)──→ Disabled ──(enable)──→ Default
Default ──(submit)──→ Loading ──(success)──→ Default
Loading ──(error)──→ Error ──(retry)──→ Loading
```

---

## 4. 组件组合规则

<!-- 填写指引：定义组件之间的组合约束和推荐模式。 -->

### 4.1 组合约束

| 规则 | 说明 | 示例 |
|------|------|------|
| 禁止嵌套 Modal | Modal 内不得再打开 Modal | ❌ Modal > Modal |
| 禁止嵌套 Button | Button 不得作为 Button 子元素 | ❌ Button > Button |
| Toast 互斥 | 同一时刻只显示一条 Toast | ✅ Toast 队列 |
| 表单校验层级 | 校验在 Form 层统一处理 | ✅ Form > Input + error |
| 下拉菜单层级 | Dropdown 使用 Portal 渲染 | ✅ Dropdown > Portal |

### 4.2 推荐组合模式

#### 模式 1：表单组合

```
Form
  ├── FormField (label + error)
  │   └── Input
  ├── FormField
  │   └── Select
  ├── FormField
  │   └── Checkbox
  └── Button (type="submit")
```

#### 模式 2：数据展示组合

```
DataTable
  ├── SearchBar
  │   ├── Input (type="search")
  │   └── Button (filter)
  ├── Table
  │   ├── Thead > Th[]
  │   └── Tbody > Tr[] > Td[]
  └── Pagination
      └── Button[]
```

#### 模式 3：确认操作组合

```
Modal (danger)
  ├── Icon (warning)
  ├── Title ("确认删除？")
  ├── Description ("此操作不可撤销")
  └── Footer
      ├── Button (variant="ghost") "取消"
      └── Button (variant="danger") "确认删除"
```

---

## 5. 组件测试要求

<!-- 填写指引：定义每个组件的测试标准，包括测试类型和覆盖率要求。 -->

### 5.1 测试类型

| 测试类型 | 工具 | 覆盖率要求 | 说明 |
|----------|------|-----------|------|
| 单元测试 | Vitest / Jest | ≥ 80% | Props/状态/事件 |
| 快照测试 | Vitest | 100% | 每个变体/状态 |
| 可访问性测试 | axe-core | 100% | WCAG AA |
| 交互测试 | Testing Library | 关键路径 | 用户操作流程 |
| 视觉回归测试 | Chromatic / Percy | P0 组件 | 截图对比 |

### 5.2 测试清单（每个组件必测）

- [ ] **渲染测试**：默认 Props 正常渲染
- [ ] **变体测试**：所有 variant 正确渲染
- [ ] **尺寸测试**：所有 size 正确渲染
- [ ] **状态测试**：disabled/loading/error 状态正确
- [ ] **事件测试**：onClick/onChange/onFocus/onBlur 触发
- [ ] **可访问性测试**：键盘可达、ARIA 属性正确
- [ ] **快照测试**：无意外 UI 变更
- [ ] **边界测试**：长文本/空值/极端值

### 5.3 测试模板

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  // 渲染测试
  it('renders with default props', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  // 变体测试
  it.each(['primary', 'secondary', 'ghost', 'danger'] as const)(
    'renders %s variant',
    (variant) => {
      render(<Button variant={variant}>Test</Button>);
      expect(screen.getByRole('button')).toHaveClass(`btn-${variant}`);
    }
  );

  // 状态测试
  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Test</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  // 事件测试
  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Test</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  // 可访问性测试
  it('is accessible', async () => {
    const { container } = render(<Button>Test</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

---

## 附录

### A. 组件依赖关系图

```
Atoms (基础组件)
  └── Molecules (复合组件)
        └── Organisms (业务组件)
              └── Pages (页面)
```

### B. 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| YYYY-MM-DD | v1.0 | 初始版本 | @Fullstack-Coder |
