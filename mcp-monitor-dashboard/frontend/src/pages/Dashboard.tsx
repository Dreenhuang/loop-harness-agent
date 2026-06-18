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
  Tooltip,
  message,
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
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAgentStore } from '@/store/agentStore';
import { useLogStore } from '@/store/logStore';
import { useProjectStore } from '@/store/projectStore';
import type { WSMessage, Agent, LogEntry, ProjectOverview, SystemStatus } from '@/types';
import agentService from '@/services/agentService';
import logService from '@/services/logService';
import projectService from '@/services/projectService';
import systemService from '@/services/systemService';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  // State
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [logLevelFilter, setLogLevelFilter] = useState<string[]>([]);
  const [lastUpdateTime, setLastUpdateTime] = useState<string>('-');

  // Stores
  const { agents, setAgents, updateAgent } = useAgentStore();
  const { logs, setLogs, prependLog } = useLogStore();
  const { overview, setOverview } = useProjectStore();

  // Refs for auto-scroll
  const logContainerRef = useRef<HTMLDivElement>(null);
  const isAutoScrollRef = useRef(true);

  // WebSocket connection
  const { isConnected, subscribe } = useWebSocket({
    onMessage: handleWSMessage,
    onOpen: () => {
      message.success('实时连接已建立');
      subscribe(['agent_status', 'logs', 'overview']);
    },
    onClose: () => {
      message.warning('连接已断开，正在重连...');
    },
  });

  // Handle incoming WebSocket messages
  function handleWSMessage(msg: WSMessage) {
    switch (msg.type) {
      case 'init':
        // Initial data load
        if (Array.isArray(msg.data?.agents)) {
          setAgents(msg.data.agents as Agent[]);
        }
        if (msg.data?.overview) {
          setOverview(msg.data.overview as ProjectOverview);
        }
        break;

      case 'agent_status_update':
        if (Array.isArray(msg.data)) {
          msg.data.forEach((agent: Agent) => {
            updateAgent(agent.id, agent);
          });
        }
        break;

      case 'project_overview_update':
        if (msg.data) {
          setOverview(msg.data as ProjectOverview);
        }
        break;

      case 'log_entry':
        if (msg.data) {
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

  // Load initial data via REST API
  useEffect(() => {
    loadInitialData();
    loadSystemStatus();

    // Poll system status every 10s
    const interval = setInterval(loadSystemStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadInitialData() {
    try {
      const [agentsRes, logsRes, projectRes] = await Promise.all([
        agentService.getAll(),
        logService.getLogs({ page_size: 100 }),
        projectService.getOverview(),
      ]);

      setAgents(agentsRes.data || []);
      setLogs(logsRes.data?.items || [], logsRes.data?.total || 0);
      setOverview(projectRes.data || null);
    } catch (error) {
      console.error('Failed to load initial data:', error);
      message.error('加载数据失败');
    }
  }

  async function loadSystemStatus() {
    try {
      const res = await systemService.getStatus();
      setSystemStatus(res.data);
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  }

  // System control handlers
  async function handleStart() {
    setLoadingAction('start');
    try {
      await systemService.start();
      message.success('MCP Server 启动成功');
      await loadSystemStatus();
    } catch (error) {
      message.error('启动失败');
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleStop() {
    setLoadingAction('stop');
    try {
      await systemService.stop();
      message.success('MCP Server 已停止');
      await loadSystemStatus();
    } catch (error) {
      message.error('停止失败');
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleRestart() {
    setLoadingAction('restart');
    try {
      await systemService.restart();
      message.success('MCP Server 重启成功');
      await loadSystemStatus();
    } catch (error) {
      message.error('重启失败');
    } finally {
      setLoadingAction(null);
    }
  }

  // Log search handler
  async function handleSearch(value: string) {
    setSearchKeyword(value);
    try {
      const res = await logService.getLogs({ keyword: value });
      setLogs(res.data?.items || [], res.data?.total || 0);
    } catch (error) {
      console.error('Search failed:', error);
    }
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
          <Tooltip title={`MCP Server: ${mcpRunning ? '运行中' : '已停止'}`}>
            <Badge status={mcpRunning ? 'success' : 'default'} />
          </Tooltip>

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
          </Space>

          <SettingOutlined className="settings-icon" style={{ fontSize: 18 }} />
        </div>
      </header>

      {/* Main Content - Four Quadrant Layout */}
      <main className="dashboard-main">
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
                  <Input
                    placeholder="搜索日志..."
                    prefix={<SearchOutlined />}
                    allowClear
                    size="small"
                    style={{ width: 180 }}
                    onChange={(e) => handleSearch(e.target.value)}
                    value={searchKeyword}
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
                  <div className="empty-logs">
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
                    value={overview?.tasks.completed || 0}
                    suffix={`/ ${overview?.tasks.total || 0}`}
                    prefix="📋"
                    valueStyle={{ color: '#52C41A' }}
                  />
                </Col>

                {/* Token Budget */}
                <Col span={12}>
                  <Statistic
                    title="Token 预算"
                    value={overview?.token_budget.percentage || 0}
                    suffix="%"
                    prefix="💰"
                    valueStyle={{
                      color:
                        (overview?.token_budget.percentage || 0) > 90
                          ? '#FF4D4F'
                          : '#FAAD14',
                    }}
                  />
                  <Progress
                    percent={Math.round(overview?.token_budget.percentage || 0)}
                    size="small"
                    showInfo={false}
                    strokeColor={
                      (overview?.token_budget.percentage || 0) > 90
                        ? '#FF4D4F'
                        : undefined
                    }
                  />
                </Col>

                {/* Agent Distribution */}
                <Col span={12}>
                  <Statistic
                    title="活跃 Agent"
                    value={overview?.agents.active || 0}
                    suffix={`/ ${overview?.agents.total || 0}`}
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
                      <Tooltip title="代码审查">
                        <span>G1: {renderGateBadge(overview?.gates.gate1_code_review || 'pending')}</span>
                      </Tooltip>
                      <Tooltip title="性能压测">
                        <span>G2: {renderGateBadge(overview?.gates.gate2_performance || 'pending')}</span>
                      </Tooltip>
                      <Tooltip title="功能测试">
                        <span>G3: {renderGateBadge(overview?.gates.gate3_testing || 'pending')}</span>
                      </Tooltip>
                      <Tooltip title="上线终审">
                        <span>G4: {renderGateBadge(overview?.gates.gate4_final_review || 'pending')}</span>
                      </Tooltip>
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
        <Tag color="blue">Auto-refresh ON</Tag>
      </footer>
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
