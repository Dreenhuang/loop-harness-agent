/**
 * Loop Agent Orchestrator CLI 入口
 * bun run loop-agent-engine/cli.ts
 */

import { OrchestratorStateMachine, type PipelineState, type TaskState } from "./orchestrator";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function initDemoTasks(state: PipelineState) {
  const phases = [
    "INIT", "REQUIREMENTS", "DESIGN", "ARCHITECTURE", "DEVELOPMENT",
    "QUALITY_GATES", "KNOWLEDGE", "DOCUMENTATION", "FINAL_REVIEW", "DEPLOY"
  ];
  const agentMap: Record<string, string> = {
    INIT: "orchestrator",
    REQUIREMENTS: "product_manager,requirements",
    DESIGN: "ux_researcher,ui_designer",
    ARCHITECTURE: "architect",
    DEVELOPMENT: "backend,frontend",
    QUALITY_GATES: "code_reviewer,professional_performance,tester",
    KNOWLEDGE: "knowledge_curator",
    DOCUMENTATION: "documenter",
    FINAL_REVIEW: "final_reviewer",
    DEPLOY: "devops",
  };
  for (let i = 0; i < phases.length; i++) {
    const phase = phases[i];
    for (const agent of agentMap[phase].split(",")) {
      const taskId = `${phase.toLowerCase()}-${agent}-${i}`;
      const prevFirstAgent = i > 0 ? agentMap[phases[i - 1]].split(",")[0].trim() : "";
      state.tasks[taskId] = {
        id: taskId,
        phase: phase as any,
        agentType: agent.trim(),
        status: "PENDING",
        inputPaths: [`./blackboard/${phase.toLowerCase()}/input/`],
        outputPath: `./blackboard/${phase.toLowerCase()}/output/${taskId}.json`,
        acceptanceCriteria: { phase_complete: true },
        attempts: 0,
        maxAttempts: 3,
        dependencies: i > 0 ? [`${phases[i - 1].toLowerCase()}-${prevFirstAgent}-${i - 1}`] : [],
        worktree: ["backend", "frontend", "bug_defect_repairer"].includes(agent.trim()),
      };
    }
  }
}

function printSummary(state: PipelineState) {
  const tasks = Object.values(state.tasks);
  console.log("\n=== 演示完成 ===");
  console.log(`Phase: ${state.phase} | Iteration: ${state.budget.currentIteration}`);
  console.log(`总任务: ${tasks.length} | 完成: ${tasks.filter(t => t.status === "DONE").length} | 运行中: ${tasks.filter(t => t.status === "RUNNING").length} | 待执行: ${tasks.filter(t => t.status === "PENDING").length} | 失败: ${tasks.filter(t => t.status === "FAILED").length}`);
  console.log("检查 blackboard/state.json 与 blackboard/tasks/*.json");
}

async function demo() {
  console.log("=== Loop Agent Orchestrator 真实持久化演示 ===\n");

  let state = await OrchestratorStateMachine.loadState();
  if (Object.keys(state.tasks).length === 0) {
    state.projectName = "demo-project";
    state.prdPath = "./blackboard/input/prd.md";
    initDemoTasks(state);
    console.log(`[Init] 已加载 ${Object.keys(state.tasks).length} 个任务`);
  } else {
    console.log(`[Resume] 从已有状态继续，${Object.keys(state.tasks).length} 个任务`);
  }

  let sm = new OrchestratorStateMachine(state);

  console.log("\n[阶段一] 运行 3 轮 tick...");
  for (let i = 0; i < 3; i++) {
    await sm.tick();
    await sleep(1500);
  }

  console.log("\n[阶段二] 模拟重启，从 state.json 恢复...");
  state = await OrchestratorStateMachine.loadState();
  sm = new OrchestratorStateMachine(state);

  console.log("\n[阶段三] 恢复后继续运行 2 轮 tick...");
  for (let i = 0; i < 2; i++) {
    await sm.tick();
    await sleep(1500);
  }

  printSummary(state);
}

demo().catch(console.error); // write-truncation-padding-