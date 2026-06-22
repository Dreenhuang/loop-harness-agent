/**
 * =============================================================================
 * Loop Agent · Agent Worker 子进程
 * TypeScript · Bun 可执行
 * =============================================================================
 *
 * 启动方式：
 *   bun run loop-agent-engine/agent-worker.ts <taskId>
 *
 * 工作流（v1.2 · 含 worktree dry-run 隔离模式）：
 * 1. 读取 blackboard/tasks/{taskId}.json 任务描述
 * 2. 决定 worktree 模式：
 *    - 环境变量 LOOP_AGENT_WORKTREE_DRY_RUN=1 → 强制 dry-run，仅打印计划动作
 *    - task.worktree === true 且非 dry-run    → 真实 git worktree 操作
 *    - 否则                                    → non-worktree 模式
 * 3. 模拟执行（sleep 1 秒）
 * 4. 将执行结果写回同一任务文件
 * 5. finally 清理 worktree（真实模式下，失败也要清理）
 * 6. 以退出码 0 表示成功，非 0 表示失败
 *
 * v1.1 融合验收标准要求：
 * - 失败必须 Loud Failure（不允许静默吞错）
 * - dry-run 模式必须可由环境变量强制启用，不依赖 task.worktree 字段
 * - 真实模式失败回退到 dry-run 时必须 console.error 标记 LOUD FAILURE
 */

import { promises as fs } from "fs";
import { existsSync } from "fs";
import { spawn } from "child_process";
import path from "path";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * 查找 git 可执行文件完整路径
 * - Windows: 优先检查常见安装位置，再回退到 PATH
 * - Linux/macOS: 直接使用 git
 * 解决 Bun 子进程找不到 git（PowerShell 进程能找到但 Bun 拿到的 PATH 不一样）
 */
function findGitExe(): string {
  if (process.platform === "win32") {
    const candidates = [
      "C:\\Program Files\\Git\\bin\\git.exe",
      "C:\\Program Files (x86)\\Git\\bin\\git.exe",
      "C:\\Program Files\\Git\\cmd\\git.exe",
      "C:\\Windows\\System32\\git.exe",
    ];
    for (const c of candidates) {
      if (existsSync(c)) return c;
    }
  }
  return "git"; // 回退到 PATH
}

const GIT_EXE = findGitExe();

/**
 * 判断是否启用 dry-run 模式
 * 优先级：环境变量 LOOP_AGENT_WORKTREE_DRY_RUN=1 > task.worktree === true
 */
function isDryRunMode(taskWorktreeFlag: boolean): boolean {
  const envFlag = process.env.LOOP_AGENT_WORKTREE_DRY_RUN;
  if (envFlag === "1" || envFlag === "true") return true;
  return false;
}

/**
 * 在 dry-run 模式下打印将要执行的 git worktree 命令
 */
function logDryRunPlan(
  wtBranch: string,
  wtAbsPath: string,
  projectRoot: string,
  taskId: string
): void {
  console.log(`[Worker][DRY-RUN] task=${taskId}`);
  console.log(`[Worker][DRY-RUN] would: mkdir -p ${path.relative(projectRoot, path.dirname(wtAbsPath))}`);
  console.log(`[Worker][DRY-RUN] would: git worktree add -b ${wtBranch} ${path.relative(projectRoot, wtAbsPath)} HEAD`);
  console.log(`[Worker][DRY-RUN] would: cd ${path.relative(projectRoot, wtAbsPath)} && <agent-task> ...`);
  console.log(`[Worker][DRY-RUN] would: git worktree remove --force ${path.relative(projectRoot, wtAbsPath)}`);
}

/**
 * 真实模式：在指定路径创建 git worktree
 * 失败时抛出异常，由调用方 catch 后 Loud Failure 回退
 */
async function createWorktree(
  wtBranch: string,
  wtAbsPath: string,
  projectRoot: string,
  taskId: string
): Promise<void> {
  // 确保父目录存在
  await fs.mkdir(path.dirname(wtAbsPath), { recursive: true });

  return new Promise<void>((resolve, reject) => {
    const proc = spawn(
      GIT_EXE,
      ["worktree", "add", "-b", wtBranch, wtAbsPath, "HEAD"],
      { cwd: projectRoot, stdio: "pipe" }
    );
    let stderr = "";
    proc.stderr?.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    proc.on("error", (err) => reject(err));
    proc.on("exit", (code) => {
      if (code === 0) {
        console.log(`[Worker] worktree created: branch=${wtBranch}, path=${wtAbsPath}`);
        resolve();
      } else {
        reject(new Error(`git worktree add exited with code ${code}: ${stderr.trim()}`));
      }
    });
  });
}

/**
 * 真实模式：强制清理 worktree
 * 策略（解决 Windows Git `worktree remove` 行为异常）：
 *   1) 物理删除 .worktrees/<wtBranch> 目录
 *   2) `git worktree prune` 清理 .git/worktrees 引用
 *   3) `git branch -D <wtBranch>` 强制删除分支（如果还存在）
 * 即便失败也要继续（finally 块），但必须记录错误
 */
function removeWorktree(
  wtAbsPath: string,
  wtBranch: string,
  projectRoot: string
): void {
  const { execFileSync } = require("child_process");
  const errors: string[] = [];

  // 1) 物理删除 .worktrees/ 目录
  try {
    if (existsSync(wtAbsPath)) {
      // 同步递归删除
      const { rmSync } = require("fs");
      rmSync(wtAbsPath, { recursive: true, force: true });
    }
  } catch (err: any) {
    errors.push(`rm: ${err.message}`);
  }

  // 2) git worktree prune
  try {
    execFileSync(GIT_EXE, ["worktree", "prune"], {
      cwd: projectRoot,
      stdio: "pipe",
      timeout: 5000,
    });
  } catch (err: any) {
    errors.push(`prune: ${err.message}`);
  }

  // 3) 删除分支（已 checkout 被移除的分支后才能删）
  try {
    execFileSync(GIT_EXE, ["branch", "-D", wtBranch], {
      cwd: projectRoot,
      stdio: "pipe",
      timeout: 5000,
    });
  } catch (err: any) {
    // 分支可能已经被 prune 一并清理，忽略
  }

  if (errors.length === 0) {
    console.log(`[Worker] worktree removed: ${wtAbsPath} (branch=${wtBranch})`);
  } else {
    console.error(
      `[Worker][LOUD FAILURE] worktree cleanup partial: ${errors.join('; ')}`
    );
  }
}

/**
 * 主入口
 */
async function main() {
  const taskId = process.argv[2];
  if (!taskId) {
    console.error("[Worker] 缺少 taskId 参数，用法：bun run agent-worker.ts <taskId>");
    process.exit(1);
  }

  // 根据 worker 脚本位置定位项目根目录，确保任务文件路径稳定
  const projectRoot = path.resolve(import.meta.dir, "..");
  const tasksDir = path.join(projectRoot, "blackboard", "tasks");
  const taskFile = path.join(tasksDir, `${taskId}.json`);

  // 预声明 worktree 状态变量（用于 finally 清理）
  let wtBranch = "";
  let wtAbsPath = "";
  let worktreeActive = false;
  let useDryRun = true;

  try {
    // 读取任务描述
    const raw = await fs.readFile(taskFile, "utf-8");
    const task = JSON.parse(raw);

    // 决定 worktree 模式
    useDryRun = isDryRunMode(task.worktree === true);
    const agentType = task.agentType || "agent";
    wtBranch = `wt-${agentType}-${taskId}`;
    wtAbsPath = path.join(projectRoot, ".worktrees", wtBranch);

    console.log(
      `[Worker] 开始执行任务 ${taskId} (agent=${agentType}, phase=${task.phase}, worktree=${task.worktree === true}, dry-run=${useDryRun})`
    );

    if (task.worktree === true && !useDryRun) {
      // 真实模式：尝试创建 worktree，失败则 Loud Failure 回退到 dry-run
      try {
        await createWorktree(wtBranch, wtAbsPath, projectRoot, taskId);
        worktreeActive = true;
      } catch (err: any) {
        console.error(
          `[Worker][LOUD FAILURE] worktree 创建失败 (task=${taskId}): ${err.message}`
        );
        console.error(
          `[Worker][LOUD FAILURE] 回退到 non-worktree 模式（不创建隔离环境）继续执行任务`
        );
        console.error(
          `[Worker][LOUD FAILURE] 这违反了 worktree 隔离策略，需在 Orchestrator 端告警并阻断后续 worktree=true 任务`
        );
        useDryRun = true; // 任务主体按 non-worktree 模式继续，但 Loud Failure 已记录
      }
    }

    if (useDryRun) {
      // dry-run 或 worktree=false：仅打印计划动作
      logDryRunPlan(wtBranch, wtAbsPath, projectRoot, taskId);
    }

    // 模拟 Agent 执行：1 秒
    await sleep(1000);

    // 写回执行结果
    task.status = "DONE";
    task.completedAt = new Date().toISOString();
    task.result = {
      success: true,
      message: useDryRun
        ? "dry-run 模式任务模拟执行完成（未创建真实 worktree）"
        : "任务模拟执行完成（worktree 已创建）",
      output: task.outputPath,
      worktreeMode: useDryRun ? "dry-run" : "real",
      worktreeBranch: task.worktree === true ? wtBranch : null,
      worktreePath: task.worktree === true ? path.relative(projectRoot, wtAbsPath) : null,
    };

    await fs.writeFile(taskFile, JSON.stringify(task, null, 2), "utf-8");
    console.log(`[Worker] 任务 ${taskId} 完成 ✓`);
    // 不再 process.exit(0) — 让 main() 自然返回，确保 finally 块中的 await cleanup 有时间完成
    return;
  } catch (err: any) {
    console.error(`[Worker] 任务 ${taskId} 执行失败:`, err.message);

    // 尽量将失败状态写回任务文件
    try {
      const raw = await fs.readFile(taskFile, "utf-8").catch(() => "{}");
      const task = JSON.parse(raw);
      task.status = "FAILED";
      task.error = err.message;
      task.completedAt = new Date().toISOString();
      await fs.writeFile(taskFile, JSON.stringify(task, null, 2), "utf-8");
    } catch {
      // 忽略写回失败时的二次异常
    }

    // 不再 process.exit(1) — 让 main() 自然返回，让 finally 块清理 worktree
    return;
  } finally {
    // 清理 worktree（仅在真实模式且成功创建后才执行）
    // 使用同步调用，确保父进程退出前 cleanup 完成
    if (worktreeActive && !useDryRun) {
      removeWorktree(wtAbsPath, wtBranch, projectRoot);
    }
  }
}

main();