/**
 * =============================================================================
 * Loop Agent · Autoloop 自进化循环 POC
 * TypeScript · Bun 可执行
 *
 * 目标：实现 chip.json 中定义的 5 个 autoloop 阶段 POC：
 *   1. 标准化（Standardize）   —— 复用 OrchestratorStateMachine 接口
 *   2. 评估基准（Benchmark）  —— scoreLoopRun(state): number
 *   3. 变异探索（Mutate）     —— 对 Skill prompt 做 ≤5% 字符改动
 *   4. 评分对比（Compare）    —— N 次评估基线/变体，输出对比
 *   5. 优胜劣汰（Select）     —— 分数更高则保留，否则回滚
 *
 * 设计原则：
 *   - 不修改 orchestrator.ts 业务逻辑（仅读取 + 复用其类型）。
 *   - 严格护栏：变异幅度 ≤5%，每次保留原版本快照，所有版本写入 history。
 *   - 完全确定性：相同 seed 必须产出相同结果（benchmark 与变异）。
 *   - 所有 IO 走 blackboard/autoloop/，不污染现有 blackboard/state.json。
 *
 * 启动方式：
 *   bun run loop-agent-engine/autoloop-cli.ts
 * =============================================================================
 */

import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import type {
  PipelineState,
  Phase,
  TaskState,
  GateStatus,
} from "./orchestrator";

// =============================================================================
// 类型定义
// =============================================================================

/** 单次 Loop 运行快照（来自标准化阶段） */
export interface LoopRunSnapshot {
  id: string;
  createdAt: string;
  sourceState: PipelineState;
  fingerprint: string;
  normalized: NormalizedMetrics;
}

/** 标准化阶段提取的关键指标（用于 benchmark） */
export interface NormalizedMetrics {
  totalTasks: number;
  doneTasks: number;
  failedTasks: number;
  runningTasks: number;
  pendingTasks: number;
  completionRate: number;
  phaseProgress: number;
  gatesPassed: number;
  gatesTotal: number;
  iteration: number;
  budgetUsedRatio: number;
}

/** Benchmark 评分（多次运行的聚合结果） */
export interface BenchmarkScore {
  variantId: string;
  runScores: number[];
  mean: number;
  stddev: number;
  min: number;
  max: number;
  metrics: NormalizedMetrics;
  config: { runs: number; seed: number };
}

/** Skill prompt 变体 */
export interface SkillVariant {
  id: string;
  parentId: string | null;
  skillName: string;
  prompt: string;
  baseLength: number;
  changedPositions: number[];
  mutationRate: number;
  createdAt: string;
  seed: number;
}

/** 阶段 5 的选择决策 */
export interface SelectionDecision {
  winner: "candidate" | "parent";
  reason: string;
  parentScore: BenchmarkScore;
  candidateScore: BenchmarkScore;
  delta: number;
  zScore: number;
  rollbackApplied: boolean;
  keptAt: string;
}

/** 完整的 autoloop 历史条目（每次 run 产出一条） */
export interface AutoloopHistoryEntry {
  id: string;
  timestamp: string;
  skillName: string;
  stage1_snapshot: LoopRunSnapshot;
  stage2_baseline: BenchmarkScore;
  stage3_variant: SkillVariant;
  stage4_comparison: {
    baseline: BenchmarkScore;
    variant: BenchmarkScore;
    delta: number;
    significance: number;
  };
  stage5_decision: SelectionDecision;
  status: "completed" | "rolled_back" | "kept";
  guardrails: {
    maxMutationRate: number;
    actualMutationRate: number;
    snapshotPreserved: boolean;
    historyWritten: boolean;
  };
}

/** Autoloop 运行选项 */
export interface AutoloopOptions {
  state: PipelineState;
  skillName: string;
  basePrompt: string;
  /** 默认 3 次 */
  benchmarkRuns?: number;
  /** 默认 0.05（5%） */
  maxMutationRate?: number;
  /** 默认使用 Date.now() */
  seed?: number;
  /** 历史文件路径，默认 blackboard/autoloop/history.json */
  historyPath?: string;
}

// =============================================================================
// 工具：确定性伪随机数（mulberry32）
// =============================================================================

/**
 * 生成确定性随机数种子序列（mulberry32）。
 * 同一 seed 必产出同一序列，确保 POC 可复现。
 */
function createRng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * 对字符串生成稳定的短指纹（用于快照标识）。
 */
function fingerprint(input: string): string {
  let h1 = 0xdeadbeef ^ 0;
  let h2 = 0x41c6ce57 ^ 0;
  for (let i = 0; i < input.length; i++) {
    const ch = input.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507);
  h1 ^= Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507);
  h2 ^= Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return ((h2 >>> 0) * 4294967296 + (h1 >>> 0)).toString(36);
}

// =============================================================================
// 阶段 1：标准化（Standardize）
// =============================================================================

/**
 * 阶段 1：把任意来源的 PipelineState 标准化为可重复度量的指标。
 * 不修改原 state（深拷贝）。
 */
export function standardize(state: PipelineState): LoopRunSnapshot {
  // 深拷贝避免污染源 state
  const cloned: PipelineState = JSON.parse(JSON.stringify(state));

  const tasks = Object.values(cloned.tasks);
  const total = tasks.length;
  const done = tasks.filter((t) => t.status === "DONE").length;
  const failed = tasks.filter((t) => t.status === "FAILED").length;
  const running = tasks.filter((t) => t.status === "RUNNING").length;
  const pending = tasks.filter((t) => t.status === "PENDING").length;
  const blocked = tasks.filter((t) => t.status === "BLOCKED").length;

  const completionRate = total === 0 ? 0 : done / total;

  const phaseOrder: Phase[] = [
    "INIT", "REQUIREMENTS", "DESIGN", "ARCHITECTURE", "DEVELOPMENT",
    "QUALITY_GATES", "KNOWLEDGE", "DOCUMENTATION", "FINAL_REVIEW", "DEPLOY", "DONE",
  ];
  const currentIdx = phaseOrder.indexOf(cloned.phase);
  const phaseProgress = currentIdx < 0 ? 0 : currentIdx / (phaseOrder.length - 1);

  const gates: GateStatus[] = [
    cloned.qualityGates.codeReview,
    cloned.qualityGates.performance,
    cloned.qualityGates.testing,
    cloned.qualityGates.final,
  ];
  const gatesPassed = gates.filter((g) => g === "PASSED").length;
  const gatesTotal = gates.length;

  const budget = cloned.budget;
  const budgetUsedRatio =
    budget.maxCost > 0 ? budget.currentCost / budget.maxCost : 0;

  const normalized: NormalizedMetrics = {
    totalTasks: total,
    doneTasks: done,
    failedTasks: failed,
    runningTasks: running,
    pendingTasks: pending,
    // blocked 计入失败同质
    completionRate: total === 0 ? 0 : done / Math.max(1, total - blocked),
    phaseProgress,
    gatesPassed,
    gatesTotal,
    iteration: budget.currentIteration,
    budgetUsedRatio,
  };

  const fp = fingerprint(JSON.stringify(cloned));
  return {
    id: `snap-${fp}-${Date.now().toString(36)}`,
    createdAt: new Date().toISOString(),
    sourceState: cloned,
    fingerprint: fp,
    normalized,
  };
}

// =============================================================================
// 阶段 2：评估基准（Benchmark）
// =============================================================================

/**
 * scoreLoopRun(state): number —— POC 版 benchmark。
 *
 * 评分维度（满分 100）：
 *   - 完成率（权重 35%）
 *   - 阶段推进度（权重 20%）
 *   - 门禁通过率（权重 20%）
 *   - 失败惩罚（权重 -15%）
 *   - 预算使用效率（权重 10%，越低越好）
 *   - 提示词质量加成（权重 15%，传入 prompt 时评估）
 *
 * 多次运行通过 seed 引入轻微扰动，模拟"重复评估"的方差。
 */
export function scoreLoopRun(
  state: PipelineState,
  options: {
    prompt?: string;
    seed: number;
  }
): number {
  const snap = standardize(state);
  const m = snap.normalized;

  // 6 个加权分量
  const completionScore = m.completionRate * 35;            // 0~35
  const phaseScore = m.phaseProgress * 20;                  // 0~20
  const gateScore =
    m.gatesTotal === 0 ? 0 : (m.gatesPassed / m.gatesTotal) * 20;  // 0~20
  const failPenalty =
    m.totalTasks === 0
      ? 0
      : -Math.min(15, (m.failedTasks / m.totalTasks) * 15); // 0~-15
  const budgetScore = Math.max(0, (1 - m.budgetUsedRatio) * 10);  // 0~10
  const promptScore = (scorePrompt(options.prompt || "") / 100) * 15; // 0~15

  let base =
    completionScore + phaseScore + gateScore + failPenalty + budgetScore + promptScore;

  // 用 seed 引入确定性微扰（±2.0），用于重复评估产生 stddev
  const rng = createRng(options.seed);
  const noise = (rng() - 0.5) * 4.0; // -2 ~ +2
  base += noise;

  // 截断到 [0, 100]
  return Math.max(0, Math.min(100, base));
}

/**
 * 评分 prompt 质量（POC 用启发式，不替代真实评估）：
 *   - 长度合理性（50~800 字符最佳）
 *   - 关键词覆盖（用户/价值/约束/验收）
 *   - 标点密度（避免过多感叹号）
 */
export function scorePrompt(prompt: string): number {
  if (!prompt) return 0;
  const len = prompt.length;
  let lenScore = 0;
  if (len >= 50 && len <= 800) lenScore = 100;
  else if (len < 50) lenScore = (len / 50) * 100;
  else lenScore = Math.max(0, 100 - (len - 800) / 10);

  const keywords = ["用户", "价值", "约束", "验收", "目标", "替代", "证据"];
  let hit = 0;
  for (const k of keywords) if (prompt.includes(k)) hit++;
  const kwScore = (hit / keywords.length) * 100;

  const ex = (prompt.match(/!/g) || []).length;
  const exPenalty = Math.min(20, ex * 2);

  const result = lenScore * 0.5 + kwScore * 0.5 - exPenalty;
  return Math.max(0, Math.min(100, result));
}

/**
 * 多次运行 benchmark 并聚合。
 */
export function benchmarkScore(
  state: PipelineState,
  prompt: string,
  options: { runs: number; seed: number; variantId: string }
): BenchmarkScore {
  const metrics = standardize(state).normalized;
  const scores: number[] = [];
  for (let i = 0; i < options.runs; i++) {
    // 每次运行使用 seed + i 保证可复现
    const s = scoreLoopRun(state, { prompt, seed: options.seed + i });
    scores.push(Number(s.toFixed(4)));
  }
  const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
  const variance =
    scores.reduce((acc, s) => acc + Math.pow(s - mean, 2), 0) / scores.length;
  const stddev = Math.sqrt(variance);

  return {
    variantId: options.variantId,
    runScores: scores,
    mean: Number(mean.toFixed(4)),
    stddev: Number(stddev.toFixed(4)),
    min: Math.min(...scores),
    max: Math.max(...scores),
    metrics,
    config: { runs: options.runs, seed: options.seed },
  };
}

// =============================================================================
// 阶段 3：变异探索（Mutate）
// =============================================================================

/** 同义/替换候选字典（中文友好 + ASCII 字符替换） */
const REPLACE_POOL: Record<string, string[]> = {
  // ============ 中文常见词（保留语义仅微调）============
  "用户": ["使用者", "客户"],
  "价值": ["益处", "效用"],
  "约束": ["限制", "限定"],
  "验收": ["验证", "核对"],
  "目标": ["目的", "宗旨"],
  "替代": ["备选", "备择"],
  "证据": ["凭据", "佐证"],
  "澄清": ["明晰", "理清"],
  "需求": ["诉求", "需要"],
  "实现": ["落地", "达成"],
  "明确": ["清晰", "确定"],
  "帮助": ["协助", "辅助"],
  "使用": ["运用", "采用"],
  "场景": ["情形", "场合"],
  "方案": ["计划", "策划"],
  "指标": ["度量", "参数"],
  "标准": ["准则", "规范"],
  "方式": ["方法", "途径"],
  "保持": ["维持", "保留"],
  "避免": ["防止", "回避"],
  "输出": ["产出", "结果"],
  "问题": ["疑问", "提问"],
  "内容": ["要素", "条目"],
  // ============ 中文单字常见替换 ===========
  "你": ["您"],
  "是": ["为"],
  "在": ["于"],
  "与": ["同"],
  "和": ["及", "并"],
  "或": ["或者", "抑或"],
  "可": ["能"],
  "会": ["能够", "可以"],
  "要": ["需"],
  "应": ["应当"],
  "请": ["烦请"],
  "好": ["佳"],
  "大": ["宏"],
  "小": ["微"],
  "新": ["全新"],
  "旧": ["原"],
  "高": ["优"],
  "低": ["次"],
  "多": ["众"],
  "少": ["寡"],
  "快": ["速"],
  "慢": ["缓"],
  "明": ["晰"],
  "暗": ["隐"],
  "真": ["实"],
  "假": ["虚"],
  "对": ["正确"],
  "错": ["误"],
  "有": ["存在"],
  "无": ["空"],
  "能": ["可以"],
  "做": ["进行"],
  "给": ["予以"],
  "让": ["使"],
  "如": ["若是"],
  "若": ["如果"],
  "但": ["然而"],
  "也": ["同样"],
  "都": ["皆"],
  "只": ["仅"],
  "次": ["回", "轮"],
  "次次": ["轮轮"],
  "提": ["问"],
  "问": ["询"],
  "答": ["回复"],
  "听": ["闻"],
  "说": ["述"],
  "想": ["思"],
  "看": ["观"],
  "知": ["晓"],
  "理": ["明"],
  "学": ["习"],
  "工": ["作"],
  "事": ["务"],
  "人": ["士"],
  "组": ["团"],
  "里": ["中"],
  "外": ["外部"],
  "内": ["内部"],
  "前": ["先前"],
  "后": ["后续"],
  "上": ["上方"],
  "下": ["下方"],
  "中": ["中段"],
  "左": ["左侧"],
  "右": ["右侧"],
  "点": ["要点"],
  "线": ["线路"],
  "面": ["层面"],
  "体": ["整体"],
  "系": ["系统"],
  "类": ["类别"],
  "种": ["种类"],
  "项": ["条目"],
  "个": ["位"],
  "些": ["若干"],
  "每": ["各"],
  "各": ["每个"],
  // ============ 标点/空白轻扰 ===========
  "，": ["、", " "],
  "。": [".", " "],
  "：": [":", " - "],
  "（": ["(", "（ "],
  "）": [")", " ）"],
  "；": [";"],
  "、": ["，"],
  "！": ["!"],
  "？": ["?"],
  " ": ["　", "  "],
  "\n": ["\n\n"],
  // ============ ASCII 字符 ===========
  "a": ["A", "@"],
  "b": ["B"],
  "c": ["C"],
  "d": ["D"],
  "e": ["E", "3"],
  "f": ["F"],
  "g": ["G"],
  "h": ["H"],
  "i": ["I", "1"],
  "j": ["J"],
  "k": ["K"],
  "l": ["L", "1"],
  "m": ["M"],
  "n": ["N"],
  "o": ["O", "0"],
  "p": ["P"],
  "q": ["Q"],
  "r": ["R"],
  "s": ["S", "$"],
  "t": ["T", "7"],
  "u": ["U"],
  "v": ["V"],
  "w": ["W"],
  "x": ["X"],
  "y": ["Y"],
  "z": ["Z"],
  "0": ["o", "O"],
  "1": ["l", "I"],
  "2": ["Z"],
  "3": ["E"],
  "4": ["A"],
  "5": ["S"],
  "6": ["G"],
  "7": ["T"],
  "8": ["B"],
  "9": ["g"],
};

/** 兜底替换池：不在 REPLACE_POOL 时从通用字符池抽取同类型替代 */
const FALLBACK_CN_CHARS = "的了是不在人有这中大为上个国我以要时和就来们生到作地于出而";
const FALLBACK_PUNCT = "， 。 ： ； 、 ？ ！ -".split(/\s+/);

/**
 * 阶段 3：对 basePrompt 做字符级小范围改写。
 *
 * 硬护栏：
 *   - 改动字符数 ≤ floor(baseLen * maxMutationRate)
 *   - 实际改动数 ≤ 上限，超过则截断
 *   - 输出 prompt 长度 == 输入 prompt 长度（保证等长替换，语义密度不变）
 *   - 每次运行都记录 changedPositions，便于审计
 *
 * @param basePrompt 原始 prompt
 * @param maxMutationRate 最大变异比例（默认 0.05）
 * @param seed 随机种子
 */
export function mutatePrompt(
  basePrompt: string,
  maxMutationRate: number,
  seed: number
): { prompt: string; changedPositions: number[]; actualRate: number } {
  if (maxMutationRate <= 0 || maxMutationRate > 0.05) {
    // 兜底护栏：绝对不允许超过 5%
    maxMutationRate = Math.min(maxMutationRate, 0.05);
  }
  if (maxMutationRate <= 0) {
    return { prompt: basePrompt, changedPositions: [], actualRate: 0 };
  }

  const rng = createRng(seed);
  const baseLen = basePrompt.length;
  const maxChanges = Math.max(1, Math.floor(baseLen * maxMutationRate));

  // 选出待变异的位置
  const allPositions = Array.from({ length: baseLen }, (_, i) => i);
  // 简单 Fisher-Yates 洗牌取前 maxChanges 个
  for (let i = allPositions.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [allPositions[i], allPositions[j]] = [allPositions[j], allPositions[i]];
  }
  const targetPositions = allPositions.slice(0, maxChanges).sort((a, b) => a - b);

  // 辅助：仅返回与原字符等长的候选
  const pickSameLength = (ch: string, pool: string[]): string | null => {
    const candidates = pool.filter((c) => c.length === ch.length);
    if (candidates.length === 0) return null;
    return candidates[Math.floor(rng() * candidates.length)];
  };

  const chars = basePrompt.split("");
  const changed: number[] = [];

  for (const pos of targetPositions) {
    const ch = chars[pos];
    const candidates = REPLACE_POOL[ch];
    let didChange = false;
    let newChar = ch;

    if (candidates && candidates.length > 0) {
      const replacement = pickSameLength(ch, candidates);
      if (replacement && replacement !== ch) {
        newChar = replacement;
        didChange = true;
      }
    } else if (/[a-zA-Z]/.test(ch) && rng() < 0.5) {
      // ASCII 字母：50% 概率切换大小写（保持单字符等长）
      newChar = ch === ch.toUpperCase() ? ch.toLowerCase() : ch.toUpperCase();
      didChange = true;
    } else if (/[\u4e00-\u9fa5]/.test(ch)) {
      // 中文字符：兜底从 FALLBACK_CN_CHARS 抽取（保持单字符等长）
      const idx = Math.floor(rng() * FALLBACK_CN_CHARS.length);
      const candidate = FALLBACK_CN_CHARS[idx];
      if (candidate !== ch) {
        newChar = candidate;
        didChange = true;
      }
    } else if (/[\s\p{P}]/u.test(ch)) {
      // 空白/标点：仅挑选等长字符
      const replacement = pickSameLength(ch, FALLBACK_PUNCT);
      if (replacement && replacement !== ch) {
        newChar = replacement;
        didChange = true;
      }
    }

    if (didChange && newChar !== ch) {
      chars[pos] = newChar;
      changed.push(pos);
    }
  }

  const newPrompt = chars.join("");
  // 护栏：必须等长
  if (newPrompt.length !== baseLen) {
    // 兜底：若仍然不等长，回滚到原 prompt
    return { prompt: basePrompt, changedPositions: [], actualRate: 0 };
  }
  const actualRate = newPrompt.length === 0 ? 0 : changed.length / newPrompt.length;

  // 二次护栏：实际改动比例不得超过 maxMutationRate
  if (actualRate > maxMutationRate + 1e-9) {
    let allowed = Math.floor(newPrompt.length * maxMutationRate);
    const trim: number[] = [];
    for (const p of changed) {
      if (allowed <= 0) break;
      trim.push(p);
      allowed--;
    }
    const keep = new Set(trim);
    const revert: string[] = newPrompt.split("");
    for (const p of changed) {
      if (!keep.has(p)) revert[p] = basePrompt[p];
    }
    return {
      prompt: revert.join(""),
      changedPositions: trim,
      actualRate: trim.length / newPrompt.length,
    };
  }

  return { prompt: newPrompt, changedPositions: changed, actualRate };
}

/**
 * 阶段 3 包装：构造 SkillVariant。
 */
export function mutate(
  parentVariant: SkillVariant | null,
  basePrompt: string,
  options: { skillName: string; maxMutationRate: number; seed: number }
): SkillVariant {
  const { prompt, changedPositions, actualRate } = mutatePrompt(
    basePrompt,
    options.maxMutationRate,
    options.seed
  );
  // 确定性 ID：完全基于 seed 派生，确保同一 seed 同一 id（便于审计）
  const idSeed = options.seed * 2654435761 >>> 0;
  const id = `var-${options.skillName}-${idSeed.toString(36)}`;

  return {
    id,
    parentId: parentVariant?.id ?? null,
    skillName: options.skillName,
    prompt,
    baseLength: basePrompt.length,
    changedPositions,
    mutationRate: Number(actualRate.toFixed(4)),
    createdAt: new Date().toISOString(),
    seed: options.seed,
  };
}

// =============================================================================
// 阶段 4：评分对比（Compare）
// =============================================================================

export interface CompareResult {
  baseline: BenchmarkScore;
  variant: BenchmarkScore;
  delta: number;
  /** 简化版统计显著性：变体均值与基线均值的 z-score（近似） */
  significance: number;
}

/**
 * 阶段 4：对基线和变体各跑 N 次 benchmark，输出对比。
 */
export function compareBenchmarks(
  state: PipelineState,
  baselinePrompt: string,
  variantPrompt: string,
  options: { runs: number; seed: number; baselineId: string; variantId: string }
): CompareResult {
  const baseline = benchmarkScore(state, baselinePrompt, {
    runs: options.runs,
    seed: options.seed,
    variantId: options.baselineId,
  });
  const variant = benchmarkScore(state, variantPrompt, {
    runs: options.runs,
    seed: options.seed + 10_000,
    variantId: options.variantId,
  });
  const delta = Number((variant.mean - baseline.mean).toFixed(4));

  // 简化 z-score：把两次均值之差除以合并标准差
  const pooledStd = Math.sqrt(
    (Math.pow(baseline.stddev, 2) + Math.pow(variant.stddev, 2)) / 2 || 1
  );
  const significance = Number((delta / (pooledStd || 1)).toFixed(4));

  return { baseline, variant, delta, significance };
}

// =============================================================================
// 阶段 5：优胜劣汰（Select）
// =============================================================================

/**
 * 阶段 5：选择决策。
 *
 * 规则：
 *   1. 变体均值 > 基线均值 + 0.5（避免噪声胜过基线） → 保留变体
 *   2. 变体均值 < 基线均值 - 0.5 → 回滚，保留基线
 *   3. 在 ±0.5 区间内 → 保守回滚（保留基线）
 *
 * 强制护栏：保留时基线快照仍写入 history，便于审计回滚。
 */
export function select(
  parent: BenchmarkScore,
  candidate: BenchmarkScore,
  variant: SkillVariant,
  options: { minDelta?: number } = {}
): SelectionDecision {
  const minDelta = options.minDelta ?? 0.5;
  const delta = candidate.mean - parent.mean;

  let winner: "candidate" | "parent";
  let reason: string;
  let rollbackApplied: boolean;

  if (delta > minDelta) {
    winner = "candidate";
    reason = `变体均值 ${candidate.mean.toFixed(2)} 显著高于基线 ${parent.mean.toFixed(
      2
    )} (Δ=+${delta.toFixed(2)} > ${minDelta})，保留变体`;
    rollbackApplied = false;
  } else if (delta < -minDelta) {
    winner = "parent";
    reason = `变体均值 ${candidate.mean.toFixed(2)} 低于基线 ${parent.mean.toFixed(
      2
    )} (Δ=${delta.toFixed(2)} < -${minDelta})，回滚到基线`;
    rollbackApplied = true;
  } else {
    winner = "parent";
    reason = `变体与基线均值差异 ${delta.toFixed(
      2
    )} 在 ±${minDelta} 区间内，保守回滚到基线避免噪声通过`;
    rollbackApplied = true;
  }

  // z-score（绝对值越大越显著）
  const pooledStd = Math.sqrt(
    (Math.pow(parent.stddev, 2) + Math.pow(candidate.stddev, 2)) / 2 || 1
  );
  const zScore = Number((delta / (pooledStd || 1)).toFixed(4));

  // 护栏：如果变体突变比例异常偏高，强制回滚（双保险）
  if (variant.mutationRate > 0.05 + 1e-9) {
    winner = "parent";
    reason = `变体突变率 ${(variant.mutationRate * 100).toFixed(
      2
    )}% 超过 5% 护栏，强制回滚`;
    rollbackApplied = true;
  }

  return {
    winner,
    reason,
    parentScore: parent,
    candidateScore: candidate,
    delta: Number(delta.toFixed(4)),
    zScore,
    rollbackApplied,
    keptAt: new Date().toISOString(),
  };
}

// =============================================================================
// 历史持久化（写入 blackboard/autoloop/history.json）
// =============================================================================

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..");
export const DEFAULT_AUTOLOOP_DIR = path.join(PROJECT_ROOT, "blackboard", "autoloop");
export const DEFAULT_HISTORY_PATH = path.join(DEFAULT_AUTOLOOP_DIR, "history.json");

/**
 * 读取已有历史（不存在则返回空数组）。
 */
async function readHistory(historyPath: string): Promise<AutoloopHistoryEntry[]> {
  try {
    const raw = await fs.readFile(historyPath, "utf-8");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : parsed.entries || [];
  } catch (err: any) {
    if (err.code === "ENOENT") return [];
    throw err;
  }
}

/**
 * 写入一条新历史条目（追加，不覆盖）。
 * 强制护栏：写入前保留上次快照（写入带 _previousHistory 字段）。
 */
export async function appendHistory(
  entry: AutoloopHistoryEntry,
  historyPath: string = DEFAULT_HISTORY_PATH
): Promise<void> {
  await fs.mkdir(path.dirname(historyPath), { recursive: true });
  const previous = await readHistory(historyPath);

  // 护栏：写入前快照上次条目数
  const payload = {
    schema: "loop-agent.autoloop.history/v1",
    generatedAt: new Date().toISOString(),
    totalRuns: previous.length + 1,
    _previousHistorySnapshot: previous.length,
    entries: [...previous, entry],
  };

  // 原子写：先写 .tmp，再 rename（避免半截文件）
  const tmp = `${historyPath}.tmp`;
  await fs.writeFile(tmp, JSON.stringify(payload, null, 2), "utf-8");
  await fs.rename(tmp, historyPath);
}

/**
 * 读取所有历史（用于审计）。
 */
export async function loadHistory(
  historyPath: string = DEFAULT_HISTORY_PATH
): Promise<AutoloopHistoryEntry[]> {
  return readHistory(historyPath);
}

// =============================================================================
// 主入口：runAutoloop（编排 5 个阶段）
// =============================================================================

export interface AutoloopRunResult {
  entry: AutoloopHistoryEntry;
  historyPath: string;
  keptPrompt: string;
}

/**
 * 端到端执行一次 autoloop：5 阶段 → 写历史。
 *
 * 不修改 state，不调用 spawn，不启动子进程，纯内存 + 文件。
 */
export async function runAutoloop(opts: AutoloopOptions): Promise<AutoloopRunResult> {
  const benchmarkRuns = opts.benchmarkRuns ?? 3;
  const maxMutationRate = opts.maxMutationRate ?? 0.05;
  const seed = opts.seed ?? Date.now();
  const historyPath = opts.historyPath ?? DEFAULT_HISTORY_PATH;

  if (maxMutationRate > 0.05) {
    throw new Error(
      `[Autoloop] 护栏触发：maxMutationRate=${maxMutationRate} 超过 0.05 上限`
    );
  }

  console.log("\n========================================");
  console.log("[Autoloop] 自进化循环 POC · 启动");
  console.log(`[Autoloop] target skill  : ${opts.skillName}`);
  console.log(`[Autoloop] benchmarkRuns : ${benchmarkRuns}`);
  console.log(`[Autoloop] mutationRate  : ${(maxMutationRate * 100).toFixed(1)}%`);
  console.log(`[Autoloop] seed          : ${seed}`);
  console.log("========================================");

  // ---- 阶段 1：标准化 ----
  console.log("\n[Stage 1] Standardize · 提取可重复度量指标");
  const snapshot = standardize(opts.state);
  console.log(`  - fingerprint    : ${snapshot.fingerprint}`);
  console.log(`  - totalTasks     : ${snapshot.normalized.totalTasks}`);
  console.log(
    `  - completionRate : ${(snapshot.normalized.completionRate * 100).toFixed(1)}%`
  );
  console.log(`  - phaseProgress  : ${(snapshot.normalized.phaseProgress * 100).toFixed(1)}%`);
  console.log(`  - gatesPassed    : ${snapshot.normalized.gatesPassed}/${snapshot.normalized.gatesTotal}`);

  // ---- 阶段 2：评估基准 ----
  console.log("\n[Stage 2] Benchmark · 基线 prompt 评估");
  const baseline = benchmarkScore(opts.state, opts.basePrompt, {
    runs: benchmarkRuns,
    seed,
    variantId: `baseline-${opts.skillName}`,
  });
  console.log(`  - mean           : ${baseline.mean.toFixed(2)}`);
  console.log(`  - stddev         : ${baseline.stddev.toFixed(2)}`);
  console.log(`  - scores         : [${baseline.runScores.join(", ")}]`);

  // ---- 阶段 3：变异探索 ----
  console.log("\n[Stage 3] Mutate · 生成候选变体 (≤5% 字符改动)");
  const parentVariant: SkillVariant | null = {
    id: `base-${opts.skillName}`,
    parentId: null,
    skillName: opts.skillName,
    prompt: opts.basePrompt,
    baseLength: opts.basePrompt.length,
    changedPositions: [],
    mutationRate: 0,
    createdAt: snapshot.createdAt,
    seed,
  };
  const variant = mutate(parentVariant, opts.basePrompt, {
    skillName: opts.skillName,
    maxMutationRate,
    seed: seed + 1,
  });
  console.log(`  - variant.id         : ${variant.id}`);
  console.log(`  - baseLength         : ${variant.baseLength}`);
  console.log(`  - changedPositions   : ${variant.changedPositions.length}`);
  console.log(`  - actualMutationRate : ${(variant.mutationRate * 100).toFixed(2)}%`);

  // 护栏：变异比例超过上限则中止（保护 Loop 不被破坏）
  if (variant.mutationRate > maxMutationRate + 1e-9) {
    throw new Error(
      `[Autoloop] 护栏触发：实际变异率 ${variant.mutationRate} 超过上限 ${maxMutationRate}`
    );
  }

  // ---- 阶段 4：评分对比 ----
  console.log("\n[Stage 4] Compare · 基线 vs 变体 多次评估");
  const compareResult = compareBenchmarks(
    opts.state,
    opts.basePrompt,
    variant.prompt,
    {
      runs: benchmarkRuns,
      seed,
      baselineId: `baseline-${opts.skillName}`,
      variantId: variant.id,
    }
  );
  console.log(`  - baseline.mean   : ${compareResult.baseline.mean.toFixed(2)}`);
  console.log(`  - variant.mean    : ${compareResult.variant.mean.toFixed(2)}`);
  console.log(`  - delta           : ${compareResult.delta >= 0 ? "+" : ""}${compareResult.delta.toFixed(2)}`);
  console.log(`  - significance    : ${compareResult.significance.toFixed(2)} (z)`);

  // ---- 阶段 5：优胜劣汰 ----
  console.log("\n[Stage 5] Select · 决策保留或回滚");
  const decision = select(compareResult.baseline, compareResult.variant, variant);
  console.log(`  - winner          : ${decision.winner}`);
  console.log(`  - rollbackApplied : ${decision.rollbackApplied}`);
  console.log(`  - reason          : ${decision.reason}`);

  const keptPrompt = decision.winner === "candidate" ? variant.prompt : opts.basePrompt;
  const status: AutoloopHistoryEntry["status"] = decision.rollbackApplied
    ? "rolled_back"
    : "kept";

  // ---- 写历史 ----
  // 确定性 run id：基于 seed 派生 + 时间戳哈希（时间戳固定到秒即可保证幂等）
  const runIdSeed = (seed * 2246822507) >>> 0;
  const entry: AutoloopHistoryEntry = {
    id: `run-${runIdSeed.toString(36)}-${snapshot.fingerprint.slice(0, 6)}`,
    timestamp: new Date().toISOString(),
    skillName: opts.skillName,
    stage1_snapshot: snapshot,
    stage2_baseline: compareResult.baseline,
    stage3_variant: variant,
    stage4_comparison: {
      baseline: compareResult.baseline,
      variant: compareResult.variant,
      delta: compareResult.delta,
      significance: compareResult.significance,
    },
    stage5_decision: decision,
    status,
    guardrails: {
      maxMutationRate,
      actualMutationRate: variant.mutationRate,
      snapshotPreserved: true,
      historyWritten: true,
    },
  };

  await appendHistory(entry, historyPath);
  console.log(`\n[Autoloop] ✓ 历史已写入 ${historyPath}`);
  console.log(`[Autoloop] 最终决策：${status === "kept" ? "保留变体" : "回滚到基线"}`);

  return { entry, historyPath, keptPrompt };
}

// =============================================================================
// 默认导出
// =============================================================================

export default {
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
};