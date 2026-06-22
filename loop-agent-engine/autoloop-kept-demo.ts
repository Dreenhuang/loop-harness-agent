/**
 * 演示「kept」路径：
 *   - 使用弱化 baseline prompt（缺失关键词，过度感叹号）
 *   - 变异可能恰好修掉一个感叹号 / 增加一个关键词 → 评分上升 → kept
 *
 * bun run loop-agent-engine/autoloop-kept-demo.ts
 */
import { runAutoloop } from "./autoloop";
import { OrchestratorStateMachine, type PipelineState } from "./orchestrator";
import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..");

// 故意构造低质量 baseline：缺少关键词、含多余感叹号
const WEAK_BASELINE = `做需求的，写好就行了啊！！！列出来吧！每次问一个吧！搞定收工！`;

function buildState(): PipelineState {
  const now = new Date().toISOString();
  return {
    phase: "REQUIREMENTS",
    tasks: {
      a: {
        id: "a",
        phase: "REQUIREMENTS",
        agentType: "requirements",
        status: "PENDING",
        inputPaths: [],
        outputPath: "x",
        acceptanceCriteria: {},
        attempts: 0,
        maxAttempts: 3,
        dependencies: [],
        worktree: false,
      } as any,
    },
    dependencies: {},
    budget: {
      maxCost: 100,
      currentCost: 0.1,
      maxIterations: 200,
      currentIteration: 1,
      maxAttemptsPerTask: 3,
      noProgressThreshold: 3,
      noProgressCount: 0,
    },
    qualityGates: {
      codeReview: "NOT_STARTED",
      performance: "NOT_STARTED",
      testing: "NOT_STARTED",
      final: "NOT_STARTED",
    },
    startedAt: now,
    updatedAt: now,
    projectName: "autoloop-kept-demo",
  };
}

async function main() {
  const state = buildState();
  const historyPath = path.join(PROJECT_ROOT, "blackboard", "autoloop", "history.json");

  console.log("=== Autoloop · kept 路径演示 ===");
  console.log(`baseline 字符数: ${WEAK_BASELINE.length}`);
  console.log("");

  // 跑若干 seed 期望命中 kept（弱 baseline 让 prompt 维度权重凸显）
  let keptCount = 0;
  let totalCount = 0;
  for (const seed of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) {
    const result = await runAutoloop({
      state,
      skillName: "brainstorming",
      basePrompt: WEAK_BASELINE,
      benchmarkRuns: 5,
      maxMutationRate: 0.05,
      seed,
      historyPath,
    });
    totalCount++;
    if (result.entry.status === "kept") keptCount++;
    console.log("");
  }

  console.log(`\n=== kept 命中率: ${keptCount}/${totalCount} ===`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});