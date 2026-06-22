import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('child_process', () => ({
  spawn: vi.fn(() => ({
    on: vi.fn(),
  })),
}));

vi.mock('fs', async (importOriginal) => {
  const actual = await importOriginal<typeof import('fs')>();
  return {
    ...actual,
    promises: {
      mkdir: vi.fn().mockResolvedValue(undefined),
      writeFile: vi.fn().mockResolvedValue(undefined),
      readFile: vi.fn().mockRejectedValue({ code: 'ENOENT' }),
    },
  };
});


import {
  OrchestratorStateMachine,
  type PipelineState,
  type TaskState,
} from '../orchestrator.ts';

function createBaseState(overrides: Partial<PipelineState> = {}): PipelineState {
  return {
    phase: 'INIT',
    tasks: {},
    dependencies: {},
    budget: {
      maxCost: 100,
      currentCost: 0,
      maxIterations: 200,
      currentIteration: 0,
      maxAttemptsPerTask: 3,
      noProgressThreshold: 3,
      noProgressCount: 0,
    },
    qualityGates: {
      codeReview: 'NOT_STARTED',
      performance: 'NOT_STARTED',
      testing: 'NOT_STARTED',
      final: 'NOT_STARTED',
    },
    startedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    projectName: 'test-project',
    ...overrides,
  };
}

function createTask(
  id: string,
  phase: PipelineState['phase'],
  overrides: Partial<TaskState> = {}
): TaskState {
  return {
    id,
    phase,
    agentType: 'test-agent',
    status: 'PENDING',
    inputPaths: ['input.md'],
    outputPath: 'output.md',
    acceptanceCriteria: {},
    attempts: 0,
    maxAttempts: 3,
    dependencies: [],
    worktree: false,
    ...overrides,
  };
}

describe('OrchestratorStateMachine', () => {
  let consoleSpies: {
    log: ReturnType<typeof vi.spyOn>;
    error: ReturnType<typeof vi.spyOn>;
    warn: ReturnType<typeof vi.spyOn>;
  };

  beforeEach(() => {
    consoleSpies = {
      log: vi.spyOn(console, 'log').mockImplementation(() => {}),
      error: vi.spyOn(console, 'error').mockImplementation(() => {}),
      warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
    };
  });

  afterEach(() => {
    consoleSpies.log.mockRestore();
    consoleSpies.error.mockRestore();
    consoleSpies.warn.mockRestore();
  });

  describe('constructor', () => {
    it('应保留初始状态并补全时间戳', () => {
      const state = createBaseState({ startedAt: undefined as unknown as string });
      const machine = new OrchestratorStateMachine(state);

      expect(machine).toBeInstanceOf(OrchestratorStateMachine);
      expect(state.phase).toBe('INIT');
      expect(state.startedAt).toBeDefined();
      expect(state.updatedAt).toBeDefined();
    });
  });

  describe('tick', () => {
    it('应推进迭代计数器', async () => {
      const state = createBaseState();
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.budget.currentIteration).toBe(1);
      expect(state.updatedAt).toBeDefined();
    });

    it('当前 Phase 完成后应推进到下一 Phase', async () => {
      const state = createBaseState({
        tasks: {
          task_init: createTask('task_init', 'INIT', { status: 'DONE' }),
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.phase).toBe('REQUIREMENTS');
      expect(state.budget.currentIteration).toBe(1);
    });

    it('没有就绪任务时当前 Phase 视为完成并推进到下一 Phase', async () => {
      const state = createBaseState();
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.budget.currentIteration).toBe(1);
      expect(state.phase).toBe('REQUIREMENTS');
    });

    it('应扇出当前 Phase 中的就绪任务并更新状态为 RUNNING', async () => {
      const state = createBaseState({
        tasks: {
          task_1: createTask('task_1', 'INIT'),
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.tasks.task_1.status).toBe('RUNNING');
      expect(state.tasks.task_1.startedAt).toBeDefined();
      expect(state.budget.currentIteration).toBe(1);
    });

    it('依赖未完成的任务不应被扇出', async () => {
      const state = createBaseState({
        tasks: {
          dep: createTask('dep', 'INIT', { status: 'RUNNING' }),
          child: createTask('child', 'INIT', { dependencies: ['dep'] }),
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.tasks.child.status).toBe('PENDING');
    });
  });

  describe('三道硬刹车', () => {
    it('达到最大迭代次数时触发 emergencyStop', async () => {
      const state = createBaseState({
        budget: {
          ...createBaseState().budget,
          currentIteration: 200,
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.phase).toBe('DONE');
      expect(state.budget.currentIteration).toBe(200);
    });

    it('预算耗尽时触发 emergencyStop', async () => {
      const state = createBaseState({
        budget: {
          ...createBaseState().budget,
          currentCost: 100,
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.phase).toBe('DONE');
    });

    it('连续无进展次数达到阈值时触发 emergencyStop', async () => {
      const state = createBaseState({
        budget: {
          ...createBaseState().budget,
          noProgressCount: 3,
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.tick();

      expect(state.phase).toBe('DONE');
    });
  });

  describe('onTaskComplete', () => {
    it('成功完成时任务状态变为 DONE 并重置无进展计数', async () => {
      const state = createBaseState({
        tasks: {
          task_1: createTask('task_1', 'INIT', { status: 'RUNNING' }),
        },
        budget: {
          ...createBaseState().budget,
          noProgressCount: 2,
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.onTaskComplete('task_1', true);

      expect(state.tasks.task_1.status).toBe('DONE');
      expect(state.tasks.task_1.completedAt).toBeDefined();
      expect(state.budget.noProgressCount).toBe(0);
    });

    it('失败且未达最大重试次数时状态回退到 PENDING', async () => {
      const state = createBaseState({
        tasks: {
          task_1: createTask('task_1', 'INIT', {
            status: 'RUNNING',
            attempts: 1,
            maxAttempts: 3,
          }),
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.onTaskComplete('task_1', false, 'network error');

      expect(state.tasks.task_1.status).toBe('PENDING');
      expect(state.tasks.task_1.attempts).toBe(2);
      expect(state.tasks.task_1.lastErrorFingerprint).toBeDefined();
      expect(state.budget.noProgressCount).toBe(1);
    });

    it('失败且达到最大重试次数时状态变为 FAILED', async () => {
      const state = createBaseState({
        tasks: {
          task_1: createTask('task_1', 'INIT', {
            status: 'RUNNING',
            attempts: 2,
            maxAttempts: 3,
          }),
        },
      });
      const machine = new OrchestratorStateMachine(state);

      await machine.onTaskComplete('task_1', false, 'build failed');

      expect(state.tasks.task_1.status).toBe('FAILED');
      expect(state.tasks.task_1.attempts).toBe(3);
      expect(state.tasks.task_1.error).toBe('build failed');
      expect(state.budget.noProgressCount).toBe(1);
    });

    it('未知任务回调时应静默返回', async () => {
      const state = createBaseState();
      const machine = new OrchestratorStateMachine(state);

      await machine.onTaskComplete('unknown', true);

      expect(consoleSpies.error).toHaveBeenCalledWith(
        expect.stringContaining('未知任务 unknown')
      );
    });
  });
});
