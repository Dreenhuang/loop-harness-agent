/**
 * Log Store - Zustand state management for log data
 */

import { create } from 'zustand';
import type { LogEntry } from '@/types';

interface LogState {
  logs: LogEntry[];
  isLoading: boolean;
  total: number;
  filter: {
    agent_id?: string;
    level?: string;
    keyword?: string;
  };

  // Actions
  setLogs: (logs: LogEntry[], total: number) => void;
  prependLog: (log: LogEntry) => void;
  setLoading: (loading: boolean) => void;
  setFilter: (filter: Partial<LogState['filter']>) => void;
  clearLogs: () => void;
}

export const useLogStore = create<LogState>((set) => ({
  logs: [],
  isLoading: true,
  total: 0,
  filter: {},

  setLogs: (logs, total) => set({ logs, total, isLoading: false }),

  prependLog: (log) =>
    set((state) => ({
      logs: [log, ...state.logs].slice(0, 1000), // Keep max 1000 logs in memory
      total: state.total + 1,
    })),

  setLoading: (isLoading) => set({ isLoading }),

  setFilter: (filter) =>
    set((state) => ({ filter: { ...state.filter, ...filter } })),

  clearLogs: () => set({ logs: [], total: 0 }),
}));
