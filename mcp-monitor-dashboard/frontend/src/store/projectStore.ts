/**
 * Project Store - Zustand state management for project overview
 */

import { create } from 'zustand';
import type { ProjectOverview } from '@/types';

interface ProjectState {
  overview: ProjectOverview | null;
  isLoading: boolean;

  // Actions
  setOverview: (overview: ProjectOverview) => void;
  setLoading: (loading: boolean) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  overview: null,
  isLoading: true,

  setOverview: (overview) => set({ overview, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
}));
