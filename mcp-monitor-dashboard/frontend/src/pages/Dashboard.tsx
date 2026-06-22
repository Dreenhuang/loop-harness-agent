/**
 * Dashboard Page - Main monitoring dashboard
 */

import React, { useEffect, useState, useRef } from 'react';
import {
  Card,
  Button,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  Progress,
  Input,
  Select,
  Badge,
  Spin,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  SearchOutlined,
  FilterOutlined,
  ClearOutlined,
  WifiOutlined,
  DisconnectOutlined,
  LoadingOutlined,
} from '@ant-design/icons';

import AgentCard from '@/components/ui/AgentCard';
import LogEntryComponent from '@/components/ui/LogEntry';
import { FeedbackSettings } from '@/components/feedback';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAgentStore } from '@/store/agentStore';
import { useLogStore } from '@/store/logStore';
import { useProjectStore } from '@/store/projectStore';
import { useNotification } from '@/hooks/useNotification';
import type { WSMessage, Agent, LogEntry, ProjectOverview, SystemStatus } from '@/types';
import services from '@/services';
const { agentService, logService, projectService, systemService } = services;
import './Dashboard.css';

const Dashboard: React.FC = () => {
  // State
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [logLevelFilter, setLogLevelFilter] = useState<string[]>([]);
  const [lastUpdateTime, setLastUpdateTime] = useState<string>('-');
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [isRealtimePaused, setIsRealtimePaused] = useState(false);
  const isRealtimePausedRef = useRef(isRealtimePaused);
  useEffect(() => {
    isRealtimePausedRef.current = isRealtimePaused;
  }, [isRealtimePaused]);

  // Stores
  const { agents, setAgents, updateAgent } = useAgentStore();
  const { logs, setLogs, prependLog } = useLogStore();
  const { overview, setOverview } = useProjectStore();

  // Notification system
  const { notify, success, warning, error, info, dedup, withLoading } = useNotification();

  // Refs for auto-scroll
  const logContainerRef = useRef<HTMLDivElement>(null);
  const isAutoScrollRef = useRef(true);

  // Refs for toast deduplication
  const hasShownDisconnectRef = useRef(false);
  const hasShownConnectRef = useRef(false);

  // Track token threshold warning state
  const tokenWarningSentRef = useRef(false);

  // WebSocket connection
  const { isConnected, subscribe, requestFullSync } = useWebSocket({
    onMessage: handleWSMessage,
    onOpen: () => {
      if (!hasShownConnectRef.current) {
        success('实时连接已建立');
        hasShownConnectRef.current = true;
        hasShownDisconnectRef.current = false;
      }
      subscribe(['agent_status', 'logs', 'overview']);
    },
    onClose: () => {
      if (!hasShownDisconnectRef.current) {
        warning('连接已断开，正在重连...');
        hasShownDisconnectRef.current = true;
        hasShownConnectRef.current = false;
      }
    },
    onError: () => {
      dedup('ws-error', 'error', '实时连接发生错误，正在尝试恢复', 10000);
    },
  });

  // Subscribe to global feedback events from services / websocket
  useEffect(() => {
    const handleFeedback = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (!detail) return;

      switch (detail.type) {
        // ws-connected 已在 useWebSocket onOpen 中通过 Dashboard 本地状态提示，避免重复
        case 'ws-disconnected':
          warning(detail.message);
          break;
        case 'ws-error':
          error(detail.message);
          break;
        case 'api-error':
          error(detail.message);
          break;
        default:
          info(detail.message);
      }
    };

    window.addEventListener('mcp-feedback', handleFeedback);
    window.addEventListener('mcp-api-error', handleFeedback);

    return () => {
      window.removeEventListener('mcp-feedback', handleFeedback);
      window.removeEventListener('mcp-api-error', handleFeedback);
    };
  }, [success, warning, error, info]);

  // Handle incoming WebSocket messages with data validation
  function handleWSMessage(msg: WSMessage) {
    // Validate message has required fields
    if (!msg.type || typeof msg.type !== 'string') {
      console.warn('Invalid WS message: missing type');
      return;
    }

    // Respect realtime pause state
    if (isRealtimePausedRef.current && ['agent_status_update', 'project_overview_update', 'log_entry'].includes(msg.type)) {
      return;
    }

    switch (msg.type) {
      case 'init': {
        // Initial data load
        const initData = msg.data as any;
        if (initData && Array.isArray(initData.agents)) {
          const validAgents = initData.agents.filter(
            (a: unknown) => a && typeof a === 'object' && 'id' in a && 'status' in a
          );
          setAgents(validAgents as Agent[]);
        }
        if (initData?.overview && typeof initData.overview === 'object') {
          setOverview(initData.overview as ProjectOverview);
        }
        break;
      }

      case 'agent_status_update':
        if (Array.isArray(msg.data)) {
          (msg.data as Agent[]).forEach((agent: Agent) => {
            if (agent?.id && agent?.status) {
              updateAgent(agent.id, agent);
            }
          });
        }
        break;

      case 'project_overview_update':
        if (msg.data && typeof msg.data === 'object' && 'name' in msg.data) {
          setOverview(msg.data as unknown as ProjectOverview);
        }
        break;

      case 'log_entry':
        if (msg.data && typeof msg.data === 'object' && 'id' in msg.data && 'message' in msg.data) {
          prependLog(msg.data as LogEntry);
          scrollToBottomIfNear();
        }
        break;

      default:
        break;
    }

    if (msg.timestamp) {
      setLastUpdateTime(new Date(msg.timestamp).toLocaleTimeString('zh-CN'));
    }
  }

  // Monitor token threshold and emit warning once per crossing
  useEffect(() => {
    const percentage = overview?.token_budget?.percentage ?? 0;
    if (percentage >= 85) {
      if (!tokenWarningSentRef.current) {
        tokenWarningSentRef.current = true;
        warning(`Token 用量已达 ${percentage.toFixed(1)}%，请关注预算消耗`, {
          duration: 0,
        });
      }
    } else {
      tokenWarningSentRef.current = false;
    }
  }, [overview?.token_budget?.percentage, warning]);

  // Load initial data via REST API
  async function loadInitialData() {
    try {
      await withLoading(
        Promise.all([
          agentService.getAll(),
          logService.getLogs({ page_size: 100 }),
          projectService.getOverview(),
        ]).then(([agentsRes, logsRes, projectRes]) => {
          setAgents(agentsRes.data || []);
          setLogs(logsRes.data?.items || [], logsRes.data?.total || 0);
          if (projectRes.data) {
            setOverview(projectRes.data);
          }
        }),
        {
          loading: '正在加载仪表盘数据...',
          success: '仪表盘数据加载完成',
          error: (err) => `加载数据失败：${(err as Error)?.message || '请稍后重试'}`,
        }
      );
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      setIsInitialLoading(false);
    }
  }

  async function loadSystemStatus() {
    try {
      const res = await systemService.getStatus();
      if (res.data) {
        setSystemStatus(res.data);
      }
    } catch (error) {
      console.error('Failed to load system status:', error);
      // 静默失败，避免轮询时刷屏；首次加载已在 loadInitialData 中提示
    }
  }

  useEffect(() => {
    loadInitialData();
    loadSystemStatus();

    // Poll system status every 10s
    const interval = setInterval(loadSystemStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  // System control handlers
  async function handleStart() {
    setLoadingAction('start');
    try {
      await withLoading(systemService.start(), {
        loading: '正在启动 MCP Server...',
        success: 'MCP Server 启动成功',
        error: 'MCP Server 启动失败',
      });
      await loadSystemStatus();
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleStop() {
    setLoadingAction('stop');
    try {
      await withLoading(systemService.stop(), {
        loading: '正在停止 MCP Server...',
        success: 'MCP Server 已停止',
        error: 'MCP Server 停止失败',
      });
      await loadSystemStatus();
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleRestart() {
    setLoadingAction('restart');
    try {
      await withLoading(systemService.restart(), {
        loading: '正在重启 MCP Server...',
        success: 'MCP Server 重启成功',
        error: 'MCP Server 重启失败',
      });
      await loadSystemStatus();
    } finally {
      setLoadingAction(null);
    }
  }

  // Realtime pause/resume toggle
  function handleToggleRealtime() {
    setIsRealtimePaused((prev) => {
      const next = !prev;
      if (next) {
        info('已暂停实时推送，页面将不再自动更新');
      } else {
        success('已恢复实时推送');
        requestFullSync?.();
      }
      return next;
    });
  }

  // Log search handler
  async function handleSearch(value: string) {
    setSearchKeyword(value);
    try {
      info(`正在搜索：${value || '全部日志'}`);
      const res = await logService.getLogs({ keyword: value });
      setLogs(res.data?.items || [], res.data?.total || 0);
      success(`找到 ${res.data?.total || 0} 条日志`);
    } catch (searchError) {
      console.error('Search failed:', searchError);
      notify({ type: 'error', message: '日志搜索失败' });
    }
  }

  // Log level filter handler
  function handleLevelFilterChange(levels: string[]) {
    setLogLevelFilter(levels);
    info(levels.length > 0 ? `已应用 ${levels.length} 个日志级别筛选` : '已清除日志级别筛选');
  }

  // Auto-scroll logic
  function scrollToBottomIfNear() {
    if (!logContainerRef.current || !isAutoScrollRef.current) return;

    const container = logContainerRef.current;
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;

    if (distanceFromBottom < 100) {
      container.scrollTop = container.scrollHeight;
    }
  }

  // Gate status component
  function renderGateBadge(status: string) {
    const config = {
      passed: { color: 'green', icon: '✅' },
      pending: { color: 'default', icon: '⬜' },
      failed: { color: 'red', icon: '❌' },
    };
    const gateConfig = config[status as keyof typeof config] || config.pending;
    return (
      <Tag color={gateConfig.color}>
        {gateConfig.icon}
      </Tag>
    );
  }

  // Get MCP server status display
  const mcpRunning = systemStatus?.mcp_server?.status === 'running';

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <span className="logo">📊</span>
          <h1 className="title">MCP Monitor Dashboard</h1>
        </div>

        <div className="header-right">
          {/* Status Indicator */}
          <span title={`MCP Server: ${mcpRunning ? '运行中' : '已停止'}`}>
            <Badge status={mcpRunning ? 'success' : 'default'} />
          </span>

          {/* Control Buttons */}
          <Space size="small">
            <Button
              type="primary"
              icon={loadingAction === 'start' ? <LoadingOutlined /> : <PlayCircleOutlined />}
              onClick={handleStart}
              disabled={mcpRunning || loadingAction !== null}
              size="small"
            >
              启动
            </Button>

            <Button
              danger
              icon={loadingAction === 'stop' ? <LoadingOutlined /> : <PauseCircleOutlined />}
              onClick={handleStop}
              disabled={!mcpRunning || loadingAction !== null}
              size="small"
            >
              停止
            </Button>

            <Button
              icon={loadingAction === 'restart' ? <LoadingOutlined /> : <ReloadOutlined />}
              onClick={handleRestart}
              disabled={loadingAction !== null}
              size="small"
            >
              重启
            </Button>

            <Button
              icon={isRealtimePaused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
              onClick={handleToggleRealtime}
              size="small"
            >
              {isRealtimePaused ? '恢复' : '暂停'}
            </Button>
          </Space>

          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => setSettingsVisible(true)}
            aria-label="打开提示设置"
          >
            设置
          </Button>
        </div>
      </header>

      {/* Main Content - Four Quadrant Layout */}
      <main className="dashboard-main">
        <Spin
          spinning={isInitialLoading}
          tip="正在加载仪表盘数据..."
          size="large"
          style={{ width: '100%' }}
        >
        <Row gutter={[16, 16]}>
          {/* Left Column */}
          <Col xs={24} lg={12}>
            {/* Agent Status Matrix */}
            <Card
              title={
                <Space>
                  <span>🤖 Agent 状态矩阵</span>
                  <Tag>共 {agents.length} 个</Tag>
                </Space>
              }
              className="section-card"
              size="small"
            >
              <div className="agent-grid">
                {agents.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
              </div>
            </Card>

            {/* Operation Log Stream */}
            <Card
              title={
                <Space>
                  <span>📝 操作日志流</span>
                  <Tag>{logs.length} 条</Tag>
                </Space>
              }
              className="section-card"
              size="small"
              extra={
                <Space size="small">
                  <Select
                    mode="multiple"
                    allowClear
                    placeholder={<><FilterOutlined /> 级别</>}
                    size="small"
                    style={{ minWidth: 120 }}
                    value={logLevelFilter}
                    onChange={handleLevelFilterChange}
                    options={[
                      { label: 'INFO', value: 'info' },
                      { label: 'WARN', value: 'warning' },
                      { label: 'ERROR', value: 'error' },
                      { label: 'DEBUG', value: 'debug' },
                    ]}
                  />
                  <Input
                    placeholder="搜索日志..."
                    prefix={<SearchOutlined />}
                    allowClear
                    size="small"
                    style={{ width: 180 }}
                    onChange={(e) => handleSearch(e.target.value)}
                    value={searchKeyword}
                  />
                  <Button
                    icon={<ClearOutlined />}
                    size="small"
                    onClick={() => {
                      setSearchKeyword('');
                      setLogLevelFilter([]);
                      handleSearch('');
                      info('已清除日志搜索和筛选');
                    }}
                    aria-label="清除搜索和筛选"
                  />
                </Space>
              }
            >
              <div className="log-container" ref={logContainerRef}>
                {logs.length > 0 ? (
                  logs.map((log) => (
                    <LogEntryComponent key={`${log.id}-${log.timestamp}`} log={log} />
                  ))
                ) : (
                  <div className="empty-logs" role="status" aria-live="polite">
                    <p>📝 暂无操作日志</p>
                    <p className="hint">当 Agent 开始执行任务后，操作日志将在此处实时显示。</p>
                  </div>
                )}
              </div>
            </Card>
          </Col>

          {/* Right Column */}
          <Col xs={24} lg={12}>
            {/* Project Overview Dashboard */}
            <Card
              title="📊 项目全景仪表盘"
              className="section-card"
              size="small"
            >
              <Row gutter={[16, 12]}>
                {/* Current Phase */}
                <Col span={24}>
                  <Statistic
                    title="当前 Phase"
                    value={overview?.current_phase || '-'}
                    prefix="📍"
                  />
                  <Progress
                    percent={Math.round(overview?.phase_progress || 0)}
                    strokeColor="#1677FF"
                    style={{ marginTop: 8 }}
                  />
                </Col>

                {/* Task Stats */}
                <Col span={12}>
                  <Statistic
                    title="任务完成率"
                    value={overview?.tasks?.completed || 0}
                    suffix={`/ ${overview?.tasks?.total || 0}`}
                    prefix="📋"
                    valueStyle={{ color: '#52C41A' }}
                  />
                </Col>

                {/* Token Budget */}
                <Col span={12}>
                  <Statistic
                    title="Token 预算"
                    value={overview?.token_budget?.percentage || 0}
                    suffix="%"
                    prefix="💰"
                    valueStyle={{
                      color:
                        (overview?.token_budget?.percentage || 0) > 90
                          ? '#FF4D4F'
                          : '#FAAD14',
                    }}
                  />
                  <Progress
                    percent={Math.round(overview?.token_budget?.percentage || 0)}
                    size="small"
                    showInfo={false}
                    strokeColor={
                      (overview?.token_budget?.percentage || 0) > 90
                        ? '#FF4D4F'
                        : undefined
                    }
                  />
                </Col>

                {/* Agent Distribution */}
                <Col span={12}>
                  <Statistic
                    title="活跃 Agent"
                    value={overview?.agents?.active || 0}
                    suffix={`/ ${overview?.agents?.total || 0}`}
                    prefix="👥"
                    valueStyle={{ color: '#1677FF' }}
                  />
                </Col>

                {/* Uptime */}
                <Col span={12}>
                  <Statistic
                    title="运行时间"
                    value={formatUptime(overview?.uptime_seconds || 0)}
                    prefix="⏱️"
                  />
                </Col>

                {/* Gate Status */}
                <Col span={24}>
                  <div className="gate-status-row">
                    <span className="gate-label">Gate 门禁状态：</span>
                    <Space>
                      <span title="代码审查门禁">
                        G1: {renderGateBadge(overview?.gates?.gate1_code_review || 'pending')}
                      </span>
                      <span title="性能压测门禁">
                        G2: {renderGateBadge(overview?.gates?.gate2_performance || 'pending')}
                      </span>
                      <span title="功能测试门禁">
                        G3: {renderGateBadge(overview?.gates?.gate3_testing || 'pending')}
                      </span>
                      <span title="上线终审门禁">
                        G4: {renderGateBadge(overview?.gates?.gate4_final_review || 'pending')}
                      </span>
                    </Space>
                  </div>
                </Col>
              </Row>
            </Card>

            {/* Progress Panel */}
            <Card title="📈 进度面板" className="section-card" size="small">
              <div className="progress-list">
                {agents
                  .filter((a) => a.status === 'running')
                  .slice(0, 8)
                  .map((agent) => (
                    <div key={agent.id} className="progress-item">
                      <div className="progress-item-header">
                        <span className="agent-name">{agent.icon} {agent.display_name}</span>
                        <span className="progress-percent">{Math.round(agent.current_task_progress)}%</span>
                      </div>
                      <Progress
                        percent={Math.round(agent.current_task_progress)}
                        size="small"
                        strokeColor={
                          agent.current_task_progress > 70
                            ? '#52C41A'
                            : agent.current_task_progress > 30
                            ? '#FAAD14'
                            : '#FF4D4F'
                        }
                      />
                      {agent.current_task_name && (
                        <span className="task-name-hint">{agent.current_task_name}</span>
                      )}
                    </div>
                  ))}

                {agents.filter((a) => a.status === 'running').length === 0 && (
                  <div className="empty-progress">
                    <p>暂无运行中的任务</p>
                  </div>
                )}
              </div>
            </Card>
          </Col>
        </Row>
        </Spin>
      </main>

      {/* Footer */}
      <footer className="dashboard-footer">
        <span>v1.0.0</span>
        <span>
          WS: {isConnected ? (
            <><WifiOutlined style={{ color: '#52C41A' }} /> Connected</>
          ) : (
            <><DisconnectOutlined style={{ color: '#FF4D4F' }} /> Disconnected</>
          )}
        </span>
        <span>Last Update: {lastUpdateTime}</span>
        <Tag color={isRealtimePaused ? 'orange' : 'blue'}>
          {isRealtimePaused ? '实时推送已暂停' : 'Auto-refresh ON'}
        </Tag>
      </footer>

      <FeedbackSettings visible={settingsVisible} onClose={() => setSettingsVisible(false)} />
    </div>
  );
};

// Helper: format uptime seconds to readable string
function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  if (seconds < 86400)
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`;
}

export default Dashboard;
