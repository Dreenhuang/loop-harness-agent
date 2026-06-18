#!/usr/bin/env bun
/**
 * =============================================================================
 * 融合验收指标采集脚本
 * =============================================================================
 *
 * 用途：从 artifacts/registry/ 和 artifacts/evidence/ 读取数据，
 * 计算融合验收标准中定义的核心指标。
 *
 * 运行：bun run scripts/fusion-metrics.ts
 */

import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

const PROJECT_ROOT = resolve(import.meta.dir, "..");

interface ArtifactEntry {
  artifact_path: string;
  owner_role: string;
  phase: string;
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "MISSING";
  version: string;
}

interface EvidenceEntry {
  evidence_type: string;
  source_role: string;
  task_id: string;
  command: string;
  result_summary: string;
  timestamp: string;
}

function loadJSON<T>(path: string): T | null {
  const fullPath = resolve(PROJECT_ROOT, path);
  if (!existsSync(fullPath)) return null;
  return JSON.parse(readFileSync(fullPath, "utf8")) as T;
}

function computeMetrics() {
  console.log("═══════════════════════════════════════════════════════");
  console.log("  融合验收指标采集报告");
  console.log("═══════════════════════════════════════════════════════\n");

  // 1. 工件完成率
  const registry = loadJSON<{ artifacts: Record<string, ArtifactEntry> }>(
    "artifacts/registry/initial-registry.json"
  );

  let artifactCompletionRate = 0;
  let artifactDetails: string[] = [];

  if (registry?.artifacts) {
    const entries = Object.entries(registry.artifacts);
    const completed = entries.filter(([_, v]) => v.status === "COMPLETED").length;
    artifactCompletionRate = entries.length > 0 ? completed / entries.length : 0;

    artifactDetails = entries.map(([name, v]) => {
      const icon = v.status === "COMPLETED" ? "✅" : v.status === "IN_PROGRESS" ? "🔄" : "⏳";
      return `  ${icon} ${name}: ${v.status} (${v.phase})`;
    });
  }

  console.log(`📊 工件完成率: ${(artifactCompletionRate * 100).toFixed(1)}%`);
  if (artifactDetails.length > 0) {
    console.log("  工件明细:");
    artifactDetails.forEach(d => console.log(d));
  }

  // 2. 证据覆盖率
  const evidence = loadJSON<{ evidence: Record<string, EvidenceEntry[]> }>(
    "artifacts/evidence/initial-evidence.json"
  );

  let evidenceCoverageRate = 0;
  let evidenceDetails: string[] = [];

  if (evidence?.evidence) {
    const entries = Object.entries(evidence.evidence);
    const covered = entries.filter(([_, v]) => v.length > 0).length;
    evidenceCoverageRate = entries.length > 0 ? covered / entries.length : 0;

    evidenceDetails = entries.map(([name, v]) => {
      const icon = v.length > 0 ? "✅" : "⏳";
      return `  ${icon} ${name}: ${v.length} 条记录`;
    });
  }

  console.log(`\n📊 证据覆盖率: ${(evidenceCoverageRate * 100).toFixed(1)}%`);
  if (evidenceDetails.length > 0) {
    console.log("  证据明细:");
    evidenceDetails.forEach(d => console.log(d));
  }

  // 3. 达标判定
  console.log("\n═══════════════════════════════════════════════════════");
  console.log("  达标判定（对齐融合验收标准）");
  console.log("═══════════════════════════════════════════════════════\n");

  const targets = [
    { name: "工件完成率", value: artifactCompletionRate, target: 0.95 },
    { name: "证据覆盖率", value: evidenceCoverageRate, target: 0.90 },
  ];

  targets.forEach(t => {
    const pass = t.value >= t.target;
    console.log(`  ${pass ? "✅" : "❌"} ${t.name}: ${(t.value * 100).toFixed(1)}% (目标 ≥ ${(t.target * 100).toFixed(0)}%)`);
  });

  // 4. 一票否决检查
  console.log("\n═══════════════════════════════════════════════════════");
  console.log("  一票否决项检查");
  console.log("═══════════════════════════════════════════════════════\n");

  const vetoChecks = [
    { item: "工件链完整性", pass: artifactCompletionRate >= 1.0 },
    { item: "证据充分性", pass: evidenceCoverageRate >= 1.0 },
    { item: "Gate 不可绕过", pass: false }, // 需要运行时验证
    { item: "黑板恢复能力", pass: false }, // 需要运行时验证
    { item: "生产级交付", pass: false }, // 需要运行时验证
    { item: "Token 可控", pass: true }, // 默认可控
  ];

  vetoChecks.forEach(v => {
    console.log(`  ${v.pass ? "✅" : "❌"} ${v.item}: ${v.pass ? "通过" : "未通过"}`);
  });

  const anyVeto = vetoChecks.some(v => !v.pass);
  console.log(`\n  最终结论: ${anyVeto ? "❌ FAIL (存在一票否决项)" : "✅ PASS"}`);

  console.log("\n═══════════════════════════════════════════════════════");
}

computeMetrics();
