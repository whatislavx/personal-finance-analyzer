import type { JobEvent } from './api';

const WS_BASE = (import.meta as any).env?.VITE_WS_BASE ?? 'ws://localhost:8000';

export type JobEventsMessage = { events: Array<{ id: string; type: string; message: string | null; created_at: string }> };

export interface WSOptions {
  token: string;
  jobId: string;
  onEvents: (events: JobEvent[]) => void;
  onStatus?: (s: 'connected' | 'disconnected' | 'reconnecting') => void;
}

export function connectJobEventsWS(opts: WSOptions) {
  let ws: WebSocket | null = null;
  let closedManually = false;
  let attempt = 0;

  const connect = () => {
    attempt += 1;
    opts.onStatus?.(attempt === 1 ? 'connected' : 'reconnecting');

    const base = WS_BASE.replace(/\/$/, '');
    const prefix = base.endsWith('/api') ? base : `${base}/api`;
    const url = `${prefix}/jobs/ws/${opts.jobId}?token=${encodeURIComponent(opts.token)}`;
    ws = new WebSocket(url);

    ws.onopen = () => {
      attempt = 0;
      opts.onStatus?.('connected');
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as JobEventsMessage;
        const events = (msg.events ?? []).map((e) => ({
          id: e.id,
          job_id: opts.jobId,
          type: e.type,
          message: e.message,
          created_at: e.created_at,
        }));
        if (events.length) opts.onEvents(events);
      } catch {
        // ignore
      }
    };

    ws.onclose = () => {
      ws = null;
      if (closedManually) return;
      opts.onStatus?.('disconnected');
      // exponential backoff, max 10s
      const delay = Math.min(10000, 500 * Math.pow(2, Math.max(0, attempt)));
      setTimeout(connect, delay);
    };

    ws.onerror = () => {
      // close triggers reconnect
      ws?.close();
    };
  };

  connect();

  return {
    close() {
      closedManually = true;
      ws?.close();
    },
  };
}

