/**
 * =============================================================================
 * Loop Agent · Orchestrator CLI 入口
 * 独立运行入口：`bun run loop-agent-engine/cli.ts`
 * =============================================================================
 */

import { OrchestratorStateMachine, type PipelineState, type TaskState } from "./orchestrator";

/**
 * 演示：初始化一个完整的 10 相位流水线
 */
async function demo() {
  console.log("═══════════════════════════════════════════════════════");
  console.log("  Loop Agent · Orchestrator 状态机 · 演示");
  console.log("  Trae Solo 工程实现 v1.0 对齐版");
  console.log("═══════════════════════════════════════════════════════\n");

  // 1. 初始化 PipelineState
  const state: PipelineState = {
    projectName: "demo-project",
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
    prdPath: "./blackboard/input/prd.md",
  };

  // 2. 加载示例任务（演示 10 相位）
  const phases = [
    "INIT", "REQUIREMENTS", "DESIGN", "ARCHITECTURE", "DEVELOPMENT",
    "QUALITY_GATES", "KNOWLEDGE", "DOCUMENTATION", "FINAL_REVIEW", "DEPLOY"
  ];

  const agentMap: Record<string, string> = {
    "INIT": "orchestrator",
    "REQUIREMENTS": "product_manager,requirements",
    "DESIGN": "ux_researcher,ui_designer",
    "ARCHITECTURE": "architect",
    "DEVELOPMENT": "backend,frontend",
    "QUALITY_GATES": "code_reviewer,professional_performance,tester",
    "KNOWLEDGE": "knowledge_curator",
    "DOCUMENTATION": "documenter",
    "FINAL_REVIEW": "final_reviewer",
    "DEPLOY": "devops",
  };

  for (let i = 0; i < phases.length; i++) {
    const phase = phases[i];
    const agents = agentMap[phase].split(",");
    for (const agent of agents) {
      const taskId = `${phase.toLowerCase()}-${agent}-${i}`;
      const task: TaskState = {
        id: taskId,
        phase: phase as any,
        agentType: agent.trim(),
        status: "PENDING",
        inputPaths: [`./blackboard/${phase.toLowerCase()}/input/`],
        outputPath: `./blackboard/${phase.toLowerCase()}/output/${taskId}.json`,
        acceptanceCriteria: { phase_complete: true },
        attempts: 0,
        maxAttempts: 3,
        dependencies: i > 0 ? [phases[i - 1].toLowerCase()] : [],
        worktree: ["backend", "frontend", "bug_defect_repairer"].includes(agent.trim()),
      };
      state.tasks[taskId] = task;
    }
  }

  console.log(`[Init] 已加载 ${Object.keys(state.tasks).length} 个任务，覆盖 ${phases.length} 个相位\n`);

  // 3. 创建状态机
  const sm = new OrchestratorStateMachine(state);

  // 4. 演示 5 轮 tick
  for (let i = 0; i < 5; i++) {
    await sm.tick();
  }

  // 5. 演示任务完成回调
  console.log("\n[Demo] 模拟完成第 1 个任务：");
  const firstTaskId = Object.keys(state.tasks)[0];
  await sm.onTaskComplete(firstTaskId, true);

  console.log("\n[Demo] 模拟失败第 2 个任务（重试 1 次）：");
  const secondTaskId = Object.keys(state.tasks)[1];
  await sm.onTaskComplete(secondTaskId, false, "Mock error: file not found");

  console.log("\n═══════════════════════════════════════════════════════");
  console.log("  演示完成");
  console.log("  当前状态：");
  console.log(`    Phase: ${state.phase}`);
  console.log(`    Iteration: ${state.budget.currentIteration}`);
  console.log(`    任务总数: ${Object.keys(state.tasks).length}`);
  console.log(`    已完成: ${Object.values(state.tasks).filter(t => t.status === "DONE").length}`);
  console.log(`    进行中: ${Object.values(state.tasks).filter(t => t.status === "RUNNING").length}`);
  console.log(`    待执行: ${Object.values(state.tasks).filter(t => t.status === "PENDING").length}`);
  console.log(`    失败: ${Object.values(state.tasks).filter(t => t.status === "FAILED").length}`);
  console.log("═══════════════════════════════════════════════════════");
}

// CLI 入口
if (import.meta.main) {
  demo().catch(console.error);
}
