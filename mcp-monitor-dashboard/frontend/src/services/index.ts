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
  async start(): Promise<ApiResponse> {
    return api.post('/system/start');
  },

  async stop(force = false): Promise<ApiResponse> {
    return api.post('/system/stop', { force });
  },

  async restart(): Promise<ApiResponse> {
    return api.post('/system/restart');
  },

  async getStatus(): Promise<ApiResponse<SystemStatus>> {
    return api.get('/system/status');
  },
};

export { api };
export default { agentService, logService, projectService, systemService };
