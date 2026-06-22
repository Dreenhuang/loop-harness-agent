import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { promises as fs } from "fs";
import path from "path";
import os from "os";
import {
  standardize,
  scoreLoopRun,
  benchmarkScore,
  mutatePrompt,
  mutate,
  compareBenchmarks,
  select,
  appendHistory,
  loadHistory,
  runAutoloop,
  type AutoloopHistoryEntry,
} from "../autoloop.ts";
import type { PipelineState } from "../orchestrator.ts";

function buildState(overrides: Partial<PipelineState> = {}): PipelineState {
  const now = new Date().toISOString();
  return {
    phase: "DEVELOPMENT",
    tasks: {
      a: {
        id: "a",
        phase: "DEVELOPMENT",
        agentType: "backend",
        status: "DONE",
        inputPaths: [],
        outputPath: "x",
        acceptanceCriteria: {},
        attempts: 0,
        maxAttempts: 3,
        dependencies: [],
        worktree: false,
      } as any,
      b: {
        id: "b",
        phase: "DEVELOPMENT",
        agentType: "frontend",
        status: "FAILED",
        inputPaths: [],
        outputPath: "x",
        acceptanceCriteria: {},
        attempts: 3,
        maxAttempts: 3,
        dependencies: [],
        worktree: false,
      } as any,
    },
    dependencies: {},
    budget: {
      maxCost: 100,
      currentCost: 25,
      maxIterations: 200,
      currentIteration: 5,
      maxAttemptsPerTask: 3,
      noProgressThreshold: 3,
      noProgressCount: 0,
    },
    qualityGates: {
      codeReview: "PASSED",
      performance: "RUNNING",
      testing: "NOT_STARTED",
      final: "NOT_STARTED",
    },
    startedAt: now,
    updatedAt: now,
    projectName: "test",
    ...overrides,
  };
}

describe("autoloop · 阶段 1 standardize", () => {
  it("深拷贝原 state，不污染源对象", () => {
    const state = buildState();
    const snap = standardize(state);
    snap.sourceState.tasks["__hack__"] = {} as any;
    expect((state.tasks as any).__hack__).toBeUndefined();
  });

  it("正确计算指标", () => {
    const snap = standardize(buildState());
    expect(snap.normalized.totalTasks).toBe(2);
    expect(snap.normalized.doneTasks).toBe(1);
    expect(snap.normalized.failedTasks).toBe(1);
    expect(snap.normalized.completionRate).toBeGreaterThan(0);
    expect(snap.normalized.completionRate).toBeLessThanOrEqual(1);
  });

  it("生成稳定的 fingerprint", () => {
    const fixed = "2026-06-22T00:00:00.000Z";
    const a = standardize(buildState({ startedAt: fixed, updatedAt: fixed }));
    const b = standardize(buildState({ startedAt: fixed, updatedAt: fixed }));
    expect(a.fingerprint).toBe(b.fingerprint);
  });
});

describe("autoloop · 阶段 2 benchmark / scoreLoopRun", () => {
  it("scoreLoopRun 返回值在 [0, 100]", () => {
    const state = buildState();
    const s = scoreLoopRun(state, { prompt: "用户价值约束验收目标", seed: 42 });
    expect(s).toBeGreaterThanOrEqual(0);
    expect(s).toBeLessThanOrEqual(100);
  });

  it("benchmarkScore 聚合多次运行得到 mean/stddev", () => {
    const state = buildState();
    const bm = benchmarkScore(state, "用户价值约束验收目标替代证据", {
      runs: 5,
      seed: 7,
      variantId: "v1",
    });
    expect(bm.runScores).toHaveLength(5);
    expect(bm.mean).toBeGreaterThan(0);
    expect(bm.stddev).toBeGreaterThanOrEqual(0);
    expect(bm.min).toBeLessThanOrEqual(bm.mean);
    expect(bm.max).toBeGreaterThanOrEqual(bm.mean);
  });

  it("同 seed 产出同 score（确定性）", () => {
    const state = buildState();
    const a = scoreLoopRun(state, { prompt: "用户价值约束", seed: 99 });
    const b = scoreLoopRun(state, { prompt: "用户价值约束", seed: 99 });
    expect(a).toBe(b);
  });
});

describe("autoloop · 阶段 3 mutate 护栏", () => {
  const SAMPLE = "你是一名用户需求澄清教练，请明确目标、价值、约束、验收标准。".repeat(2);

  it("变异比例 ≤ 5%", () => {
    for (let s = 1; s <= 10; s++) {
      const { prompt, actualRate } = mutatePrompt(SAMPLE, 0.05, s);
      expect(actualRate).toBeLessThanOrEqual(0.05 + 1e-9);
      expect(prompt.length).toBe(SAMPLE.length); // 不允许变长
    }
  });

  it("maxMutationRate 超过 0.05 会被硬护栏截断", () => {
    // 传入 0.5 应当被强制截断为 0.05
    const { actualRate } = mutatePrompt(SAMPLE, 0.5, 42);
    expect(actualRate).toBeLessThanOrEqual(0.05 + 1e-9);
  });

  it("mutate() 输出 SkillVariant 字段齐全", () => {
    const v = mutate(null, SAMPLE, {
      skillName: "brainstorming",
      maxMutationRate: 0.05,
      seed: 1,
    });
    expect(v.id).toMatch(/^var-brainstorming-/);
    expect(v.skillName).toBe("brainstorming");
    expect(v.baseLength).toBe(SAMPLE.length);
    expect(v.prompt.length).toBe(SAMPLE.length);
    expect(v.mutationRate).toBeLessThanOrEqual(0.05);
  });

  it("同 seed 产出同 variant（确定性）", () => {
    const a = mutate(null, SAMPLE, {
      skillName: "brainstorming",
      maxMutationRate: 0.05,
      seed: 100,
    });
    const b = mutate(null, SAMPLE, {
      skillName: "brainstorming",
      maxMutationRate: 0.05,
      seed: 100,
    });
    expect(a.prompt).toBe(b.prompt);
    expect(a.changedPositions).toEqual(b.changedPositions);
  });
});

describe("autoloop · 阶段 4 compare", () => {
  it("compareBenchmarks 输出 baseline/variant/delta/significance", () => {
    const state = buildState();
    const r = compareBenchmarks(
      state,
      "用户价值约束验收目标",
      "使用者益处限制验证目的",
      { runs: 3, seed: 5, baselineId: "base", variantId: "var" }
    );
    expect(r.baseline.runScores).toHaveLength(3);
    expect(r.variant.runScores).toHaveLength(3);
    expect(typeof r.delta).toBe("number");
    expect(typeof r.significance).toBe("number");
  });
});

describe("autoloop · 阶段 5 select", () => {
  function fakeScore(mean: number, stddev: number, id: string) {
    return {
      variantId: id,
      runScores: [mean, mean, mean],
      mean,
      stddev,
      min: mean,
      max: mean,
      metrics: {} as any,
      config: { runs: 3, seed: 1 },
    };
  }
  function fakeVariant(mr: number) {
    return {
      id: "v",
      parentId: null,
      skillName: "x",
      prompt: "x",
      baseLength: 1,
      changedPositions: [],
      mutationRate: mr,
      createdAt: "",
      seed: 1,
    };
  }

  it("变体明显胜出 → 保留", () => {
    const d = select(fakeScore(70, 1, "p"), fakeScore(75, 1, "c"), fakeVariant(0.03));
    expect(d.winner).toBe("candidate");
    expect(d.rollbackApplied).toBe(false);
    expect(d.delta).toBeGreaterThan(0);
  });

  it("变体明显落后 → 回滚", () => {
    const d = select(fakeScore(80, 1, "p"), fakeScore(70, 1, "c"), fakeVariant(0.03));
    expect(d.winner).toBe("parent");
    expect(d.rollbackApplied).toBe(true);
  });

  it("变体差异在 ±0.5 内 → 保守回滚", () => {
    const d = select(fakeScore(70, 1, "p"), fakeScore(70.2, 1, "c"), fakeVariant(0.03));
    expect(d.winner).toBe("parent");
    expect(d.rollbackApplied).toBe(true);
  });

  it("变体突变率 > 5% → 强制回滚（双保险护栏）", () => {
    const d = select(fakeScore(50, 1, "p"), fakeScore(80, 1, "c"), fakeVariant(0.06));
    expect(d.winner).toBe("parent");
    expect(d.rollbackApplied).toBe(true);
    expect(d.reason).toContain("5%");
  });
});

describe("autoloop · 历史持久化", () => {
  let tmpDir: string;
  let historyPath: string;

  beforeEach(async () => {
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "autoloop-test-"));
    historyPath = path.join(tmpDir, "history.json");
  });

  afterEach(async () => {
    try {
      await fs.rm(tmpDir, { recursive: true, force: true });
    } catch {}
  });

  it("appendHistory 原子写入并保留上次条目数", async () => {
    const e1: AutoloopHistoryEntry = {
      id: "r1",
      timestamp: new Date().toISOString(),
      skillName: "brainstorming",
      stage1_snapshot: {} as any,
      stage2_baseline: {} as any,
      stage3_variant: {} as any,
      stage4_comparison: { baseline: {} as any, variant: {} as any, delta: 0, significance: 0 },
      stage5_decision: {} as any,
      status: "rolled_back",
      guardrails: {
        maxMutationRate: 0.05,
        actualMutationRate: 0.04,
        snapshotPreserved: true,
        historyWritten: true,
      },
    };
    await appendHistory(e1, historyPath);
    let history = await loadHistory(historyPath);
    expect(history).toHaveLength(1);
    expect(history[0].id).toBe("r1");

    const e2 = { ...e1, id: "r2" };
    await appendHistory(e2, historyPath);
    history = await loadHistory(historyPath);
    expect(history).toHaveLength(2);
  });

  it("loadHistory 在文件不存在时返回空数组", async () => {
    const h = await loadHistory(path.join(tmpDir, "missing.json"));
    expect(h).toEqual([]);
  });
});

describe("autoloop · 端到端 runAutoloop", () => {
  it("整链路：state→5阶段→history", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "autoloop-e2e-"));
    const historyPath = path.join(tmpDir, "history.json");
    try {
      const state = buildState();
      const result = await runAutoloop({
        state,
        skillName: "brainstorming",
        basePrompt: "用户价值约束验收目标替代证据".repeat(5),
        benchmarkRuns: 3,
        maxMutationRate: 0.05,
        seed: 11,
        historyPath,
      });
      expect(result.entry.status).toMatch(/kept|rolled_back/);
      expect(result.entry.guardrails.actualMutationRate).toBeLessThanOrEqual(0.05 + 1e-9);
      const history = await loadHistory(historyPath);
      expect(history).toHaveLength(1);
      expect(history[0].id).toBe(result.entry.id);
    } finally {
      await fs.rm(tmpDir, { recursive: true, force: true });
    }
  });

  it("maxMutationRate 超过 5% 抛错（兜底护栏）", async () => {
    const state = buildState();
    await expect(
      runAutoloop({
        state,
        skillName: "brainstorming",
        basePrompt: "用户价值",
        benchmarkRuns: 1,
        maxMutationRate: 0.5,
        seed: 1,
      })
    ).rejects.toThrow(/超过/);
  });
});