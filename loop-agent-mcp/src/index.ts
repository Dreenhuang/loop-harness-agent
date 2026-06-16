#!/usr/bin/env node
/**
 * Loop Agent MCP Server for Claude Code
 * 暴露 6 个工具：start_loop, get_status, abort_loop, spawn_agent, list_agents, save_blackboard
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { OrchestratorClient } from "./lib/orchestrator-client.js";
import { resolve } from "path";

// 获取项目根目录（从命令行参数或环境变量）
const projectRoot =
  process.env.LOOP_AGENT_PROJECT_ROOT ??
  process.argv[2] ??
  process.cwd();

const client = new OrchestratorClient(resolve(projectRoot));

// 创建 MCP Server
const server = new Server(
  {
    name: "loop-agent-orchestrator",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 列出工具
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "start_loop",
      description: "启动 Loop Agent 完整流程（10 相位 + 4 门禁）",
      inputSchema: {
        type: "object",
        properties: {
          prd_path: {
            type: "string",
            description: "PRD 文档路径（相对于项目根目录）",
          },
          time_budget_hours: {
            type: "number",
            description: "时间预算（小时），默认 9",
            default: 9,
          },
          mode: {
            type: "enum",
            enum: ["closed", "open", "unattended"],
            description:
              "Loop 模式：closed=封闭, open=开放, unattended=无人值守",
            default: "closed",
          },
          project_name: {
            type: "string",
            description: "项目名称",
            default: "auto-dev",
          },
        },
        required: ["prd_path"],
      },
    },
    {
      name: "get_status",
      description: "查询 Loop Agent 当前状态（Phase、进度、预算、门禁）",
      inputSchema: {
        type: "object",
        properties: {
          loop_id: {
            type: "string",
            description: "Loop ID（可选）",
          },
        },
      },
    },
    {
      name: "abort_loop",
      description: "中止当前 Loop Agent 流程",
      inputSchema: {
        type: "object",
        properties: {
          loop_id: {
            type: "string",
            description: "Loop ID",
          },
          reason: {
            type: "string",
            description: "中止原因",
            default: "User requested abort",
          },
        },
        required: ["loop_id"],
      },
    },
    {
      name: "spawn_agent",
      description: "派发任务给指定的 Agent（16 角色之一）",
      inputSchema: {
        type: "object",
        properties: {
          agent_type: {
            type: "enum",
            enum: [
              "orchestrator",
              "product_manager",
              "requirements",
              "ux_researcher",
              "ui_designer",
              "architect",
              "backend",
              "frontend",
              "bug_defect_repairer",
              "code_reviewer",
              "professional_performance",
              "tester",
              "knowledge_curator",
              "documenter",
              "final_reviewer",
              "devops",
            ],
            description: "Agent 类型",
          },
          task_input: {
            type: "object",
            description: "任务输入（具体内容由 agent_type 决定）",
          },
        },
        required: ["agent_type", "task_input"],
      },
    },
    {
      name: "list_agents",
      description: "列出 16 角色 Agent Profile",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
    {
      name: "save_blackboard",
      description: "保存黑板记录（项目进度）",
      inputSchema: {
        type: "object",
        properties: {
          phase: {
            type: "string",
            description: "当前 Phase",
          },
          completed_items: {
            type: "array",
            items: { type: "string" },
            description: "已完成项列表",
          },
          uncertain_items: {
            type: "array",
            items: { type: "string" },
            description: "不确定项列表",
          },
          open_issues: {
            type: "array",
            items: { type: "string" },
            description: "开放问题列表",
          },
          next_plan: {
            type: "array",
            items: { type: "string" },
            description: "下一轮工作计划",
          },
          blackboard_updates: {
            type: "object",
            description: "黑板节点更新记录",
          },
        },
        required: ["phase"],
      },
    },
  ],
}));

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "start_loop": {
        const result = await client.startLoop(args as any);
        return {
          content: [
            {
              type: "text",
              text: `✅ Loop 已启动\n\n${JSON.stringify(result, null, 2)}`,
            },
          ],
        };
      }

      case "get_status": {
        const status = await client.getStatus((args as any)?.loop_id);
        return {
          content: [
            {
              type: "text",
              text: `📊 Loop Agent 状态\n\n${JSON.stringify(status, null, 2)}`,
            },
          ],
        };
      }

      case "abort_loop": {
        const result = await client.abortLoop(
          (args as any).loop_id,
          (args as any).reason
        );
        return {
          content: [
            {
              type: "text",
              text: `🛑 Loop 已中止\n\n${JSON.stringify(result, null, 2)}`,
            },
          ],
        };
      }

      case "spawn_agent": {
        const result = await client.spawnAgent(
          (args as any).agent_type,
          (args as any).task_input
        );
        return {
          content: [
            {
              type: "text",
              text: `🚀 Agent 任务已派发\n\n${JSON.stringify(result, null, 2)}`,
            },
          ],
        };
      }

      case "list_agents": {
        const agents = await client.listAgents();
        return {
          content: [
            {
              type: "text",
              text: `👥 16 角色 Agent Profile\n\n${agents
                .map(
                  (a) =>
                    `- ${a.display_name} (${a.id}) | Layer ${a.layer} | Type: ${a.type} | Skills: ${a.bound_skills.join(", ")}`
                )
                .join("\n")}`,
            },
          ],
        };
      }

      case "save_blackboard": {
        const result = await client.saveBlackboard(args as any);
        return {
          content: [
            {
              type: "text",
              text: `📝 黑板已保存\n\n${JSON.stringify(result, null, 2)}`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `❌ 错误: ${
            error instanceof Error ? error.message : String(error)
          }`,
        },
      ],
      isError: true,
    };
  }
});

// 启动 Server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`Loop Agent MCP Server started (project: ${projectRoot})`);
}

main().catch((error) => {
  console.error("Failed to start MCP Server:", error);
  process.exit(1);
});
