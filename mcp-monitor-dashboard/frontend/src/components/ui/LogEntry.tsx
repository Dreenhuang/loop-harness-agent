/**
 * LogEntry Component - displays a single log line
 */

import React from 'react';
import type { LogEntry, LogLevel } from '@/types';
import './LogEntry.css';

interface LogEntryProps {
  log: LogEntry;
}

const levelConfig: Record<LogLevel, { className: string; label: string }> = {
  debug: { className: 'level-debug', label: 'DEBUG' },
  info: { className: 'level-info', label: 'INFO' },
  warn: { className: 'level-warn', label: 'WARN' },
  error: { className: 'level-error', label: 'ERROR' },
};

const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }) + '.' + String(date.getMilliseconds()).padStart(3, '0');
  } catch {
    return timestamp;
  }
};

const LogEntryComponent: React.FC<LogEntryProps> = ({ log }) => {
  const config = levelConfig[log.level];

  return (
    <div className={`log-entry ${config.className}`}>
      <span className="log-timestamp">{formatTimestamp(log.timestamp)}</span>
      <span className="log-agent" title="点击过滤此 Agent">
        [{log.agent_id}]
      </span>
      <span className={`log-level ${config.className}`}>[{config.label}]</span>
      <span className="log-message">{log.message}</span>
    </div>
  );
};

export default LogEntryComponent;
