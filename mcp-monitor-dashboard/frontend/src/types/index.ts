/**
 * TypeScript Type Definitions for MCP Monitor Dashboard
 */

// ==================== Agent Types ====================

export type AgentStatus = 'idle' | 'running' | 'error' | 'complete';

export interface AgentTask {
  name?: string;
  phase?: number;
  progress: number;
  started_at?: string;
  estimated_end?: string;
}

export interface Agent {
  id: string;
  display_name: string;
  role_type: string;
  icon: string;
  status: AgentStatus;
  current_task_name?: string;
  current_task_phase?: number;
  current_task_progress: number;
  last_activity_time?: string;
  error_summary?: string;
}

// ==================== Log Types ====================

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  id: number;
  agent_id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface LogQueryResult {
  items: LogEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ==================== Project Types ====================

export type GateStatus = 'pending' | 'passed' | 'failed';

export interface TokenBudget {
  used: number;
  total: number;
  percentage: number;
}

export interface TaskStats {
  total: number;
  completed: number;
  in_progress: number;
  failed: number;
  pending: number;
}

export interface AgentStats {
  total: number;
  active: number;
  idle: number;
  error: number;
}

export interface GateInfo {
  gate1_code_review: GateStatus;
  gate2_performance: GateStatus;
  gate3_testing: GateStatus;
  gate4_final_review: GateStatus;
}

export interface ProjectOverview {
  project_name: string;
  current_phase: string;
  phase_progress: number;
  tasks: TaskStats;
  token_budget: TokenBudget;
  agents: AgentStats;
  gates: GateInfo;
  uptime_seconds: number;
  last_update: string;
}

// ==================== System Types ====================

export type MCPServerStatusType = 'running' | 'stopped' | 'error';

export interface MCPServerStatus {
  status: MCPServerStatusType;
  pid?: number;
  uptime_seconds: number;
  memory_usage_mb: number;
  cpu_usage_percent: number;
}

export interface MonitorSystemStatus {
  version: string;
  websocket_connections: number;
  uptime_seconds: number;
}

export interface SystemStatus {
  mcp_server: MCPServerStatus;
  monitor_system: MonitorSystemStatus;
}

// ==================== WebSocket Types ====================

export type WSMessageType =
  | 'subscribe'
  | 'unsubscribe'
  | 'ping'
  | 'request_full_sync'
  | 'init'
  | 'agent_status_update'
  | 'log_entry'
  | 'project_overview_update'
  | 'progress_update'
  | 'alert'
  | 'pong'
  | 'error';

export interface WSMessage {
  type: WSMessageType;
  data?: unknown;
  channel?: string;
  timestamp: string;
}

export interface WSSubscribeRequest {
  type: 'subscribe';
  channels: string[];
}

// ==================== API Response Types ====================

export interface ApiResponse<T> {
  code: number;
  data?: T;
  message?: string;
}
