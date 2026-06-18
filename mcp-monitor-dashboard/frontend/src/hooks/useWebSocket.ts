/**
 * WebSocket Hook - manages real-time connection
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import type { WSMessage, WSSubscribeRequest } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`;

interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onMessage, onOpen, onClose, onError, autoConnect = true } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const retryCountRef = useRef(0);

  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('🔌 WebSocket connected');
        setIsConnected(true);
        setIsReconnecting(false);
        retryCountRef.current = 0;
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WS message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        onClose?.(event);

        // Auto-reconnect with exponential backoff
        if (!event.wasClean && autoConnect) {
          scheduleReconnect();
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        onError?.(event);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
    }
  }, [onOpen, onClose, onError, autoConnect]);

  // Schedule reconnection attempt
  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) return;

    setIsReconnecting(true);

    const delay = Math.min(
      retryCountRef.current === 0 ? 0 : 1000 * Math.pow(2, retryCountRef.current),
      30000
    );

    console.log(`🔄 Reconnecting in ${delay}ms (attempt ${retryCountRef.current + 1})`);

    reconnectTimeoutRef.current = window.setTimeout(() => {
      reconnectTimeoutRef.current = null;
      retryCountRef.current += 1;
      connect();
    }, delay);
  }, [connect]);

  // Send message
  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    console.warn('⚠️ Cannot send: WebSocket not connected');
    return false;
  }, []);

  // Subscribe to channels
  const subscribe = useCallback((channels: string[] = ['agent_status', 'logs', 'overview']) => {
    const request: WSSubscribeRequest = { type: 'subscribe', channels };
    send(request);
  }, [send]);

  // Request full sync (after reconnection)
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

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

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
    retryCount: retryCountRef.current,
  };
}
