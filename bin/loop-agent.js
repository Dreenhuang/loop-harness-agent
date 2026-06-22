#!/usr/bin/env node
/**
 * Loop-Harness-Agent · npm 包 CLI 入口
 * 子命令：init / loop / status / abort / version
 * 跨平台运行：node bin/loop-agent.js <subcommand>
 */

import { existsSync, mkdirSync, writeFileSync, copyFileSync, readFileSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PKG_ROOT = resolve(__dirname, "..");

const BLACKBOARD_TPL = `# 项目进度记录

> Loop Agent 黑板 · 最后更新：{{TIMESTAMP}}

---

## 【Loop 启动占位】
- 等待用户在 blackboard/input/prd.md 写入 PRD
- 启动命令：\`npx loop-agent loop\`
`;

const RULE_TPL = `# Loop-Harness-Agent · 项目级触发规则

触发关键词：\`loop-harness-agent\` / \`Loop Agent\` / \`LHA\` / 中文「循环工程」

启动 Loop：\`npx loop-agent loop\`
查询状态：\`npx loop-agent status\`
中止 Loop：\`npx loop-agent abort\`
`;

function ensureDir(p) {
  if (!existsSync(p)) mkdirSync(p, { recursive: true });
}

function writeIfMissing(path, content) {
  if (!existsSync(path)) writeFileSync(path, content, "utf-8");
}

function cmdInit(cwd) {
  const dirs = [
    "blackboard/input",
    "blackboard/tasks",
    "blackboard/templates",
    "loop-agent-engine",
    ".trae/rules",
  ];
  for (const d of dirs) ensureDir(join(cwd, d));

  writeIfMissing(
    join(cwd, "blackboard/templates/项目进度记录.md"),
    BLACKBOARD_TPL.replace("{{TIMESTAMP}}", new Date().toISOString())
  );
  writeIfMissing(join(cwd, "loop-agent-engine/orchestrator.ts"), "// 占位：从 loop-agent 包复制完整 orchestrator.ts\n");
  writeIfMissing(join(cwd, ".trae/rules/loop-agent.md"), RULE_TPL);
  writeIfMissing(join(cwd, "LOOP_AGENT_README.md"), `# Loop-Harness-Agent 已初始化\n\n时间：${new Date().toISOString()}\n\n详见 \`npx loop-agent --help\`\n`);

  console.log(`[init] 已创建 Loop-Agent 骨架于 ${cwd}`);
  console.log(`       下一步：写入 blackboard/input/prd.md，然后运行 \`npx loop-agent loop\``);
}

function cmdLoop(cwd) {
  const tsx = existsSync(join(PKG_ROOT, "node_modules/.bin/tsx"))
    ? join(PKG_ROOT, "node_modules/.bin/tsx")
    : "npx";
  const args = tsx === "npx"
    ? ["--yes", "tsx", join(PKG_ROOT, "loop-agent-engine/cli.ts")]
    : [join(PKG_ROOT, "loop-agent-engine/cli.ts")];

  const child = spawn(tsx, args, { stdio: "inherit", cwd });
  child.on("exit", (code) => process.exit(code ?? 0));
}

function cmdStatus(cwd) {
  const stateFile = join(cwd, "blackboard/state.json");
  if (!existsSync(stateFile)) {
    console.log(`[status] 未找到 ${stateFile}，请先运行 \`npx loop-agent loop\``);
    return;
  }
  const state = JSON.parse(readFileSync(stateFile, "utf-8"));
  console.log(JSON.stringify({
    loop_id: state.loopId,
    phase: state.phase,
    status: state.status,
    iteration: state.budget?.currentIteration,
    budget_used: state.budget?.currentCost,
    quality_gates: state.qualityGates,
  }, null, 2));
}

function cmdAbort(cwd) {
  const stateFile = join(cwd, "blackboard/state.json");
  if (!existsSync(stateFile)) {
    console.log(`[abort] 未找到 state.json`);
    return;
  }
  const state = JSON.parse(readFileSync(stateFile, "utf-8"));
  state.status = "aborted";
  state.phase = "DONE";
  state.abortedAt = new Date().toISOString();
  writeFileSync(stateFile, JSON.stringify(state, null, 2), "utf-8");
  console.log(`[abort] Loop 已中止（reason: manual）`);
}

function cmdVersion() {
  const pkg = JSON.parse(readFileSync(join(PKG_ROOT, "package.json"), "utf-8"));
  console.log(`loop-agent v${pkg.version}`);
  console.log(`pkgRoot: ${PKG_ROOT}`);
}

function help() {
  console.log(`Loop-Harness-Agent CLI

用法：
  loop-agent init      在当前目录初始化 Loop-Agent 骨架
  loop-agent loop      启动 10 相位流水线
  loop-agent status    查询当前 Loop 状态
  loop-agent abort     中止当前 Loop
  loop-agent version   输出版本与包根路径
  loop-agent help      显示本帮助
`);
}

const sub = process.argv[2] || "help";
const cwd = process.cwd();

switch (sub) {
  case "init":    cmdInit(cwd); break;
  case "loop":    cmdLoop(cwd); break;
  case "status":  cmdStatus(cwd); break;
  case "abort":   cmdAbort(cwd); break;
  case "version": cmdVersion(); break;
  case "help":
  case "--help":
  case "-h":
  default:
    help();
}
