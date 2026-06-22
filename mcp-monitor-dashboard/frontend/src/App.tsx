/**
 * Root App Component
 */

import React from 'react';
import { ConfigProvider, App as AntdApp, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Dashboard from '@/pages/Dashboard';
import { NotificationProvider } from '@/components/feedback';
import './styles/globals.css';

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677FF',
          borderRadius: 6,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
        },
        components: {
          Card: {
            borderRadiusLG: 8,
          },
        },
      }}
    >
      <AntdApp>
        <NotificationProvider>
          <Dashboard />
        </NotificationProvider>
      </AntdApp>
    </ConfigProvider>
  );
};

export default App;
