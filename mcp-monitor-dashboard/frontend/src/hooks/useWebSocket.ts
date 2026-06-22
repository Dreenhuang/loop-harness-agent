/**
 * WebSocket Hook - manages real-time connection
 * Uses refs for callbacks to avoid infinite reconnect loops
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import type { WSMessage, WSSubscribeRequest } from '@/types';

// WebSocket URL 配置：优先环境变量，其次 wss 协议，最后开发环境回退
const getWsUrl = (): string => {
  const envUrl = (import.meta as any).env?.VITE_WS_URL;
  
  if (envUrl) {
    return envUrl;
  }
  
  // 未配置环境变量时输出警告
  console.warn(
    '⚠️ VITE_WS_URL 未配置，使用默认回退逻辑。生产环境必须配置 VITE_WS_URL 环境变量。'
  );
  
  // 生产环境使用 wss 协议
  if (window.location.protocol === 'https:') {
    return `wss://${window.location.host}/ws`;
  }
  
  // 开发环境回退到 localhost
  return 'ws://localhost:8000/ws';
};

const WS_URL = getWsUrl();

const MAX_RECONNECT_ATTEMPTS = 10;

function dispatchFeedbackEvent(eventType: string, message: string, detail?: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent('mcp-feedback', {
      detail: { type: eventType, message, ...detail },
    })
  );
}

interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { autoConnect = true } = options;

  // Store callbacks in refs to avoid recreating connect() on every render
  const onMessageRef = useRef(options.onMessage);
  const onOpenRef = useRef(options.onOpen);
  const onCloseRef = useRef(options.onClose);
  const onErrorRef = useRef(options.onError);

  useEffect(() => { onMessageRef.current = options.onMessage; }, [options.onMessage]);
  useEffect(() => { onOpenRef.current = options.onOpen; }, [options.onOpen]);
  useEffect(() => { onCloseRef.current = options.onClose; }, [options.onClose]);
  useEffect(() => { onErrorRef.current = options.onError; }, [options.onError]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const autoConnectRef = useRef(autoConnect);
  const connectRef = useRef<() => void>();
  // 标记是否仍处于首次连接尝试中（在 onopen 成功前）
  const isInitialAttemptRef = useRef(true);
  useEffect(() => { autoConnectRef.current = autoConnect; }, [autoConnect]);

  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) return;

    if (retryCount >= MAX_RECONNECT_ATTEMPTS) {
      console.error(`WebSocket reconnection failed after ${MAX_RECONNECT_ATTEMPTS} attempts.`);
      setIsReconnecting(false);
      onErrorRef.current?.(new Event('reconnect_max_exceeded'));
      return;
    }

    setIsReconnecting(true);

    const delay = Math.min(
      retryCount === 0 ? 1000 : 1000 * Math.pow(2, retryCount),
      30000
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${retryCount + 1}/${MAX_RECONNECT_ATTEMPTS})`);

    reconnectTimeoutRef.current = window.setTimeout(() => {
      reconnectTimeoutRef.current = null;
      setRetryCount((prev) => prev + 1);
      connectRef.current?.();
    }, delay);
  }, [retryCount]);

  // Connect to WebSocket - stable reference (no deps that change)
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        // 首次连接成功后重置标记
        isInitialAttemptRef.current = false;
        console.log('🔌 WebSocket connected');
        setIsConnected(true);
        setIsReconnecting(false);
        setRetryCount(0);
        dispatchFeedbackEvent('ws-connected', '实时连接已建立');
        onOpenRef.current?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          onMessageRef.current?.(message);
        } catch (error) {
          console.error('Failed to parse WS message:', error);
        }
      };

      ws.onclose = (event) => {
        // 首次连接尝试结束（无论成功与否），重置标记
        const wasInitialAttempt = isInitialAttemptRef.current;
        if (wasInitialAttempt) {
          isInitialAttemptRef.current = false;
        }

        if (event.wasClean) {
          console.log('🔌 WebSocket disconnected cleanly:', event.code, event.reason);
        } else if (wasInitialAttempt) {
          console.log('🔌 WebSocket initial connection closed abnormally, scheduling reconnect...');
        } else {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        }
        setIsConnected(false);
        dispatchFeedbackEvent('ws-disconnected', '连接已断开，正在重连...');
        onCloseRef.current?.(event);

        // Auto-reconnect with exponential backoff
        if (!event.wasClean && autoConnectRef.current) {
          scheduleReconnect();
        }
      };

      ws.onerror = (event) => {
        // 页面初始化时首次连接可能因时机问题触发瞬时 error（常见于 1006）
        // 此类错误通常可由 onclose 触发的重连恢复，避免在控制台打印吓人的错误日志
        if (isInitialAttemptRef.current) {
          console.log('WebSocket initial connection error, will retry silently...');
        } else if (retryCount >= MAX_RECONNECT_ATTEMPTS - 1) {
          console.error('❌ WebSocket error (max reconnection attempts exceeded):', event);
        } else {
          console.error('❌ WebSocket error:', event);
        }
        dispatchFeedbackEvent('ws-error', '实时连接发生错误');
        onErrorRef.current?.(event);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
    }
  }, [scheduleReconnect, retryCount]);

  // Keep connect ref in sync without assigning during render
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // Send message
  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  // Subscribe to channels
  const subscribe = useCallback((channels: string[] = ['agent_status', 'logs', 'overview']) => {
    const request: WSSubscribeRequest = { type: 'subscribe', channels };
    send(request);
  }, [send]);

  // Request full sync
  const requestFullSync = useCallback(() => {
    send({ type: 'request_full_sync' });
  }, [send]);

  // Disconnect manually
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsReconnecting(false);
  }, []);

  // Auto-connect on mount - 延迟连接以避免页面初始化资源竞争
  useEffect(() => {
    if (!autoConnect) return;

    let timeoutId: number | undefined;

    // 等待页面完全加载，避免与 Vite HMR/client WebSocket 产生竞态
    const doConnect = () => {
      if (typeof document !== 'undefined' && document.readyState !== 'complete') {
        timeoutId = window.setTimeout(doConnect, 100);
        return;
      }
      connectRef.current?.();
    };

    // 额外增加 200ms 延迟，确保后端 ready 和浏览器事件循环稳定
    timeoutId = window.setTimeout(doConnect, 200);

    return () => {
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
      disconnect();
    };
  }, [autoConnect, disconnect]);

  // Heartbeat - send ping every 30s
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      send({ type: 'ping' });
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected, send]);

  return {
    isConnected,
    isReconnecting,
    connect,
    disconnect,
    send,
    subscribe,
    requestFullSync,
    retryCount,
  };
}
