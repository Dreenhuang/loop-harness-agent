/**
 * 多次运行 autoloop POC 用于演示 kept / rolled_back 两种结果
 * bun run loop-agent-engine/autoloop-multirun.ts
 */
import { runAutoloop } from "./autoloop";
import { OrchestratorStateMachine, type PipelineState } from "./orchestrator";
import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..");

const DEFAULT_PROMPT = `你是一名资深产品教练，正在与用户进行苏格拉底式需求澄清。

目标：通过一次一提问的方式，帮助用户明确以下内容：
- 真实用户是谁、典型使用场景
- 核心价值主张与成功指标
- 2-3 个替代方案及取舍
- 约束条件（预算/时间/合规）
- AI 能力需求与边界
- 验收标准与衡量方式

请保持中立、不臆测；每次只问一个问题，给用户留出充分表达空间。
回答使用中文，避免输出 Markdown 标题与代码块，方便后续解析。`;

function buildDemoState(): PipelineState {
  const now = new Date().toISOString();
  const tasks: Record<string, any> = {};
  const phases = [
    "INIT",
    "REQUIREMENTS",
    "DESIGN",
    "ARCHITECTURE",
    "DEVELOPMENT",
    "QUALITY_GATES",
  ];
  const agents = [
    "orchestrator",
    "requirements",
    "ux",
    "architect",
    "backend",
    "reviewer",
  ];
  for (let i = 0; i < phases.length; i++) {
    const id = `${phases[i].toLowerCase()}-${agents[i]}-${i}`;
    const isDone = i < 3;
    const isFailed = i === 4;
    tasks[id] = {
      id,
      phase: phases[i],
      agentType: agents[i],
      status: isDone ? "DONE" : isFailed ? "FAILED" : "PENDING",
      inputPaths: [],
      outputPath: `./blackboard/${phases[i].toLowerCase()}/output.json`,
      acceptanceCriteria: {},
      attempts: isFailed ? 3 : 0,
      maxAttempts: 3,
      dependencies: i === 0 ? [] : [`${phases[i - 1].toLowerCase()}-${agents[i - 1]}-${i - 1}`],
      worktree: false,
      ...(isDone ? { completedAt: now } : {}),
    };
  }
  return {
    phase: phases[3] as PipelineState["phase"],
    tasks,
    dependencies: {},
    budget: {
      maxCost: 100,
      currentCost: 24.7,
      maxIterations: 200,
      currentIteration: 12,
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
    projectName: "autoloop-poc-demo",
  };
}

async function main() {
  // 重置 history
  const historyPath = path.join(PROJECT_ROOT, "blackboard", "autoloop", "history.json");
  try {
    await fs.unlink(historyPath);
  } catch {}

  const state = buildDemoState();
  console.log("=== Autoloop 多轮运行（POC 演示）===\n");

  const seeds = [42, 100, 7, 999, 13, 2024];
  const summary: Array<{ seed: number; mutation: number; delta: number; status: string }> = [];

  for (const seed of seeds) {
    const result = await runAutoloop({
      state,
      skillName: "brainstorming",
      basePrompt: DEFAULT_PROMPT,
      benchmarkRuns: 5,
      maxMutationRate: 0.05,
      seed,
      historyPath,
    });
    summary.push({
      seed,
      mutation: result.entry.stage3_variant.mutationRate,
      delta: result.entry.stage4_comparison.delta,
      status: result.entry.status,
    });
    console.log("");
  }

  console.log("\n=== 汇总 ===");
  console.table(summary);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});