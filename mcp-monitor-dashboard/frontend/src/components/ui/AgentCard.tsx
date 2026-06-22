/**
 * AgentCard Component - displays individual agent status
 */

import React from 'react';
import { Card, Tag, Progress } from 'antd';
import type { Agent, AgentStatus } from '@/types';
import './AgentCard.css';

interface AgentCardProps {
  agent: Agent;
  onClick?: (agent: Agent) => void;
}

const statusConfig: Record<AgentStatus, { color: string; label: string; className: string }> = {
  idle: { color: 'default', label: '空闲', className: 'status-idle' },
  running: { color: 'processing', label: '运行中', className: 'status-running' },
  error: { color: 'error', label: '异常', className: 'status-error' },
  complete: { color: 'success', label: '已完成', className: 'status-complete' },
};

const AgentCard: React.FC<AgentCardProps> = ({ agent, onClick }) => {
  const config = statusConfig[agent.status];

  return (
    <Card
      className={`agent-card ${config.className}`}
      hoverable
      size="small"
      onClick={() => onClick?.(agent)}
    >
      <div className="agent-card-header">
        <span className="agent-icon">{agent.icon}</span>
        <span className="agent-name">{agent.display_name}</span>
      </div>

      <div className="agent-card-status">
        <Tag color={config.color}>{config.label}</Tag>
      </div>

      {(agent.status === 'running' || agent.status === 'complete') && (
        <div className="agent-card-progress">
          <Progress
            percent={Math.round(agent.current_task_progress || 0)}
            size="small"
            status={
              agent.status === 'complete'
                ? 'success'
                : 'active'
            }
            strokeColor={
              agent.current_task_progress && agent.current_task_progress > 70
                ? '#52C41A'
                : undefined
            }
          />
        </div>
      )}

      {agent.current_task_name && (
        <div className="agent-card-task">
          <span className="task-name" title={agent.current_task_name}>
            {agent.current_task_name}
          </span>
        </div>
      )}
    </Card>
  );
};

export default AgentCard;
