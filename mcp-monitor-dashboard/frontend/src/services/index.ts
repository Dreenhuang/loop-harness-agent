/**
 * API Service - Axios instance and API methods
 */

import axios from 'axios';
import type { ApiResponse, Agent, LogQueryResult, ProjectOverview, SystemStatus } from '@/types';

// Create axios instance
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);

    // 通过自定义事件把错误派发给 NotificationProvider，避免 axios 拦截器内无法使用 Hook
    if (typeof window !== 'undefined') {
      let messageText: string;
      let statusCode: number | undefined;

      if (error.response) {
        statusCode = error.response.status;
        const data = error.response.data as { message?: string; detail?: string; msg?: string } | undefined;
        messageText = data?.message || data?.detail || data?.msg || `服务器错误 (${statusCode})`;
      } else if (error.request) {
        messageText = '网络连接失败，请检查后端服务是否运行';
      } else {
        messageText = error.message || '请求异常';
      }

      window.dispatchEvent(
        new CustomEvent('mcp-api-error', {
          detail: { message: messageText, statusCode, original: error },
        })
      );
    }

    return Promise.reject(error);
  }
);

// ==================== Agent Service ====================

const agentService = {
  async getAll(): Promise<ApiResponse<Agent[]>> {
    return api.get('/agents');
  },

  async getById(id: string): Promise<ApiResponse<Agent>> {
    return api.get(`/agents/${id}`);
  },
};

// ==================== Log Service ====================

interface LogQueryParams {
  agent_id?: string;
  level?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}

const logService = {
  async getLogs(params: LogQueryParams = {}): Promise<ApiResponse<LogQueryResult>> {
    return api.get('/logs', { params });
  },
};

// ==================== Project Service ====================

const projectService = {
  async getOverview(): Promise<ApiResponse<ProjectOverview>> {
    return api.get('/project/overview');
  },
};

// ==================== System Service ====================

const systemService = {
  async start(): Promise<ApiResponse<{ status: string }>> {
    return api.post('/system/start');
  },

  async stop(force = false): Promise<ApiResponse<{ status: string }>> {
    return api.post('/system/stop', { force });
  },

  async restart(): Promise<ApiResponse<{ status: string }>> {
    return api.post('/system/restart');
  },

  async getStatus(): Promise<ApiResponse<SystemStatus>> {
    return api.get('/system/status');
  },
};

export { api };
export default { agentService, logService, projectService, systemService };
