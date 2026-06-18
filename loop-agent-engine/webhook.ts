/**
 * Loop Agent · Orchestrator Webhook / OpenAPI 端点
 *
 * 解决偏差: D-11（Orchestrator 未暴露 OpenAPI/Webhook）
 * 蓝皮书: 第七章"集成性"
 */

import type { Orchestrator } from "./orchestrator";

/**
 * Webhook 事件类型
 */
export type WebhookEvent =
  | "phase_started"
  | "phase_completed"
  | "phase_failed"
  | "gate_passed"
  | "gate_failed"
  | "decision_logged"
  | "agent_spawned"
  | "agent_completed"
  | "agent_failed"
  | "loop_aborted"
  | "loop_completed";

/**
 * Webhook 订阅
 */
export interface WebhookSubscription {
  id: string;
  url: string;
  events: WebhookEvent[];
  secret?: string;
  enabled: boolean;
  createdAt: string;
}

/**
 * Webhook 载荷
 */
export interface WebhookPayload {
  event: WebhookEvent;
  timestamp: string;
  loop_agent_version: string;
  session_id: string;
  data: Record<string, unknown>;
}

/**
 * Webhook 管理器
 */
export class WebhookManager {
  private subscriptions: Map<string, WebhookSubscription> = new Map();
  private orchestrator: Orchestrator;

  constructor(orchestrator: Orchestrator) {
    this.orchestrator = orchestrator;
  }

  /**
   * 订阅 Webhook
   */
  subscribe(sub: Omit<WebhookSubscription, "id" | "createdAt">): WebhookSubscription {
    const id = `wh-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const subscription: WebhookSubscription = {
      ...sub,
      id,
      createdAt: new Date().toISOString(),
    };
    this.subscriptions.set(id, subscription);
    return subscription;
  }

  /**
   * 取消订阅
   */
  unsubscribe(id: string): boolean {
    return this.subscriptions.delete(id);
  }

  /**
   * 触发 Webhook
   */
  async emit(event: WebhookEvent, data: Record<string, unknown>): Promise<void> {
    const payload: WebhookPayload = {
      event,
      timestamp: new Date().toISOString(),
      loop_agent_version: "v1.2",
      session_id: this.orchestrator.getSessionId(),
      data,
    };

    const targets = Array.from(this.subscriptions.values()).filter(
      (s) => s.enabled && s.events.includes(event)
    );

    await Promise.allSettled(
      targets.map((sub) => this.deliver(sub, payload))
    );
  }

  private async deliver(sub: WebhookSubscription, payload: WebhookPayload): Promise<void> {
    try {
      await fetch(sub.url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(sub.secret ? { "X-Webhook-Secret": sub.secret } : {}),
        },
        body: JSON.stringify(payload),
      });
    } catch (e) {
      console.error(`Webhook delivery failed for ${sub.id}:`, e);
    }
  }
}

/**
 * OpenAPI 规范（3.1.0）
 */
export const openApiSpec = {
  openapi: "3.1.0",
  info: {
    title: "Loop Agent Orchestrator API",
    version: "1.2.0",
    description: "Loop Agent v1.2 - 4 级封装的 Agent 编排引擎",
  },
  servers: [{ url: "http://localhost:9450", description: "Local" }],
  paths: {
    "/api/v1/loops": {
      post: {
        summary: "启动 Loop",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: { $ref: "#/components/schemas/StartLoopRequest" },
            },
          },
        },
        responses: {
          "200": {
            description: "Loop 启动成功",
            content: {
              "application/json": {
                schema: { $ref: "#/components/schemas/LoopResponse" },
              },
            },
          },
        },
      },
    },
    "/api/v1/loops/{id}": {
      get: {
        summary: "查询 Loop 状态",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: {
          "200": {
            description: "Loop 当前状态",
            content: {
              "application/json": {
                schema: { $ref: "#/components/schemas/LoopStatus" },
              },
            },
          },
        },
      },
    },
    "/api/v1/loops/{id}/abort": {
      post: {
        summary: "中止 Loop",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: { "200": { description: "已中止" } },
      },
    },
    "/api/v1/loops/{id}/decision-log": {
      get: {
        summary: "查询决策日志",
        parameters: [
          { name: "id", in: "path", required: true, schema: { type: "string" } },
        ],
        responses: { "200": { description: "决策日志" } },
      },
    },
    "/api/v1/webhooks": {
      post: {
        summary: "订阅 Webhook",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: { $ref: "#/components/schemas/WebhookSubscription" },
            },
          },
        },
        responses: { "201": { description: "订阅成功" } },
      },
    },
  },
  components: {
    schemas: {
      StartLoopRequest: {
        type: "object",
        required: ["prd_path"],
        properties: {
          prd_path: { type: "string" },
          mode: { enum: ["closed", "open"], default: "closed" },
          max_duration_hours: { type: "number", default: 9 },
          max_budget_usd: { type: "number", default: 100 },
        },
      },
      LoopResponse: {
        type: "object",
        properties: {
          loop_id: { type: "string" },
          status: { enum: ["started", "running", "completed", "failed"] },
          started_at: { type: "string", format: "date-time" },
        },
      },
      LoopStatus: {
        type: "object",
        properties: {
          loop_id: { type: "string" },
          current_phase: { type: "string" },
          progress: { type: "number" },
          budget_used_usd: { type: "number" },
          active_agents: { type: "number" },
        },
      },
      WebhookSubscription: {
        type: "object",
        required: ["url", "events"],
        properties: {
          url: { type: "string", format: "uri" },
          events: {
            type: "array",
            items: {
              enum: [
                "phase_started",
                "phase_completed",
                "phase_failed",
                "gate_passed",
                "gate_failed",
                "decision_logged",
                "agent_spawned",
                "agent_completed",
                "agent_failed",
                "loop_aborted",
                "loop_completed",
              ],
            },
          },
          secret: { type: "string" },
        },
      },
    },
  },
};

/**
 * HTTP 路由（伪代码，可嵌入 Bun.serve）
 */
export const httpRoutes = {
  "POST /api/v1/loops": "orchestrator.startLoop",
  "GET /api/v1/loops/:id": "orchestrator.getStatus",
  "POST /api/v1/loops/:id/abort": "orchestrator.abortLoop",
  "GET /api/v1/loops/:id/decision-log": "orchestrator.getDecisionLog",
  "POST /api/v1/webhooks": "webhookManager.subscribe",
  "GET /openapi.json": "return openApiSpec",
};
