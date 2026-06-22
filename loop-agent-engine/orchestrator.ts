/**
 * =============================================================================
 * Loop Agent · Orchestrator 状态机核心实现
 * TypeScript · Bun 可执行
 * 完全对齐 Trae Solo 工程实现指南 v1.0（第三章）
 * =============================================================================
 *
 * 启动方式：
 *   bun run loop-agent-engine/orchestrator.ts
 *   或 bun run loop-agent-engine/cli.ts
 *
 * 文档参考：
 *   - Trae Solo 工程实现指南：PRD→生产全链路自动化系统.md 第 3 章
 *   - PRD→生产 全链路自动化开发标准化流程 v1.0.md 第 3 章
 *   - Agent Loop Engineering 深度解读报告.md
 */

import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";

// =============================================================================
// 类型定义
// =============================================================================

export type Phase =
  | "INIT"
  | "REQUIREMENTS"
  | "DESIGN"
  | "ARCHITECTURE"
  | "DEVELOPMENT"
  | "QUALITY_GATES"
  | "KNOWLEDGE"
  | "DOCUMENTATION"
  | "FINAL_REVIEW"
  | "DEPLOY"
  | "DONE";

export type TaskStatus = "PENDING" | "RUNNING" | "DONE" | "FAILED" | "BLOCKED";
export type GateStatus = "NOT_STARTED" | "RUNNING" | "PASSED" | "FAILED";
export type NodeStatus = "NOT_STARTED" | "PENDING" | "RUNNING" | "DONE" | "FAILED" | "BLOCKED";

export interface BudgetState {
  maxCost: number;
  currentCost: number;
  maxIterations: number;
  currentIteration: number;
  maxAttemptsPerTask: number;
  noProgressThreshold: number;
  noProgressCount: number;
}

export interface QualityGates {
  codeReview: GateStatus;
  performance: GateStatus;
  testing: GateStatus;
  final: GateStatus;
}

export interface TaskState {
  id: string;
  phase: Phase;
  agentType: string;
  status: TaskStatus;
  inputPaths: string[];
  outputPath: string;
  acceptanceCriteria: Record<string, any>;
  attempts: number;
  maxAttempts: number;
  dependencies: string[];
  startedAt?: string;
  completedAt?: string;
  error?: string;
  lastErrorFingerprint?: string;
  worktree: boolean;
}

export interface PipelineState {
  phase: Phase;
  tasks: Record<string, TaskState>;
  dependencies: Record<string, string[]>;
  budget: BudgetState;
  qualityGates: QualityGates;
  startedAt: string;
  updatedAt: string;
  projectName: string;
  prdPath?: string;
}

export interface AgentInput {
  taskId: string;
  inputPaths: string[];
  outputPath: string;
  acceptanceCriteria: Record<string, any>;
  // 严格遵循最小输入原则：不传内容，只传路径
}

// =============================================================================
// 融合验收类型定义（v1.1 新增）
// =============================================================================

export interface HarnessProtocol {
  phase: Phase;
  project_type: string;
  task_type: string;
  role: string;
  required_harness_steps: string[];
  required_skills: string[];
  required_artifacts: string[];
  evidence_requirements: string[];
}

export interface ArtifactRecord {
  artifact_name: string;
  artifact_path: string;
  owner_role: string;
  phase: string;
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "MISSING";
  version: string;
  updated_at: string;
}

export interface EvidenceRecord {
  evidence_type: string;
  source_role: string;
  task_id: string;
  command: string;
  result_summary: string;
  attachments: string[];
  timestamp: string;
}

export interface GateComplianceResult {
  gate_id: string;
  pass: boolean;
  blockers: string[];
  missing_artifacts: string[];
  missing_evidence: string[];
  discipline_violations: string[];
  veto_triggered: boolean;
  veto_reasons: string[];
}

export interface FusionMetrics {
  artifact_completion_rate: number;
  evidence_coverage_rate: number;
  tdd_execution_rate: number;
  review_closure_rate: number;
  harness_protocol_injection_rate: number;
}

// =============================================================================
// 状态机核心
// =============================================================================

export class OrchestratorStateMachine {
  // 基于当前模块位置解析项目根目录，保证无论从哪个 cwd 启动都能找到 blackboard
  private readonly PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  private readonly BLACKBOARD_DIR = path.join(this.PROJECT_ROOT, "blackboard");
  private readonly BLACKBOARD_PATH = path.join(this.BLACKBOARD_DIR, "state.json");
  private readonly TASKS_DIR = path.join(this.BLACKBOARD_DIR, "tasks");
  private readonly WORKER_SCRIPT = path.join(path.dirname(fileURLToPath(import.meta.url)), "agent-worker.ts");
  private readonly MAX_PARALLEL_TASKS = 16;
  private previousErrorFingerprints: string[] = [];

  constructor(private readonly config: PipelineState) {
    if (!config.startedAt) {
      config.startedAt = new Date().toISOString();
    }
    config.updatedAt = new Date().toISOString();
  }

  /**
   * 调度主循环（由 Trae React 模式触发）
   */
  async tick(): Promise<void> {
    console.log(`\n[Tick] Phase: ${this.config.phase} | Iteration: ${this.config.budget.currentIteration}`);

    // 1. 三道硬刹车检查
    if (!this.hasBudget(this.config)) {
      await this.emergencyStop("三道硬刹车之一触发");
      return;
    }

    // 2. 检查当前 Phase 是否完成
    if (this.isPhaseComplete(this.config)) {
      await this.advancePhase(this.config);
    }

    // 3. 调度下一批任务（并行扇出）
    const readyTasks = this.getReadyTasks(this.config);
    if (readyTasks.length > 0) {
      await this.spawnAgents(readyTasks);
    } else {
      console.log("[Tick] 没有 READY 任务，等待依赖完成...");
    }

    // 4. 更新状态并保存
    this.config.budget.currentIteration++;
    this.config.updatedAt = new Date().toISOString();
    await this.saveState(this.config);
  }

  /**
   * 三道硬刹车：预算、迭代、无进展检测
   */
  private hasBudget(state: PipelineState): boolean {
    // 第 1 道：迭代次数
    if (state.budget.currentIteration >= state.budget.maxIterations) {
      console.error(`[HardBrake] 达到最大迭代次数 ${state.budget.maxIterations}`);
      return false;
    }

    // 第 2 道：预算
    if (state.budget.currentCost >= state.budget.maxCost) {
      console.error(`[HardBrake] 预算耗尽 $${state.budget.currentCost}/$${state.budget.maxCost}`);
      return false;
    }

    // 第 3 道：无进展检测
    if (state.budget.noProgressCount >= state.budget.noProgressThreshold) {
      console.error(`[HardBrake] 连续 ${state.budget.noProgressCount} 轮无进展`);
      return false;
    }

    return true;
  }

  /**
   * 检查 Phase 是否完成
   */
  private isPhaseComplete(state: PipelineState): boolean {
    const phaseTasks = Object.values(state.tasks).filter(
      (t) => t.phase === state.phase
    );
    if (phaseTasks.length === 0) return true;
    return phaseTasks.every((t) => t.status === "DONE");
  }

  /**
   * 推进到下一 Phase
   */
  private async advancePhase(state: PipelineState): Promise<void> {
    const phaseOrder: Phase[] = [
      "INIT", "REQUIREMENTS", "DESIGN", "ARCHITECTURE", "DEVELOPMENT",
      "QUALITY_GATES", "KNOWLEDGE", "DOCUMENTATION", "FINAL_REVIEW", "DEPLOY", "DONE"
    ];
    const currentIdx = phaseOrder.indexOf(state.phase);
    if (currentIdx < phaseOrder.length - 1) {
      const nextPhase = phaseOrder[currentIdx + 1];
      console.log(`[Phase] ${state.phase} → ${nextPhase}`);
      state.phase = nextPhase;
    }
  }

  /**
   * 获取所有依赖已满足的就绪任务
   */
  private getReadyTasks(state: PipelineState): TaskState[] {
    return Object.values(state.tasks).filter((task) => {
      if (task.status !== "PENDING") return false;

      // 检查所有依赖是否完成
      const deps = task.dependencies || [];
      const allDepsDone = deps.every(
        (depId) => state.tasks[depId]?.status === "DONE"
      );

      // 任务必须在当前 Phase
      const inCurrentPhase = task.phase === state.phase;

      return allDepsDone && inCurrentPhase;
    });
  }

  /**
   * 并行扇出：分派任务给 Specialist Agent
   *
   * 实现说明：
   * 1. 为每个任务生成 blackboard/tasks/{taskId}.json 描述文件
   * 2. 通过 child_process.spawn 启动 loop-agent-engine/agent-worker.ts 子进程
   * 3. 子进程模拟执行（sleep 1s）后写回任务文件
   * 4. 主进程监听 exit 事件，调用 onTaskComplete 更新 PipelineState
   * 5. worker 子进程以 detached=true 启动，并通过 unref() 释放父进程引用，
   *    确保 Orchestrator 主进程不会被 worktree 隔离子进程阻塞退出
   * 6. 默认通过环境变量 LOOP_AGENT_WORKTREE_DRY_RUN=1 强制 worker 进入 dry-run 模式，
   *    Phase D 之前不创建真实 git worktree（仅打印计划动作）
   */
  private async spawnAgents(tasks: TaskState[]): Promise<void> {
    const batch = tasks.slice(0, this.MAX_PARALLEL_TASKS);
    console.log(`[Spawn] 扇出 ${batch.length} 个并行任务（最多 ${this.MAX_PARALLEL_TASKS}）`);

    // 确保任务目录存在
    await fs.mkdir(this.TASKS_DIR, { recursive: true });

    for (const task of batch) {
      task.status = "RUNNING";
      task.startedAt = new Date().toISOString();

      // v1.1: 生成 Harness 执行协议
      const harnessProtocol = HarnessPolicyEngine.generateProtocol(
        task.phase,
        "web-fullstack",
        "feature-development",
        task.agentType
      );
      console.log(`  → [Harness] Protocol: steps=${harnessProtocol.required_harness_steps.join(",") || "none"}, artifacts=${harnessProtocol.required_artifacts.join(",") || "none"}`);

      // 构造 Agent 最小输入
      const input: AgentInput = {
        taskId: task.id,
        inputPaths: task.inputPaths,
        outputPath: task.outputPath,
        acceptanceCriteria: task.acceptanceCriteria,
      };

      console.log(`  → [${task.agentType}] Task ${task.id} (attempts=${task.attempts}, worktree=${task.worktree})`);
      console.log(`     Input: ${task.inputPaths.join(", ")}`);
      console.log(`     Output: ${task.outputPath}`);

      // 写入任务描述文件
      const taskFile = path.join(this.TASKS_DIR, `${task.id}.json`);
      const taskPayload = {
        ...input,
        agentType: task.agentType,
        phase: task.phase,
        status: "RUNNING",
        startedAt: task.startedAt,
        worktree: task.worktree,
      };
      await fs.writeFile(taskFile, JSON.stringify(taskPayload, null, 2));

      // 启动 worker 子进程（Bun 运行时）
      // 使用 process.execPath 确保使用与当前进程相同的 Bun 可执行文件，避免依赖 PATH
      // detached=true 让 worker 子进程拥有独立的进程组，unref() 让父进程不被 worker 阻塞
      const worker = spawn(process.execPath, [this.WORKER_SCRIPT, task.id], {
        stdio: "inherit",
        detached: true,
        env: {
          ...process.env,
          // v1.2.1：默认真实模式（Phase B 7/7 PASS 后启用）
          // 设置 LOOP_AGENT_WORKTREE_DRY_RUN=1 可强制回退到 dry-run
          LOOP_AGENT_WORKTREE_DRY_RUN:
            process.env.LOOP_AGENT_WORKTREE_DRY_RUN,
        },
      });
      worker.unref?.();

      worker.on("error", (err) => {
        console.error(`[Spawn] Worker for task ${task.id} failed to start:`, err.message);
        this.onTaskComplete(task.id, false, `Worker spawn error: ${err.message}`).catch(console.error);
      });

      worker.on("exit", (code) => {
        const success = code === 0;
        if (!success) {
          console.error(`[Spawn] Worker for task ${task.id} exited with code ${code}`);
        }
        this.onTaskComplete(task.id, success, success ? undefined : `Worker exited with code ${code}`).catch(console.error);
      });
    }
  }

  /**
   * 任务完成回调
   */
  async onTaskComplete(taskId: string, success: boolean, error?: string): Promise<void> {
    const task = this.config.tasks[taskId];
    if (!task) {
      console.error(`[Callback] 未知任务 ${taskId}`);
      return;
    }

    if (success) {
      task.status = "DONE";
      task.completedAt = new Date().toISOString();
      this.config.budget.noProgressCount = 0;  // 重置无进展计数
      console.log(`[Callback] Task ${taskId} ✓ DONE`);
    } else {
      task.attempts++;
      const errorFingerprint = this.hashError(error || "unknown");
      task.lastErrorFingerprint = errorFingerprint;

      if (task.attempts >= task.maxAttempts) {
        task.status = "FAILED";
        task.error = error;
        this.config.budget.noProgressCount++;
        console.error(`[Callback] Task ${taskId} ✗ FAILED (attempts=${task.attempts})`);
      } else {
        task.status = "PENDING";  // 重试
        this.config.budget.noProgressCount++;
        console.warn(`[Callback] Task ${taskId} retry ${task.attempts}/${task.maxAttempts}`);
      }
    }

    this.config.updatedAt = new Date().toISOString();
    await this.saveState(this.config);
  }

  /**
   * 紧急停止
   */
  private async emergencyStop(reason: string): Promise<void> {
    console.error(`\n[EMERGENCY STOP] ${reason}`);
    this.config.phase = "DONE";
    this.config.updatedAt = new Date().toISOString();
    await this.saveState(this.config);
  }

  /**
   * 错误指纹（用于无进展检测）
   */
  private hashError(error: string): string {
    let hash = 0;
    for (let i = 0; i < error.length; i++) {
      hash = (hash << 5) - hash + error.charCodeAt(i);
      hash |= 0;
    }
    return hash.toString(36);
  }

  /**
   * 保存状态到黑板（真实写入 blackboard/state.json）
   */
  private async saveState(state: PipelineState): Promise<void> {
    await fs.mkdir(this.BLACKBOARD_DIR, { recursive: true });
    await fs.writeFile(
      this.BLACKBOARD_PATH,
      JSON.stringify(state, null, 2),
      "utf-8"
    );
    console.log(`[Persist] state.json 已更新 (phase=${state.phase}, iter=${state.budget.currentIteration})`);
  }

  /**
   * 从黑板加载状态；不存在时返回初始状态并自动创建目录
   */
  static async loadState(loadPath?: string): Promise<PipelineState> {
    const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
    const blackboardDir = path.join(projectRoot, "blackboard");
    const statePath = loadPath ? path.resolve(loadPath) : path.join(blackboardDir, "state.json");

    try {
      const data = await fs.readFile(statePath, "utf-8");
      const state = JSON.parse(data) as PipelineState;
      console.log(`[Load] 从 ${statePath} 恢复状态 (phase=${state.phase}, iter=${state.budget.currentIteration})`);
      return state;
    } catch (err: any) {
      if (err.code === "ENOENT") {
        // 自动创建 blackboard 与 tasks 目录
        await fs.mkdir(blackboardDir, { recursive: true });
        await fs.mkdir(path.join(blackboardDir, "tasks"), { recursive: true });
        console.log(`[Load] 状态文件不存在，已创建目录并返回初始状态`);
        return OrchestratorStateMachine.createInitialState();
      }
      throw err;
    }
  }

  /**
   * 创建初始 PipelineState
   */
  private static createInitialState(): PipelineState {
    return {
      phase: "INIT",
      tasks: {},
      dependencies: {},
      budget: {
        maxCost: 100.0,
        currentCost: 0.0,
        maxIterations: 200,
        currentIteration: 0,
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
      startedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      projectName: "untitled",
    };
  }
}

// =============================================================================
// Harness Policy Engine（融合验收执行协议引擎）
// =============================================================================

const HARNESS_PHASE_MAPPING: Record<string, Partial<HarnessProtocol>> = {
  INIT: {
    required_harness_steps: [],
    required_skills: ["pre-flight-check"],
    required_artifacts: [],
    evidence_requirements: [],
  },
  REQUIREMENTS: {
    required_harness_steps: ["step1"],
    required_skills: ["brainstorming", "product-spec-builder"],
    required_artifacts: ["Product-Spec.md"],
    evidence_requirements: ["requirement_clarification_record"],
  },
  DESIGN: {
    required_harness_steps: ["step2", "step3"],
    required_skills: ["web-design-guidelines"],
    required_artifacts: ["Design-Brief.md", "UI-Design.md", "Component-Library.md"],
    evidence_requirements: ["design_review_record"],
  },
  ARCHITECTURE: {
    required_harness_steps: ["step5_prefix"],
    required_skills: [],
    required_artifacts: ["Architecture.md", "API-Spec.md"],
    evidence_requirements: ["tech_stack_comparison", "risk_assessment_record"],
  },
  DEVELOPMENT: {
    required_harness_steps: ["step5", "step6"],
    required_skills: ["writing-plans", "test-driven-development", "subagent-driven-development", "using-git-worktrees"],
    required_artifacts: ["DEV-PLAN.md"],
    evidence_requirements: ["failing_test", "passing_test", "refactor_evidence"],
  },
  QUALITY_GATES: {
    required_harness_steps: ["step7", "step8", "step9"],
    required_skills: ["verification-before-completion", "quality-gate", "requesting-code-review", "receiving-code-review"],
    required_artifacts: ["Quality-Check-Report.md", "Test-Report.md", "Code-Review-Report.md"],
    evidence_requirements: ["verification_commands", "review_feedback"],
  },
  KNOWLEDGE: {
    required_harness_steps: [],
    required_skills: ["knowledge-extract"],
    required_artifacts: [],
    evidence_requirements: [],
  },
  DOCUMENTATION: {
    required_harness_steps: [],
    required_skills: [],
    required_artifacts: [],
    evidence_requirements: [],
  },
  FINAL_REVIEW: {
    required_harness_steps: ["step11"],
    required_skills: ["verification-before-completion"],
    required_artifacts: ["UX-Review-Report.md", "Release-Notes.md"],
    evidence_requirements: ["deploy_smoke_test"],
  },
  DEPLOY: {
    required_harness_steps: ["step11"],
    required_skills: ["verification-before-completion", "finishing-a-development-branch"],
    required_artifacts: [],
    evidence_requirements: ["deploy_smoke_test", "build_verification"],
  },
};

export class HarnessPolicyEngine {
  /**
   * 根据当前 Phase 和任务类型生成 Harness 执行协议
   */
  static generateProtocol(
    phase: Phase,
    projectType: string = "web-fullstack",
    taskType: string = "feature-development",
    role: string = ""
  ): HarnessProtocol {
    const mapping = HARNESS_PHASE_MAPPING[phase] || {
      required_harness_steps: [],
      required_skills: [],
      required_artifacts: [],
      evidence_requirements: [],
    };

    return {
      phase,
      project_type: projectType,
      task_type: taskType,
      role,
      required_harness_steps: mapping.required_harness_steps || [],
      required_skills: mapping.required_skills || [],
      required_artifacts: mapping.required_artifacts || [],
      evidence_requirements: mapping.evidence_requirements || [],
    };
  }

  /**
   * 检查指定 Phase 的强制工件是否齐全
   */
  static checkArtifactCompleteness(
    phase: Phase,
    artifactRegistry: Record<string, ArtifactRecord>
  ): { complete: boolean; missing: string[] } {
    const mapping = HARNESS_PHASE_MAPPING[phase];
    if (!mapping || !mapping.required_artifacts) {
      return { complete: true, missing: [] };
    }

    const missing = mapping.required_artifacts.filter(
      (artifact) =>
        !artifactRegistry[artifact] ||
        artifactRegistry[artifact].status !== "COMPLETED"
    );

    return { complete: missing.length === 0, missing };
  }

  /**
   * 检查指定 Phase 的证据是否充分
   */
  static checkEvidenceSufficiency(
    phase: Phase,
    evidenceRegistry: Record<string, EvidenceRecord[]>
  ): { sufficient: boolean; missing: string[] } {
    const mapping = HARNESS_PHASE_MAPPING[phase];
    if (!mapping || !mapping.evidence_requirements) {
      return { sufficient: true, missing: [] };
    }

    const missing = mapping.evidence_requirements.filter(
      (evidenceType) =>
        !evidenceRegistry[evidenceType] ||
        evidenceRegistry[evidenceType].length === 0
    ) ?? [];

    return { sufficient: missing.length === 0, missing };
  }
}

// =============================================================================
// Gate 合规检查器
// =============================================================================

const VETO_ITEMS = [
  "工件链不完整",
  "Gate 可被绕过",
  "无法基于黑板恢复",
  "demo 级结果伪装生产级",
  "Token 失控无法收敛",
  "无人值守空转或伪完成",
];

const MANDATORY_ARTIFACTS_FOR_FINAL = [
  "Product-Spec.md",
  "Design-Brief.md",
  "UI-Design.md",
  "Component-Library.md",
  "Architecture.md",
  "API-Spec.md",
  "DEV-PLAN.md",
  "Quality-Check-Report.md",
  "Test-Report.md",
  "Code-Review-Report.md",
  "UX-Review-Report.md",
  "Release-Notes.md",
];

const MANDATORY_EVIDENCE_FOR_FINAL = [
  "failing_test",
  "passing_test",
  "verification_commands",
  "review_feedback",
  "deploy_smoke_test",
];

export class GateComplianceChecker {
  /**
   * Gate 1 合规检查：代码质量 + 证据链 + 工件完整性
   */
  static checkGate1(
    artifactRegistry: Record<string, ArtifactRecord>,
    evidenceRegistry: Record<string, EvidenceRecord[]>
  ): GateComplianceResult {
    const blockers: string[] = [];
    const missingArtifacts: string[] = [];
    const missingEvidence: string[] = [];
    const disciplineViolations: string[] = [];

    // 检查 DEV-PLAN.md
    const devPlanCheck = HarnessPolicyEngine.checkArtifactCompleteness(
      "DEVELOPMENT",
      artifactRegistry
    );
    if (!devPlanCheck.complete) {
      missingArtifacts.push(...devPlanCheck.missing);
      blockers.push(`缺少开发工件: ${devPlanCheck.missing.join(", ")}`);
    }

    // 检查 TDD 证据
    const tddEvidence = ["failing_test", "passing_test"];
    for (const evType of tddEvidence) {
      if (!evidenceRegistry[evType] || evidenceRegistry[evType].length === 0) {
        missingEvidence.push(evType);
        blockers.push(`缺少 TDD 证据: ${evType}`);
      }
    }

    return {
      gate_id: "gate1",
      pass: blockers.length === 0,
      blockers,
      missing_artifacts: missingArtifacts,
      missing_evidence: missingEvidence,
      discipline_violations: disciplineViolations,
      veto_triggered: false,
      veto_reasons: [],
    };
  }

  /**
   * Gate 4 终审合规检查：工件完整性 + 证据充分性 + 一票否决
   */
  static checkGate4Final(
    artifactRegistry: Record<string, ArtifactRecord>,
    evidenceRegistry: Record<string, EvidenceRecord[]>,
    gateResults: { gate1: boolean; gate2: boolean; gate3: boolean },
    canRecoverFromBlackboard: boolean = true,
    isProductionGrade: boolean = true,
    isTokenUnderControl: boolean = true,
    noHollowLoop: boolean = true
  ): GateComplianceResult {
    const blockers: string[] = [];
    const missingArtifacts: string[] = [];
    const missingEvidence: string[] = [];
    const vetoReasons: string[] = [];

    // 1. 强制工件完整性检查
    for (const artifact of MANDATORY_ARTIFACTS_FOR_FINAL) {
      if (
        !artifactRegistry[artifact] ||
        artifactRegistry[artifact].status !== "COMPLETED"
      ) {
        missingArtifacts.push(artifact);
      }
    }
    if (missingArtifacts.length > 0) {
      blockers.push(`工件链不完整: 缺少 ${missingArtifacts.length} 个工件`);
      vetoReasons.push(VETO_ITEMS[0]);
    }

    // 2. 证据充分性检查
    for (const evidence of MANDATORY_EVIDENCE_FOR_FINAL) {
      if (!evidenceRegistry[evidence] || evidenceRegistry[evidence].length === 0) {
        missingEvidence.push(evidence);
      }
    }
    if (missingEvidence.length > 0) {
      blockers.push(`证据不充分: 缺少 ${missingEvidence.length} 类证据`);
    }

    // 3. Gate 绕过检查
    if (!gateResults.gate1 || !gateResults.gate2 || !gateResults.gate3) {
      blockers.push("存在未通过的前置 Gate");
      vetoReasons.push(VETO_ITEMS[1]);
    }

    // 4. 黑板恢复能力检查
    if (!canRecoverFromBlackboard) {
      blockers.push("无法基于黑板恢复执行");
      vetoReasons.push(VETO_ITEMS[2]);
    }

    // 5. 生产级 vs Demo 级检查
    if (!isProductionGrade) {
      blockers.push("输出仍停留在 demo 级，不满足生产级交付");
      vetoReasons.push(VETO_ITEMS[3]);
    }

    // 6. Token 控制检查
    if (!isTokenUnderControl) {
      blockers.push("Token 消耗明显失控且无法收敛");
      vetoReasons.push(VETO_ITEMS[4]);
    }

    // 7. 无人值守空转检查
    if (!noHollowLoop) {
      blockers.push("无人值守模式出现长时间空转或伪完成");
      vetoReasons.push(VETO_ITEMS[5]);
    }

    return {
      gate_id: "gate4",
      pass: blockers.length === 0 && vetoReasons.length === 0,
      blockers,
      missing_artifacts: missingArtifacts,
      missing_evidence: missingEvidence,
      discipline_violations: [],
      veto_triggered: vetoReasons.length > 0,
      veto_reasons: vetoReasons,
    };
  }

  /**
   * 计算融合验收指标
   */
  static computeMetrics(
    artifactRegistry: Record<string, ArtifactRecord>,
    evidenceRegistry: Record<string, EvidenceRecord[]>,
    totalFeatures: number = 0,
    tddCoveredFeatures: number = 0,
    totalReviewItems: number = 0,
    closedReviewItems: number = 0,
    totalTasks: number = 0,
    harnessInjectedTasks: number = 0
  ): FusionMetrics {
    const totalArtifacts = MANDATORY_ARTIFACTS_FOR_FINAL.length;
    const completedArtifacts = MANDATORY_ARTIFACTS_FOR_FINAL.filter(
      (a) => artifactRegistry[a]?.status === "COMPLETED"
    ).length;

    const totalEvidenceTypes = MANDATORY_EVIDENCE_FOR_FINAL.length;
    const coveredEvidenceTypes = MANDATORY_EVIDENCE_FOR_FINAL.filter(
      (e) => evidenceRegistry[e] && evidenceRegistry[e].length > 0
    ).length;

    return {
      artifact_completion_rate: totalArtifacts > 0 ? completedArtifacts / totalArtifacts : 0,
      evidence_coverage_rate: totalEvidenceTypes > 0 ? coveredEvidenceTypes / totalEvidenceTypes : 0,
      tdd_execution_rate: totalFeatures > 0 ? tddCoveredFeatures / totalFeatures : 0,
      review_closure_rate: totalReviewItems > 0 ? closedReviewItems / totalReviewItems : 0,
      harness_protocol_injection_rate: totalTasks > 0 ? harnessInjectedTasks / totalTasks : 0,
    };
  }
}

// =============================================================================
// 默认导出
// =============================================================================

export default OrchestratorStateMachine