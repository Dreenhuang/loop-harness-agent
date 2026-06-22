/**
 * =============================================================================
 * Loop Agent · Autoloop CLI 入口
 * TypeScript · Bun 可执行
 *
 * 用法：
 *   bun run loop-agent-engine/autoloop-cli.ts
 *   bun run loop-agent-engine/autoloop-cli.ts --skill brainstorming --runs 5
 *   bun run loop-agent-engine/autoloop-cli.ts --seed 42 --dry-run
 *   bun run loop-agent-engine/autoloop-cli.ts --history ./custom.json
 *
 * 参数：
 *   --skill       指定目标 Skill 名（默认 brainstorming）
 *   --runs        benchmark 运行次数（默认 3）
 *   --mutation    最大变异比例（默认 0.05，硬护栏上限）
 *   --seed        随机种子（默认 Date.now()）
 *   --state       自定义 state.json 路径（默认 blackboard/state.json）
 *   --history     自定义 history 输出路径
 *   --dry-run     只打印结果不写文件
 *   --reset       清空 history 后重跑
 *
 * 默认行为：复用当前 blackboard/state.json 作为输入上下文。
 * =============================================================================
 */

import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { OrchestratorStateMachine, type PipelineState } from "./orchestrator";
import {
  runAutoloop,
  loadHistory,
  type AutoloopHistoryEntry,
  DEFAULT_HISTORY_PATH,
} from "./autoloop";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..");

// =============================================================================
// 默认 Skill Prompt（brainstorming 示例）
// =============================================================================

/**
 * brainstorming Skill 的默认 prompt 模板。
 * 真实环境应从 .trae/skills/core/brainstorming/SKILL.md 读取；
 * 此处提供 POC 默认值，便于在没有 SKILL.md 时也能运行。
 */
const DEFAULT_BRAINSTORMING_PROMPT = `你是一名资深产品教练，正在与用户进行苏格拉底式需求澄清。

目标：通过一次一提问的方式，帮助用户明确以下内容：
- 真实用户是谁、典型使用场景
- 核心价值主张与成功指标
- 2-3 个替代方案及取舍
- 约束条件（预算/时间/合规）
- AI 能力需求与边界
- 验收标准与衡量方式

请保持中立、不臆测；每次只问一个问题，给用户留出充分表达空间。
回答使用中文，避免输出 Markdown 标题与代码块，方便后续解析。`;

// =============================================================================
// CLI 参数解析
// =============================================================================

interface CliArgs {
  skill: string;
  runs: number;
  mutation: number;
  seed: number;
  statePath: string | null;
  historyPath: string;
  dryRun: boolean;
  reset: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const out: CliArgs = {
    skill: "brainstorming",
    runs: 3,
    mutation: 0.05,
    seed: Date.now(),
    statePath: null,
    historyPath: DEFAULT_HISTORY_PATH,
    dryRun: false,
    reset: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = argv[i + 1];
    switch (a) {
      case "--skill":
        if (next) {
          out.skill = next;
          i++;
        }
        break;
      case "--runs":
        if (next) {
          out.runs = Math.max(1, parseInt(next, 10));
          i++;
        }
        break;
      case "--mutation":
        if (next) {
          const m = parseFloat(next);
          if (!Number.isNaN(m)) out.mutation = m;
          i++;
        }
        break;
      case "--seed":
        if (next) {
          out.seed = parseInt(next, 10) || out.seed;
          i++;
        }
        break;
      case "--state":
        if (next) {
          out.statePath = path.resolve(next);
          i++;
        }
        break;
      case "--history":
        if (next) {
          out.historyPath = path.resolve(next);
          i++;
        }
        break;
      case "--dry-run":
        out.dryRun = true;
        break;
      case "--reset":
        out.reset = true;
        break;
      case "--help":
      case "-h":
        printHelp();
        process.exit(0);
      default:
        // 忽略未知参数
        break;
    }
  }
  return out;
}

function printHelp() {
  console.log(`用法: bun run loop-agent-engine/autoloop-cli.ts [选项]

选项:
  --skill <name>     目标 Skill 名称（默认 brainstorming）
  --runs <n>         benchmark 运行次数（默认 3）
  --mutation <r>     最大变异比例（默认 0.05，硬上限）
  --seed <n>         随机种子（默认 Date.now()）
  --state <path>     PipelineState 输入路径
  --history <path>   history.json 输出路径
  --dry-run          只打印结果，不写文件
  --reset            清空 history 后重新跑
  -h, --help         显示帮助`);
}

// =============================================================================
// 主入口
// =============================================================================

async function main() {
  const args = parseArgs(process.argv.slice(2));

  console.log("[Autoloop CLI] ========================================");
  console.log(`[Autoloop CLI] skill    : ${args.skill}`);
  console.log(`[Autoloop CLI] runs     : ${args.runs}`);
  console.log(`[Autoloop CLI] mutation : ${(args.mutation * 100).toFixed(1)}%`);
  console.log(`[Autoloop CLI] seed     : ${args.seed}`);
  console.log(`[Autoloop CLI] dry-run  : ${args.dryRun}`);
  console.log(`[Autoloop CLI] reset    : ${args.reset}`);
  console.log("[Autoloop CLI] ========================================");

  // 1) 加载或初始化 PipelineState
  let state: PipelineState;
  try {
    state = args.statePath
      ? await loadStateFromPath(args.statePath)
      : await OrchestratorStateMachine.loadState();
  } catch (err: any) {
    console.warn(
      `[Autoloop CLI] 加载 state.json 失败：${err.message}，使用空 state 演示`
    );
    state = buildDemoState();
  }

  // 2) 如果当前 state 没有任何 task，注入 demo 任务让 benchmark 有数据可看
  if (Object.keys(state.tasks).length === 0) {
    console.log("[Autoloop CLI] 当前 state 为空，注入演示任务");
    state = buildDemoState();
  }

  // 3) 选择 basePrompt
  const basePrompt = await resolveBasePrompt(args.skill);
  console.log(`[Autoloop CLI] basePrompt 长度: ${basePrompt.length} chars`);

  // 4) reset 处理
  if (args.reset && !args.dryRun) {
    try {
      await fs.unlink(args.historyPath);
      console.log(`[Autoloop CLI] ✓ 已重置 ${args.historyPath}`);
    } catch (err: any) {
      if (err.code !== "ENOENT") {
        console.warn(`[Autoloop CLI] 重置 history 失败：${err.message}`);
      }
    }
  } else {
    const existing = await loadHistory(args.historyPath).catch(() => []);
    if (existing.length > 0) {
      console.log(`[Autoloop CLI] 历史已有 ${existing.length} 条 run，本次追加`);
    }
  }

  // 5) dry-run 跳过写入
  if (args.dryRun) {
    console.log("\n[Autoloop CLI] DRY-RUN 模式：不写入文件");
    // 仍然执行 5 阶段打印，但不落盘
    const result = await runAutoloop({
      state,
      skillName: args.skill,
      basePrompt,
      benchmarkRuns: args.runs,
      maxMutationRate: args.mutation,
      seed: args.seed,
      historyPath: path.join(
        path.dirname(args.historyPath),
        "_dryrun.history.json"
      ),
    });
    printFinalSummary(result.entry);
    return;
  }

  // 6) 真正执行
  const result = await runAutoloop({
    state,
    skillName: args.skill,
    basePrompt,
    benchmarkRuns: args.runs,
    maxMutationRate: args.mutation,
    seed: args.seed,
    historyPath: args.historyPath,
  });

  printFinalSummary(result.entry);

  // 7) 退出码：rolled_back 用 0（业务上视为成功路径），kept 同理
  //     只有护栏错误才用非零（已被 throw）。
  process.exit(0);
}

function printFinalSummary(entry: AutoloopHistoryEntry) {
  console.log("\n[Autoloop CLI] ====== 最终摘要 ======");
  console.log(`  run.id            : ${entry.id}`);
  console.log(`  skill             : ${entry.skillName}`);
  console.log(`  status            : ${entry.status}`);
  console.log(
    `  baseline.mean     : ${entry.stage4_comparison.baseline.mean.toFixed(2)}`
  );
  console.log(
    `  variant.mean      : ${entry.stage4_comparison.variant.mean.toFixed(2)}`
  );
  console.log(
    `  delta             : ${
      entry.stage4_comparison.delta >= 0 ? "+" : ""
    }${entry.stage4_comparison.delta.toFixed(2)}`
  );
  console.log(`  significance (z)  : ${entry.stage4_comparison.significance}`);
  console.log(`  decision.winner   : ${entry.stage5_decision.winner}`);
  console.log(`  decision.reason   : ${entry.stage5_decision.reason}`);
  console.log(
    `  guardrails.mutation: ${(entry.guardrails.actualMutationRate * 100).toFixed(
      2
    )}% / ≤${(entry.guardrails.maxMutationRate * 100).toFixed(0)}%`
  );
  console.log("======================================");
}

// =============================================================================
// 辅助函数
// =============================================================================

async function loadStateFromPath(p: string): Promise<PipelineState> {
  const raw = await fs.readFile(p, "utf-8");
  return JSON.parse(raw);
}

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
    const isFailed = i === 4; // 让 benchmark 看到一点失败
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
    phase: phases[3] as PipelineState["phase"], // 当前在 ARCHITECTURE
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

/**
 * 解析 basePrompt：
 *   - 优先尝试读取 .trae/skills/core/<skill>/SKILL.md
 *   - 找不到则使用内置默认 prompt
 */
async function resolveBasePrompt(skill: string): Promise<string> {
  const skillFile = path.join(
    PROJECT_ROOT,
    ".trae",
    "skills",
    "core",
    skill,
    "SKILL.md"
  );
  try {
    const content = await fs.readFile(skillFile, "utf-8");
    console.log(`[Autoloop CLI] 从 ${skillFile} 读取 basePrompt`);
    return content;
  } catch {
    console.log(
      `[Autoloop CLI] 未找到 ${skillFile}，使用内置 DEFAULT_BRAINSTORMING_PROMPT`
    );
    return DEFAULT_BRAINSTORMING_PROMPT;
  }
}

// =============================================================================
// 运行
// =============================================================================

main().catch((err) => {
  console.error("[Autoloop CLI] 运行失败:", err);
  process.exit(1);
});