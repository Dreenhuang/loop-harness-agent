/**
 * Orchestrator Client - 封装对 orchestrator.ts 的调用
 * 纯 Node.js 实现，不依赖 Bun
 */
import { spawn } from "child_process";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { join, resolve } from "path";

export interface StartLoopParams {
  prd_path: string;
  time_budget_hours?: number;
  mode?: "closed" | "open" | "unattended";
  project_name?: string;
}

export interface LoopStatus {
  loop_id: string;
  current_phase: string;
  progress: number;
  budget_used_usd: number;
  budget_max_usd: number;
  active_agents: number;
  completed_tasks: number;
  failed_tasks: number;
  iterations: number;
  max_iterations: number;
  gates: {
    gate1_code_review: string;
    gate2_performance: string;
    gate3_testing: string;
    gate4_final: string;
  };
  started_at: string;
  updated_at: string;
  status: "running" | "completed" | "failed" | "aborted" | "not_started";
}

export interface AgentInfo {
  id: string;
  display_name: string;
  layer: number;
  type: string;
  bound_skills: string[];
}

export class OrchestratorClient {
  private projectRoot: string;
  private stateFile: string;
  private blackboardFile: string;
  private tasksDir: string;

  constructor(projectRoot: string) {
    this.projectRoot = resolve(projectRoot);
    this.stateFile = join(this.projectRoot, "blackboard", "state.json");
    this.blackboardFile = join(
      this.projectRoot,
      "blackboard",
      "项目进度记录.md"
    );
    this.tasksDir = join(this.projectRoot, "blackboard", "tasks");

    // 确保目录存在
    this.ensureDir(join(this.projectRoot, "blackboard"));
    this.ensureDir(this.tasksDir);

    // 初始化 state.json（如果不存在）
    if (!existsSync(this.stateFile)) {
      this.initState();
    }
  }

  private ensureDir(dir: string): void {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  }

  private initState(): void {
    const initialState = {
      loopId: null,
      phase: "INIT",
      status: "not_started",
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
      prdPath: null,
      mode: "closed",
    };
    writeFileSync(this.stateFile, JSON.stringify(initialState, null, 2), "utf-8");
  }

  private readState(): any {
    if (!existsSync(this.stateFile)) {
      this.initState();
    }
    const content = readFileSync(this.stateFile, "utf-8");
    return JSON.parse(content);
  }

  private writeState(state: any): void {
    state.updatedAt = new Date().toISOString();
    writeFileSync(this.stateFile, JSON.stringify(state, null, 2), "utf-8");
  }

  /**
   * 启动 Loop
   */
  async startLoop(params: StartLoopParams): Promise<{
    loop_id: string;
    status: string;
    started_at: string;
    mode: string;
    time_budget_hours: number;
    prd_path: string;
  }> {
    const loopId = `loop-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const timeBudget = params.time_budget_hours ?? 9;
    const mode = params.mode ?? "closed";

    // 更新 state.json
    const state = this.readState();
    state.loopId = loopId;
    state.phase = "INIT";
    state.status = "running";
    state.projectName = params.project_name ?? "auto-dev";
    state.prdPath = params.prd_path;
    state.mode = mode;
    state.timeBudgetHours = timeBudget;
    state.startedAt = new Date().toISOString();
    state.budget.currentCost = 0;
    state.budget.currentIteration = 0;
    this.writeState(state);

    // 初始化 10 相位任务
    this.initPhases(state);

    // 初始化黑板
    if (!existsSync(this.blackboardFile)) {
      this.saveBlackboard({
        phase: "Phase 0 - 初始化",
        completed_items: [
          `Loop 已启动: ${loopId}`,
          `PRD 路径: ${params.prd_path}`,
          `时间预算: ${timeBudget} 小时`,
          `模式: ${mode}`,
        ],
        uncertain_items: [],
        open_issues: [],
        next_plan: ["等待用户确认 PRD 内容", "进入 Phase 1 需求基线"],
        blackboard_updates: {
          new_nodes: ["LOOP-INIT"],
          status_changes: [`phase: INIT → running`],
          snapshot: `CP-000`,
        },
      });
    }

    return {
      loop_id: loopId,
      status: "started",
      started_at: new Date().toISOString(),
      mode,
      time_budget_hours: timeBudget,
      prd_path: params.prd_path,
    };
  }

  /**
   * 初始化 10 相位任务
   */
  private initPhases(state: any): void {
    const phases = [
      { id: "INIT", agents: ["orchestrator"] },
      { id: "REQUIREMENTS", agents: ["product_manager", "requirements"] },
      { id: "DESIGN", agents: ["ux_researcher", "ui_designer"] },
      { id: "ARCHITECTURE", agents: ["architect"] },
      { id: "DEVELOPMENT", agents: ["backend", "frontend"] },
      {
        id: "QUALITY_GATES",
        agents: ["code_reviewer", "professional_performance", "tester"],
      },
      { id: "KNOWLEDGE", agents: ["knowledge_curator"] },
      { id: "DOCUMENTATION", agents: ["documenter"] },
      { id: "FINAL_REVIEW", agents: ["final_reviewer"] },
      { id: "DEPLOY", agents: ["devops"] },
    ];

    for (let i = 0; i < phases.length; i++) {
      const phase = phases[i];
      for (const agent of phase.agents) {
        const taskId = `${phase.id.toLowerCase()}-${agent}-${i}`;
        state.tasks[taskId] = {
          id: taskId,
          phase: phase.id,
          agentType: agent,
          status: i === 0 ? "PENDING" : "PENDING", // 所有任务初始为 PENDING
          attempts: 0,
          maxAttempts: 3,
          dependencies:
            i > 0
              ? phases[i - 1].agents.map((a) => `${phases[i - 1].id.toLowerCase()}-${a}-${i - 1}`)
              : [],
        };
      }
    }

    this.writeState(state);
  }

  /**
   * 查询 Loop 状态
   */
  async getStatus(loopId?: string): Promise<LoopStatus> {
    const state = this.readState();

    const tasks = Object.values(state.tasks || {}) as any[];
    const completed = tasks.filter((t) => t.status === "DONE").length;
    const failed = tasks.filter((t) => t.status === "FAILED").length;
    const active = tasks.filter((t) => t.status === "RUNNING").length;
    const total = tasks.length;
    const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

    return {
      loop_id: state.loopId ?? loopId ?? "unknown",
      current_phase: state.phase ?? "INIT",
      progress,
      budget_used_usd: state.budget?.currentCost ?? 0,
      budget_max_usd: state.budget?.maxCost ?? 100,
      active_agents: active,
      completed_tasks: completed,
      failed_tasks: failed,
      iterations: state.budget?.currentIteration ?? 0,
      max_iterations: state.budget?.maxIterations ?? 200,
      gates: {
        gate1_code_review: state.qualityGates?.codeReview ?? "NOT_STARTED",
        gate2_performance: state.qualityGates?.performance ?? "NOT_STARTED",
        gate3_testing: state.qualityGates?.testing ?? "NOT_STARTED",
        gate4_final: state.qualityGates?.final ?? "NOT_STARTED",
      },
      started_at: state.startedAt ?? new Date().toISOString(),
      updated_at: state.updatedAt ?? new Date().toISOString(),
      status: state.status ?? "not_started",
    };
  }

  /**
   * 中止 Loop
   */
  async abortLoop(
    loopId: string,
    reason: string
  ): Promise<{
    aborted: boolean;
    reason: string;
    final_state: LoopStatus;
  }> {
    const state = this.readState();
    state.status = "aborted";
    state.abortReason = reason;
    state.abortedAt = new Date().toISOString();
    state.phase = "DONE";
    this.writeState(state);

    // 更新黑板
    this.saveBlackboard({
      phase: "ABORTED",
      completed_items: [],
      uncertain_items: [],
      open_issues: [`Loop 已中止: ${reason}`],
      next_plan: [],
      blackboard_updates: {
        abort_reason: reason,
        abort_time: new Date().toISOString(),
      },
    });

    return {
      aborted: true,
      reason,
      final_state: await this.getStatus(loopId),
    };
  }

  /**
   * 派发 Agent 任务
   */
  async spawnAgent(
    agentType: string,
    taskInput: Record<string, any>
  ): Promise<{
    task_id: string;
    agent_type: string;
    status: string;
    phase: string;
    started_at: string;
    task_file: string;
  }> {
    const state = this.readState();
    const currentPhase = state.phase;

    // 查找当前 Phase 的对应任务
    const phaseTask = Object.values(state.tasks || {}).find(
      (t: any) => t.phase === currentPhase && t.agentType === agentType
    ) as any;

    const taskId = phaseTask
      ? phaseTask.id
      : `task-${agentType}-${Date.now()}-${Math.random()
          .toString(36)
          .slice(2, 6)}`;

    // 更新任务状态
    if (phaseTask) {
      phaseTask.status = "RUNNING";
      phaseTask.startedAt = new Date().toISOString();
      phaseTask.input = taskInput;
    } else {
      // 创建临时任务
      state.tasks[taskId] = {
        id: taskId,
        phase: currentPhase,
        agentType,
        status: "RUNNING",
        attempts: 0,
        maxAttempts: 3,
        dependencies: [],
        input: taskInput,
        startedAt: new Date().toISOString(),
      };
    }

    state.budget.currentIteration++;
    this.writeState(state);

    // 写入任务文件
    const taskFile = join(this.tasksDir, `${taskId}.json`);
    writeFileSync(
      taskFile,
      JSON.stringify(
        {
          task_id: taskId,
          agent_type: agentType,
          phase: currentPhase,
          status: "RUNNING",
          input: taskInput,
          created_at: new Date().toISOString(),
        },
        null,
        2
      ),
      "utf-8"
    );

    return {
      task_id: taskId,
      agent_type: agentType,
      status: "RUNNING",
      phase: currentPhase,
      started_at: new Date().toISOString(),
      task_file: taskFile,
    };
  }

  /**
   * 列出 16 角色
   */
  async listAgents(): Promise<AgentInfo[]> {
    return [
      { id: "orchestrator", display_name: "@Orchestrator", layer: 1, type: "supervisor", bound_skills: ["budget-track", "progress-detect", "state-snapshot", "orchestrate-map-reduce"] },
      { id: "product_manager", display_name: "@Product-Manager", layer: 2, type: "decision_maker", bound_skills: ["knowledge-extract"] },
      { id: "requirements", display_name: "@Requirements", layer: 2, type: "specialist", bound_skills: ["bug-triaging"] },
      { id: "ux_researcher", display_name: "@UX-Researcher", layer: 2, type: "specialist", bound_skills: [] },
      { id: "ui_designer", display_name: "@UI-Designer", layer: 2, type: "specialist", bound_skills: [] },
      { id: "architect", display_name: "@Architect", layer: 3, type: "decision_maker", bound_skills: ["orchestrate-map-reduce"] },
      { id: "backend", display_name: "@Backend", layer: 4, type: "specialist", bound_skills: ["gate1-code-review", "progress-detect"] },
      { id: "frontend", display_name: "@Fullstack-Coder", layer: 4, type: "specialist", bound_skills: ["gate1-code-review"] },
      { id: "bug_defect_repairer", display_name: "@Bug-Defect-Repairer", layer: 4, type: "specialist", bound_skills: ["bug-triaging", "gate1-code-review"] },
      { id: "code_reviewer", display_name: "@Code-Reviewer", layer: 5, type: "gate_keeper", bound_skills: ["gate1-code-review"] },
      { id: "professional_performance", display_name: "@Professional-Performance", layer: 5, type: "gate_keeper", bound_skills: ["gate2-performance"] },
      { id: "tester", display_name: "@全栈测试员", layer: 5, type: "gate_keeper", bound_skills: ["gate3-testing", "bug-triaging"] },
      { id: "knowledge_curator", display_name: "@Knowledge-Curator", layer: 6, type: "specialist", bound_skills: ["knowledge-extract"] },
      { id: "documenter", display_name: "@Documenter", layer: 7, type: "specialist", bound_skills: [] },
      { id: "final_reviewer", display_name: "@Final-Reviewer", layer: 7, type: "gate_keeper", bound_skills: ["gate4-final"] },
      { id: "devops", display_name: "@DevOps", layer: 7, type: "specialist", bound_skills: ["progress-detect"] },
    ];
  }

  /**
   * 保存黑板
   */
  async saveBlackboard(data: {
    phase: string;
    completed_items: string[];
    uncertain_items: string[];
    open_issues: string[];
    next_plan: string[];
    blackboard_updates: Record<string, any>;
  }): Promise<{
    saved: boolean;
    file_path: string;
    timestamp: string;
  }> {
    const timestamp = new Date().toISOString();
    const dateStr = timestamp.split("T")[0];

    let content = "";
    if (existsSync(this.blackboardFile)) {
      content = readFileSync(this.blackboardFile, "utf-8");
    } else {
      content = `# 项目进度记录

> Loop Agent 黑板 · 最后更新：${timestamp}

---

`;
    }

    // 追加新记录
    const newSection = `
## 【${dateStr}｜Loop Agent｜${data.phase}】${timestamp}

### 1. ✅ 本轮已完成
${data.completed_items.length > 0 ? data.completed_items.map((item) => `- ${item}`).join("\n") : "- （无）"}

### 2. ⚠️ 本轮不确定项
${data.uncertain_items.length > 0 ? data.uncertain_items.map((item) => `- ${item}`).join("\n") : "- （无）"}

### 3. ❌ 遗留待解决问题
${data.open_issues.length > 0 ? data.open_issues.map((item) => `- ${item}`).join("\n") : "- （无）"}

### 4. 📋 下一轮工作计划
${data.next_plan.length > 0 ? data.next_plan.map((item) => `- ${item}`).join("\n") : "- （无）"}

### 5. 🔄 黑板更新记录
${Object.entries(data.blackboard_updates)
  .map(([key, value]) => `- **${key}**: ${JSON.stringify(value)}`)
  .join("\n")}

---
`;

    content = content + newSection;
    writeFileSync(this.blackboardFile, content, "utf-8");

    return {
      saved: true,
      file_path: this.blackboardFile,
      timestamp,
    };
  }
}
