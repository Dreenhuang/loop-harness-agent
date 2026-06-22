import { describe, it, expect } from 'vitest';
import {
  HarnessPolicyEngine,
  type ArtifactRecord,
  type EvidenceRecord,
} from '../orchestrator.ts';

const PHASES = [
  'INIT',
  'REQUIREMENTS',
  'DESIGN',
  'ARCHITECTURE',
  'DEVELOPMENT',
  'QUALITY_GATES',
  'KNOWLEDGE',
  'DOCUMENTATION',
  'FINAL_REVIEW',
  'DEPLOY',
  'DONE',
] as const;

function createArtifact(
  name: string,
  status: ArtifactRecord['status']
): ArtifactRecord {
  return {
    artifact_name: name,
    artifact_path: `./${name}`,
    owner_role: 'test',
    phase: 'DEVELOPMENT',
    status,
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

describe('HarnessPolicyEngine', () => {
  describe('generateProtocol', () => {
    it('应为每个 Phase 生成正确的 required_artifacts 与 evidence_requirements', () => {
      const expectations: Record<
        string,
        { artifacts: string[]; evidence: string[] }
      > = {
        INIT: { artifacts: [], evidence: [] },
        REQUIREMENTS: {
          artifacts: ['Product-Spec.md'],
          evidence: ['requirement_clarification_record'],
        },
        DESIGN: {
          artifacts: ['Design-Brief.md', 'UI-Design.md', 'Component-Library.md'],
          evidence: ['design_review_record'],
        },
        ARCHITECTURE: {
          artifacts: ['Architecture.md', 'API-Spec.md'],
          evidence: ['tech_stack_comparison', 'risk_assessment_record'],
        },
        DEVELOPMENT: {
          artifacts: ['DEV-PLAN.md'],
          evidence: ['failing_test', 'passing_test', 'refactor_evidence'],
        },
        QUALITY_GATES: {
          artifacts: [
            'Quality-Check-Report.md',
            'Test-Report.md',
            'Code-Review-Report.md',
          ],
          evidence: ['verification_commands', 'review_feedback'],
        },
        KNOWLEDGE: { artifacts: [], evidence: [] },
        DOCUMENTATION: { artifacts: [], evidence: [] },
        FINAL_REVIEW: {
          artifacts: ['UX-Review-Report.md', 'Release-Notes.md'],
          evidence: ['deploy_smoke_test'],
        },
        DEPLOY: {
          artifacts: [],
          evidence: ['deploy_smoke_test', 'build_verification'],
        },
        DONE: { artifacts: [], evidence: [] },
      };

      for (const phase of PHASES) {
        const protocol = HarnessPolicyEngine.generateProtocol(phase);
        expect(protocol.phase).toBe(phase);
        expect(protocol.required_artifacts).toEqual(
          expectations[phase].artifacts
        );
        expect(protocol.evidence_requirements).toEqual(
          expectations[phase].evidence
        );
      }
    });

    it('应使用默认项目类型与任务类型', () => {
      const protocol = HarnessPolicyEngine.generateProtocol('REQUIREMENTS');
      expect(protocol.project_type).toBe('web-fullstack');
      expect(protocol.task_type).toBe('feature-development');
      expect(protocol.role).toBe('');
    });

    it('应接受自定义项目类型、任务类型与角色', () => {
      const protocol = HarnessPolicyEngine.generateProtocol(
        'DEVELOPMENT',
        'mobile-app',
        'bugfix',
        'backend'
      );
      expect(protocol.project_type).toBe('mobile-app');
      expect(protocol.task_type).toBe('bugfix');
      expect(protocol.role).toBe('backend');
    });
  });

  describe('checkArtifactCompleteness', () => {
    it('应检测缺失的工件', () => {
      const registry: Record<string, ArtifactRecord> = {};
      const result = HarnessPolicyEngine.checkArtifactCompleteness(
        'DEVELOPMENT',
        registry
      );
      expect(result.complete).toBe(false);
      expect(result.missing).toEqual(['DEV-PLAN.md']);
    });

    it('应检测状态非 COMPLETED 的工件', () => {
      const registry = {
        'DEV-PLAN.md': createArtifact('DEV-PLAN.md', 'IN_PROGRESS'),
      };
      const result = HarnessPolicyEngine.checkArtifactCompleteness(
        'DEVELOPMENT',
        registry
      );
      expect(result.complete).toBe(false);
      expect(result.missing).toEqual(['DEV-PLAN.md']);
    });

    it('工件齐全时应返回 complete', () => {
      const registry = {
        'DEV-PLAN.md': createArtifact('DEV-PLAN.md', 'COMPLETED'),
      };
      const result = HarnessPolicyEngine.checkArtifactCompleteness(
        'DEVELOPMENT',
        registry
      );
      expect(result.complete).toBe(true);
      expect(result.missing).toEqual([]);
    });

    it('无强制工件的 Phase 应视为 complete', () => {
      const result = HarnessPolicyEngine.checkArtifactCompleteness('INIT', {});
      expect(result.complete).toBe(true);
      expect(result.missing).toEqual([]);
    });
  });

  describe('checkEvidenceSufficiency', () => {
    it('应检测缺失的证据类型', () => {
      const registry: Record<string, EvidenceRecord[]> = {};
      const result = HarnessPolicyEngine.checkEvidenceSufficiency(
        'DEVELOPMENT',
        registry
      );
      expect(result.sufficient).toBe(false);
      expect(result.missing).toEqual([
        'failing_test',
        'passing_test',
        'refactor_evidence',
      ]);
    });

    it('应检测证据数组为空的情况', () => {
      const registry = { failing_test: [] as EvidenceRecord[] };
      const result = HarnessPolicyEngine.checkEvidenceSufficiency(
        'DEVELOPMENT',
        registry
      );
      expect(result.sufficient).toBe(false);
      expect(result.missing).toContain('failing_test');
    });

    it('证据充分时应返回 sufficient', () => {
      const registry = {
        failing_test: [createEvidence('failing_test')],
        passing_test: [createEvidence('passing_test')],
        refactor_evidence: [createEvidence('refactor_evidence')],
      };
      const result = HarnessPolicyEngine.checkEvidenceSufficiency(
        'DEVELOPMENT',
        registry
      );
      expect(result.sufficient).toBe(true);
      expect(result.missing).toEqual([]);
    });

    it('无强制证据的 Phase 应视为 sufficient', () => {
      const result = HarnessPolicyEngine.checkEvidenceSufficiency(
        'DOCUMENTATION',
        {}
      );
      expect(result.sufficient).toBe(true);
      expect(result.missing).toEqual([]);
    });
  });
});
