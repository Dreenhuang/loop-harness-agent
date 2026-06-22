import { describe, it, expect } from 'vitest';
import {
  GateComplianceChecker,
  type ArtifactRecord,
  type EvidenceRecord,
} from '../orchestrator.ts';

function createArtifact(name: string): ArtifactRecord {
  return {
    artifact_name: name,
    artifact_path: `./${name}`,
    owner_role: 'test',
    phase: 'DEVELOPMENT',
    status: 'COMPLETED',
    version: '1.0.0',
    updated_at: new Date().toISOString(),
  };
}

function createEvidence(type: string): EvidenceRecord {
  return {
    evidence_type: type,
    source_role: 'test',
    task_id: 'task-1',
    command: 'test',
    result_summary: 'ok',
    attachments: [],
    timestamp: new Date().toISOString(),
  };
}

const MANDATORY_ARTIFACTS = [
  'Product-Spec.md',
  'Design-Brief.md',
  'UI-Design.md',
  'Component-Library.md',
  'Architecture.md',
  'API-Spec.md',
  'DEV-PLAN.md',
  'Quality-Check-Report.md',
  'Test-Report.md',
  'Code-Review-Report.md',
  'UX-Review-Report.md',
  'Release-Notes.md',
];

const MANDATORY_EVIDENCE = [
  'failing_test',
  'passing_test',
  'verification_commands',
  'review_feedback',
  'deploy_smoke_test',
];

describe('GateComplianceChecker', () => {
  describe('checkGate1', () => {
    it('DEV-PLAN 与 TDD 证据齐全时应通过', () => {
      const artifacts = { 'DEV-PLAN.md': createArtifact('DEV-PLAN.md') };
      const evidence = {
        failing_test: [createEvidence('failing_test')],
        passing_test: [createEvidence('passing_test')],
      };
      const result = GateComplianceChecker.checkGate1(artifacts, evidence);
      expect(result.pass).toBe(true);
      expect(result.blockers).toEqual([]);
      expect(result.gate_id).toBe('gate1');
      expect(result.veto_triggered).toBe(false);
    });

    it('缺少 DEV-PLAN 与 TDD 证据时应失败并列出缺失项', () => {
      const result = GateComplianceChecker.checkGate1({}, {});
      expect(result.pass).toBe(false);
      expect(result.missing_artifacts).toContain('DEV-PLAN.md');
      expect(result.missing_evidence).toContain('failing_test');
      expect(result.missing_evidence).toContain('passing_test');
      expect(result.blockers.length).toBeGreaterThan(0);
    });
  });

  describe('checkGate4Final', () => {
    it('全部工件、证据与 Gate 通过时应通过', () => {
      const artifacts = Object.fromEntries(
        MANDATORY_ARTIFACTS.map((name) => [name, createArtifact(name)])
      );
      const evidence = Object.fromEntries(
        MANDATORY_EVIDENCE.map((type) => [type, [createEvidence(type)]])
      );
      const result = GateComplianceChecker.checkGate4Final(artifacts, evidence, {
        gate1: true,
        gate2: true,
        gate3: true,
      });
      expect(result.pass).toBe(true);
      expect(result.veto_triggered).toBe(false);
      expect(result.gate_id).toBe('gate4');
    });

    it('缺少强制工件与证据时应失败并触发一票否决', () => {
      const result = GateComplianceChecker.checkGate4Final(
        {},
        {},
        { gate1: true, gate2: true, gate3: true }
      );
      expect(result.pass).toBe(false);
      expect(result.missing_artifacts.length).toBe(MANDATORY_ARTIFACTS.length);
      expect(result.missing_evidence.length).toBe(MANDATORY_EVIDENCE.length);
      expect(result.veto_triggered).toBe(true);
      expect(result.veto_reasons).toContain('工件链不完整');
    });

    it('前置 Gate 未通过时应触发一票否决', () => {
      const artifacts = Object.fromEntries(
        MANDATORY_ARTIFACTS.map((name) => [name, createArtifact(name)])
      );
      const evidence = Object.fromEntries(
        MANDATORY_EVIDENCE.map((type) => [type, [createEvidence(type)]])
      );
      const result = GateComplianceChecker.checkGate4Final(artifacts, evidence, {
        gate1: false,
        gate2: true,
        gate3: true,
      });
      expect(result.pass).toBe(false);
      expect(result.blockers).toContain('存在未通过的前置 Gate');
      expect(result.veto_triggered).toBe(true);
      expect(result.veto_reasons).toContain('Gate 可被绕过');
    });

    it('生产级未达标时应触发一票否决', () => {
      const artifacts = Object.fromEntries(
        MANDATORY_ARTIFACTS.map((name) => [name, createArtifact(name)])
      );
      const evidence = Object.fromEntries(
        MANDATORY_EVIDENCE.map((type) => [type, [createEvidence(type)]])
      );
      const result = GateComplianceChecker.checkGate4Final(
        artifacts,
        evidence,
        { gate1: true, gate2: true, gate3: true },
        true,
        false
      );
      expect(result.pass).toBe(false);
      expect(result.veto_triggered).toBe(true);
      expect(result.veto_reasons).toContain('demo 级结果伪装生产级');
    });

    it('无法基于黑板恢复时应触发一票否决', () => {
      const artifacts = Object.fromEntries(
        MANDATORY_ARTIFACTS.map((name) => [name, createArtifact(name)])
      );
      const evidence = Object.fromEntries(
        MANDATORY_EVIDENCE.map((type) => [type, [createEvidence(type)]])
      );
      const result = GateComplianceChecker.checkGate4Final(
        artifacts,
        evidence,
        { gate1: true, gate2: true, gate3: true },
        false
      );
      expect(result.pass).toBe(false);
      expect(result.veto_triggered).toBe(true);
      expect(result.veto_reasons).toContain('无法基于黑板恢复');
    });
  });

  describe('computeMetrics', () => {
    it('应正确计算工件完成率与证据覆盖率', () => {
      const artifacts = Object.fromEntries(
        MANDATORY_ARTIFACTS.slice(0, 6).map((name) => [name, createArtifact(name)])
      );
      const evidence = {
        failing_test: [createEvidence('failing_test')],
        passing_test: [createEvidence('passing_test')],
      };
      const metrics = GateComplianceChecker.computeMetrics(artifacts, evidence);
      expect(metrics.artifact_completion_rate).toBeCloseTo(6 / 12);
      expect(metrics.evidence_coverage_rate).toBeCloseTo(2 / 5);
      expect(metrics.tdd_execution_rate).toBe(0);
      expect(metrics.review_closure_rate).toBe(0);
      expect(metrics.harness_protocol_injection_rate).toBe(0);
    });

    it('应正确计算 TDD 执行率与审查闭环率', () => {
      const metrics = GateComplianceChecker.computeMetrics(
        {},
        {},
        10,
        7,
        20,
        15,
        8,
        6
      );
      expect(metrics.tdd_execution_rate).toBe(0.7);
      expect(metrics.review_closure_rate).toBe(0.75);
      expect(metrics.harness_protocol_injection_rate).toBe(0.75);
    });
  });
});
