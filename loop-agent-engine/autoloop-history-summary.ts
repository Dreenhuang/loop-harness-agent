/**
 * 输出 history.json 摘要
 * bun run loop-agent-engine/autoloop-history-summary.ts
 */
import { loadHistory, DEFAULT_HISTORY_PATH } from "./autoloop";

async function main() {
  const history = await loadHistory(DEFAULT_HISTORY_PATH);
  console.log("=== Autoloop History 摘要 ===");
  console.log(`路径: ${DEFAULT_HISTORY_PATH}`);
  console.log(`总条目: ${history.length}`);
  console.log("");
  console.log("| # | run.id | seed | mutation | delta | status |");
  console.log("|---|--------|------|----------|-------|--------|");
  history.forEach((e, i) => {
    const seed = e.stage3_variant.seed;
    const mr = (e.stage3_variant.mutationRate * 100).toFixed(2) + "%";
    const delta = (e.stage4_comparison.delta >= 0 ? "+" : "") + e.stage4_comparison.delta.toFixed(2);
    console.log(`| ${i} | ${e.id} | ${seed} | ${mr} | ${delta} | ${e.status} |`);
  });
}

main().catch(console.error);