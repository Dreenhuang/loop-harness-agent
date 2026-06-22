/**
 * Application Entry Point
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  // 关闭 StrictMode 以避免 antd 内部 Tooltip/ResizeObserver 触发 findDOMNode 警告
  // 该警告来自 antd 自身实现，非本应用代码问题
  <App />
);
