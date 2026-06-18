/**
 * Agent Store - Zustand state management for agent data
 */

import { create } from 'zustand';
import type { Agent, AgentStatus } from '@/types';

interface AgentState {
  agents: Agent[];
  isLoading: boolean;
  error: string | null;

  // Actions
  setAgents: (agents: Agent[]) => void;
  updateAgent: (agentId: string, updates: Partial<Agent>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Getters
  getAgentById: (id: string) => Agent | undefined;
  getAgentsByStatus: (status: AgentStatus) => Agent[];
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  isLoading: true,
  error: null,

  setAgents: (agents) => set({ agents, isLoading: false, error: null }),

  updateAgent: (agentId, updates) =>
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.id === agentId ? { ...agent, ...updates } : agent
      ),
    })),

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),

  getAgentById: (id) => get().agents.find((a) => a.id === id),

  getAgentsByStatus: (status) =>
    get().agents.filter((a) => a.status === status),
}));
