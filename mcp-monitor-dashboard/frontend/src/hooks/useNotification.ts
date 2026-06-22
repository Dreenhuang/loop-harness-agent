/**
 * useNotification - 业务层通知 Hook
 *
 * 在 NotificationProvider 基础上封装了去重、节流、加载状态等常用模式。
 */

import { useCallback, useRef } from 'react';
import { useNotificationContext, type FeedbackOptions } from '@/components/feedback/NotificationProvider';

type NotifyType = 'success' | 'warning' | 'error' | 'info';

interface UseNotificationReturn {
  notify: (options: FeedbackOptions) => string | void;
  success: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  warning: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  error: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  info: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  modal: (options: Omit<FeedbackOptions, 'display'>) => string;
  inline: (options: Omit<FeedbackOptions, 'display'>) => string;
  removeInline: (id: string) => void;
  clearAll: () => void;
  /** 相同 key 的提示在 lockoutMs 内只触发一次 */
  dedup: (key: string, type: NotifyType, message: string, lockoutMs?: number) => void;
  /** 包装异步函数：自动展示 loading / success / error */
  withLoading: <T>(
    promise: Promise<T>,
    messages: {
      loading?: string;
      success?: string | ((result: T) => string);
      error?: string | ((err: unknown) => string);
    }
  ) => Promise<T>;
}

export function useNotification(): UseNotificationReturn {
  const ctx = useNotificationContext();
  const dedupMapRef = useRef<Map<string, number>>(new Map());
  const inlineIdRef = useRef<string | null>(null);

  const dedup = useCallback(
    (key: string, type: NotifyType, message: string, lockoutMs = 5000) => {
      const now = Date.now();
      const last = dedupMapRef.current.get(key);
      if (last && now - last < lockoutMs) return;
      dedupMapRef.current.set(key, now);
      ctx[type](message);
    },
    [ctx]
  );

  const withLoading = useCallback(
    async <T,>(
      promise: Promise<T>,
      messages: {
        loading?: string;
        success?: string | ((result: T) => string);
        error?: string | ((err: unknown) => string);
      }
    ): Promise<T> => {
      if (messages.loading) {
        // inline loading 提示，成功/失败后移除
        inlineIdRef.current = ctx.inline({
          type: 'info',
          message: messages.loading,
          icon: '⏳',
        }) as string;
      }

      try {
        const result = await promise;
        if (inlineIdRef.current) {
          ctx.removeInline(inlineIdRef.current);
          inlineIdRef.current = null;
        }
        if (messages.success) {
          const text = typeof messages.success === 'function' ? messages.success(result) : messages.success;
          ctx.success(text);
        }
        return result;
      } catch (err) {
        if (inlineIdRef.current) {
          ctx.removeInline(inlineIdRef.current);
          inlineIdRef.current = null;
        }
        if (messages.error) {
          const text = typeof messages.error === 'function' ? messages.error(err) : messages.error;
          ctx.error(text);
        }
        throw err;
      }
    },
    [ctx]
  );

  return {
    notify: ctx.notify,
    success: ctx.success,
    warning: ctx.warning,
    error: ctx.error,
    info: ctx.info,
    modal: ctx.modal,
    inline: ctx.inline,
    removeInline: ctx.removeInline,
    clearAll: ctx.clearAll,
    dedup,
    withLoading,
  };
}
