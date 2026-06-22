/**
 * NotificationProvider - 全局通知与反馈系统
 *
 * 提供统一的 Toast / Modal / Inline 三种提示方式，支持：
 * - 4 种语义类型：success / warning / error / info
 * - 可配置时长、位置、声音开关（localStorage 持久化）
 * - 可访问性：role、aria-live、aria-label、键盘 Esc 关闭
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import './feedback.css';

export type FeedbackType = 'success' | 'warning' | 'error' | 'info';
export type FeedbackDisplay = 'toast' | 'modal' | 'inline';
export type ToastPosition =
  | 'topRight'
  | 'topLeft'
  | 'bottomRight'
  | 'bottomLeft';

export interface FeedbackConfig {
  duration: number; // 毫秒，0 表示不自动关闭
  position: ToastPosition;
  soundEnabled: boolean;
  maxToastCount: number;
  pauseOnHover: boolean;
}

export interface FeedbackOptions {
  id?: string;
  type?: FeedbackType;
  display?: FeedbackDisplay;
  title?: string;
  message: string;
  description?: string;
  duration?: number; // 覆盖全局
  closable?: boolean;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  onClose?: () => void;
}

interface InlineItem extends Required<Pick<FeedbackOptions, 'id' | 'type' | 'message'>> {
  description?: string;
}

export interface NotificationContextValue {
  config: FeedbackConfig;
  updateConfig: (patch: Partial<FeedbackConfig>) => void;
  notify: (options: FeedbackOptions) => string | void;
  success: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  warning: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  error: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  info: (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => void;
  modal: (options: Omit<FeedbackOptions, 'display'>) => string;
  inline: (options: Omit<FeedbackOptions, 'display'>) => string;
  removeInline: (id: string) => void;
  clearAll: () => void;
}

const DEFAULT_CONFIG: FeedbackConfig = {
  duration: 3000,
  position: 'topRight',
  soundEnabled: false,
  maxToastCount: 5,
  pauseOnHover: true,
};

const STORAGE_KEY = 'mcp_feedback_config_v1';

const TYPE_META: Record<
  FeedbackType,
  {
    color: string;
    bg: string;
    border: string;
    icon: React.ReactNode;
    ariaLive: 'polite' | 'assertive';
  }
> = {
  success: {
    color: '#52C41A',
    bg: '#F6FFED',
    border: '#B7EB8F',
    icon: <CheckCircleOutlined />,
    ariaLive: 'polite',
  },
  warning: {
    color: '#FAAD14',
    bg: '#FFFBE6',
    border: '#FFE58F',
    icon: <ExclamationCircleOutlined />,
    ariaLive: 'polite',
  },
  error: {
    color: '#FF4D4F',
    bg: '#FFF2F0',
    border: '#FFCCC7',
    icon: <CloseCircleOutlined />,
    ariaLive: 'assertive',
  },
  info: {
    color: '#1890FF',
    bg: '#E6F7FF',
    border: '#91D5FF',
    icon: <InfoCircleOutlined />,
    ariaLive: 'polite',
  },
};

function loadConfig(): FeedbackConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...DEFAULT_CONFIG, ...parsed };
    }
  } catch {
    // ignore
  }
  return DEFAULT_CONFIG;
}

function saveConfig(config: FeedbackConfig) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  } catch {
    // ignore
  }
}

function playSound(type: FeedbackType) {
  if (typeof window === 'undefined') return;
  try {
    const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    const frequencies: Record<FeedbackType, number> = {
      success: 880,
      warning: 660,
      error: 220,
      info: 440,
    };
    osc.frequency.value = frequencies[type] || 440;
    osc.type = type === 'error' ? 'sawtooth' : 'sine';
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch {
    // ignore
  }
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

export const useNotificationContext = () => {
  const ctx = useContext(NotificationContext);
  if (!ctx) {
    throw new Error('useNotificationContext must be used within NotificationProvider');
  }
  return ctx;
};

interface ToastItem extends FeedbackOptions {
  id: string;
  createdAt: number;
  remaining: number;
  meta: (typeof TYPE_META)[FeedbackType];
}

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<FeedbackConfig>(loadConfig);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [modals, setModals] = useState<Array<FeedbackOptions & { id: string }>>([]);
  const [inlines, setInlines] = useState<InlineItem[]>([]);
  const timersRef = useRef<Map<string, number>>(new Map());
  const toastIdRef = useRef(0);
  const modalIdRef = useRef(0);
  const inlineIdRef = useRef(0);

  useEffect(() => {
    saveConfig(config);
  }, [config]);

  const updateConfig = useCallback((patch: Partial<FeedbackConfig>) => {
    setConfig((prev) => ({ ...prev, ...patch }));
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      window.clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const scheduleToastClose = useCallback(
    (id: string, duration: number) => {
      if (duration <= 0) return;
      const timer = window.setTimeout(() => {
        removeToast(id);
      }, duration);
      timersRef.current.set(id, timer);
    },
    [removeToast]
  );

  const notify = useCallback(
    (options: FeedbackOptions): string | void => {
      const type = options.type || 'info';
      const display = options.display || 'toast';

      if (config.soundEnabled) {
        playSound(type);
      }

      if (display === 'modal') {
        const id = `modal-${++modalIdRef.current}`;
        setModals((prev) => [...prev, { ...options, id, type }]);
        return id;
      }

      if (display === 'inline') {
        const id = `inline-${++inlineIdRef.current}`;
        setInlines((prev) => [
          ...prev,
          {
            id,
            type,
            message: options.message,
            description: options.description,
          },
        ]);
        return id;
      }

      // Toast
      const id = `toast-${++toastIdRef.current}`;
      const duration = options.duration ?? config.duration;
      const meta = TYPE_META[type];
      const newToast: ToastItem = {
        ...options,
        id,
        type,
        createdAt: Date.now(),
        remaining: duration,
        meta,
      };

      setToasts((prev) => {
        const next = [...prev, newToast];
        if (next.length > config.maxToastCount) {
          const [first, ...rest] = next;
          removeToast(first.id);
          return rest;
        }
        return next;
      });

      scheduleToastClose(id, duration);
      return id;
    },
    [config, removeToast, scheduleToastClose]
  );

  const success = useCallback(
    (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => {
      notify({ type: 'success', message, ...options });
    },
    [notify]
  );

  const warning = useCallback(
    (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => {
      notify({ type: 'warning', message, ...options });
    },
    [notify]
  );

  const error = useCallback(
    (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => {
      notify({ type: 'error', message, duration: 0, ...options });
    },
    [notify]
  );

  const info = useCallback(
    (message: string, options?: Omit<FeedbackOptions, 'type' | 'message'>) => {
      notify({ type: 'info', message, ...options });
    },
    [notify]
  );

  const modal = useCallback(
    (options: Omit<FeedbackOptions, 'display'>) => {
      return notify({ ...options, display: 'modal' }) as string;
    },
    [notify]
  );

  const inline = useCallback(
    (options: Omit<FeedbackOptions, 'display'>) => {
      return notify({ ...options, display: 'inline' }) as string;
    },
    [notify]
  );

  const removeInline = useCallback((id: string) => {
    setInlines((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setToasts([]);
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current.clear();
    setModals([]);
    setInlines([]);
  }, []);

  const closeModal = useCallback(
    (id: string) => {
      setModals((prev) => prev.filter((m) => m.id !== id));
    },
    []
  );

  const contextValue = useMemo(
    () => ({
      config,
      updateConfig,
      notify,
      success,
      warning,
      error,
      info,
      modal,
      inline,
      removeInline,
      clearAll,
    }),
    [config, updateConfig, notify, success, warning, error, info, modal, inline, removeInline, clearAll]
  );

  // 全局键盘监听：Esc 关闭最新 Toast / Modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (modals.length > 0) {
        closeModal(modals[modals.length - 1].id);
      } else if (toasts.length > 0) {
        removeToast(toasts[toasts.length - 1].id);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toasts, modals, closeModal, removeToast]);

  // 关闭前回调触发
  const handleCloseToast = useCallback(
    (id: string, onClose?: () => void) => {
      removeToast(id);
      onClose?.();
    },
    [removeToast]
  );

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}

      {/* Toast Container */}
      <div
        className={`feedback-toast-container feedback-toast-${config.position}`}
        role="region"
        aria-label="通知消息列表"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`feedback-toast feedback-toast-${toast.type}`}
            role="status"
            aria-live={toast.meta.ariaLive}
            aria-atomic="true"
            style={{
              backgroundColor: toast.meta.bg,
              borderColor: toast.meta.border,
              color: 'rgba(0,0,0,0.85)',
            }}
            onMouseEnter={() => {
              if (config.pauseOnHover) {
                const timer = timersRef.current.get(toast.id);
                if (timer) {
                  window.clearTimeout(timer);
                  timersRef.current.delete(toast.id);
                }
              }
            }}
            onMouseLeave={() => {
              if (config.pauseOnHover && toast.remaining > 0) {
                scheduleToastClose(toast.id, toast.remaining);
              }
            }}
          >
            <span
              className="feedback-toast-icon"
              style={{ color: toast.meta.color }}
              aria-hidden="true"
            >
              {toast.icon ?? toast.meta.icon}
            </span>
            <div className="feedback-toast-content">
              {toast.title && <div className="feedback-toast-title">{toast.title}</div>}
              <div className="feedback-toast-message">{toast.message}</div>
              {toast.description && (
                <div className="feedback-toast-description">{toast.description}</div>
              )}
            </div>
            {(toast.closable ?? true) && (
              <button
                type="button"
                className="feedback-toast-close"
                onClick={() => handleCloseToast(toast.id, toast.onClose)}
                aria-label="关闭通知"
              >
                <CloseOutlined />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Inline Container - rendered as a hidden portal so inline messages can be mounted by callers */}
      {inlines.length > 0 && (
        <div className="feedback-inline-container" role="region" aria-label="行内提示消息列表">
          {inlines.map((item) => {
            const meta = TYPE_META[item.type];
            return (
              <div
                key={item.id}
                className={`feedback-inline feedback-inline-${item.type}`}
                role="status"
                aria-live={meta.ariaLive}
                aria-atomic="true"
                style={{ backgroundColor: meta.bg, borderColor: meta.border, color: 'rgba(0,0,0,0.85)' }}
              >
                <span className="feedback-inline-icon" style={{ color: meta.color }} aria-hidden="true">
                  {meta.icon}
                </span>
                <div className="feedback-inline-content">
                  <span className="feedback-inline-message">{item.message}</span>
                  {item.description && (
                    <span className="feedback-inline-description">{item.description}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal Container */}
      {modals.length > 0 && (
        <div
          className="feedback-modal-backdrop"
          role="presentation"
          onClick={(e) => {
            if (e.target === e.currentTarget && modals.length > 0) {
              closeModal(modals[modals.length - 1].id);
            }
          }}
        >
          {modals.map((m) => {
            const meta = TYPE_META[m.type || 'info'];
            return (
              <div
                key={m.id}
                className={`feedback-modal feedback-modal-${m.type}`}
                role="alertdialog"
                aria-modal="true"
                aria-labelledby={`modal-title-${m.id}`}
                aria-describedby={`modal-desc-${m.id}`}
                style={{ borderColor: meta.border }}
              >
                <div className="feedback-modal-header">
                  <span className="feedback-modal-icon" style={{ color: meta.color }}>
                    {m.icon ?? meta.icon}
                  </span>
                  <h3 id={`modal-title-${m.id}`} className="feedback-modal-title">
                    {m.title || (m.type === 'error' ? '错误' : '提示')}
                  </h3>
                  <button
                    type="button"
                    className="feedback-modal-close"
                    onClick={() => closeModal(m.id)}
                    aria-label="关闭弹窗"
                  >
                    <CloseOutlined />
                  </button>
                </div>
                <div id={`modal-desc-${m.id}`} className="feedback-modal-body">
                  <p>{m.message}</p>
                  {m.description && <p className="feedback-modal-description">{m.description}</p>}
                </div>
                {(m.actions || m.closable !== false) && (
                  <div className="feedback-modal-footer">
                    {m.actions}
                    {m.closable !== false && (
                      <button
                        type="button"
                        className="feedback-btn feedback-btn-primary"
                        onClick={() => closeModal(m.id)}
                      >
                        知道了
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </NotificationContext.Provider>
  );
};

