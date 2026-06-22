# 前端控制台日志修复手册

> **类型**：问题解决经验
> **适用项目**：MCP Monitor Dashboard 及同类 React + Vite + Ant Design 前端项目
> **创建时间**：2026-06-20

---

## 一、问题场景

浏览器控制台同时出现多条 error/warning，常见组合如下：

1. `net::ERR_ABORTED http://localhost:3000/` / `net::ERR_CONNECTION_REFUSED http://localhost:3000/`
2. `Warning: findDOMNode is deprecated...`
3. `Warning: [antd: message] Static function can not consume context...`
4. `❌ WebSocket error:`
5. `API Error: AxiosError: Network Error`
6. `Failed to load system status: AxiosError: Network Error`

---

## 二、根因与修复方案

### 1. Vite dev server 代理链路中断

**根因**：
- 后端 Uvicorn `--reload` 重启期间，Vite 的 `/api` 与 `/ws` 代理会短暂失效。
- 前端 WebSocket 默认使用 `ws://${window.location.host}/ws`，先连 Vite 再代理到后端，Vite 不稳定时会被拒绝。

**修复**：
- 开发环境新增 `frontend/.env.development`：
  ```env
  VITE_WS_URL=ws://localhost:8000/ws
  ```
- 前端 `useWebSocket.ts` 优先读取 `import.meta.env.VITE_WS_URL`，让 WebSocket 直连后端。
- 生产环境移除 Uvicorn `--reload`，使用多 worker 模式。

### 2. Ant Design `message` 静态方法警告

**根因**：`message.success()` / `message.warning()` / `message.error()` 等静态方法无法消费 `ConfigProvider` 的动态主题上下文。

**修复**：
- 在 `App.tsx` 中用 `<App>` 组件包裹应用：
  ```tsx
  import { ConfigProvider, App as AntdApp } from 'antd';
  <ConfigProvider ...>
    <AntdApp>
      <Dashboard />
    </AntdApp>
  </ConfigProvider>
  ```
- 在业务组件中使用 `const { message } = App.useApp();` 获取 message 实例。

### 3. `findDOMNode is deprecated` 警告

**根因**：Ant Design `Tooltip` / `ResizeObserver` 等组件需要直接操作 DOM，如果直接子元素是无法转发 ref 的组件（如 `Badge` 在某些版本），会触发 `findDOMNode` 回退。

**修复**：
- 将 `Tooltip` 的直接子元素改为原生 DOM 节点，或用 `React.forwardRef` 包装自定义子组件。
- 示例：
  ```tsx
  <Tooltip title="提示">
    <span><Badge ... /></span>
  </Tooltip>
  ```

### 4. WebSocket 首次连接 `onerror` 红色日志

**根因**：
- React 组件挂载时浏览器事件循环、Vite HMR WebSocket 与业务 WebSocket 同时初始化，导致首次握手被异常中断（code 1006）。
- 后端 `accept()` 阶段若发生异常被静默吞掉，也会触发前端 `onerror`。

**修复（前端）**：
- 延迟首次连接时机，等待 `document.readyState === 'complete'`。
- 对首次连接的瞬时错误降级为 `console.log`，避免红色错误刷屏。

**修复（后端）**：
- `await websocket.accept()` 不应放在锁内，避免锁竞争影响握手。
- 对 `accept()` 与首次 `send_json` 增加显式异常捕获与日志。
- 对缓存数据做防御性类型转换，避免空缓存导致序列化失败。

### 5. Axios 网络错误刷屏

**根因**：响应拦截器中直接 `console.error(error)` 打印整个错误对象；轮询接口失败时每次都会打印。

**修复**：
- 在 `services/index.ts` 拦截器中分类处理：
  - `ERR_NETWORK` / `Network Error`：使用 `console.warn` 输出简洁提示。
  - 业务错误：仅输出状态码和后台 message。
- 在轮询函数中对网络错误做静默/降频处理，首次失败后不再每次打印。

---

## 三、验证清单

修复后必须执行：

- [ ] `npm run build` 通过，无 TypeScript 错误。
- [ ] 浏览器控制台 15 秒内无 error / warning。
- [ ] WebSocket 正常连接、订阅、接收消息。
- [ ] 后端测试套件全部通过。

---

## 四、预防建议

1. 新建 Ant Design 项目时，根组件统一用 `<App>` 包裹，业务组件统一用 `App.useApp()`。
2. `Tooltip` / `Popover` 等需要 ref 的组件，子元素优先使用原生 DOM 节点。
3. WebSocket 连接地址优先使用环境变量配置，开发环境直连后端，生产环境使用独立域名/wss。
4. Axios 拦截器统一封装错误分类逻辑，避免在轮询场景打印整个错误对象。
5. 后端 WebSocket 握手阶段避免加锁、避免 accept 后立即发送大数据包、增加异常捕获。
