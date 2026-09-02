import { useState, useEffect } from 'react';

export interface Metric {
  timestamp: string;
  host: string;
  cpu_percent: number | null;
  cpu_min: number | null;
  cpu_max: number | null;
  memory_percent: number | null;
  memory_min: number | null;
  memory_max: number | null;
  disk_percent: number | null;
  disk_min: number | null;
  disk_max: number | null;
  network_in: number | null;
  network_out: number | null;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const MAX_METRICS = 50;
const RECONNECT_MS = 3000;

export function useMetricsSSE(host?: string) {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;
    let source: EventSource | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      if (disposed) return;
      const url = host
        ? `${API_URL}/stream?host=${encodeURIComponent(host)}`
        : `${API_URL}/stream`;
      source = new EventSource(url);

      source.onopen = () => {
        setConnected(true);
        setError(null);
      };

      source.onmessage = (event) => {
        try {
          const metric: Metric = JSON.parse(event.data);
          setMetrics((prev) => [metric, ...prev].slice(0, MAX_METRICS));
        } catch (e) {
          console.error('Failed to parse metric:', e);
        }
      };

      source.onerror = () => {
        setConnected(false);
        setError('Connection lost. Reconnecting...');
        source?.close();
        source = null;
        if (!disposed) retryTimer = setTimeout(connect, RECONNECT_MS);
      };
    };

    connect();

    return () => {
      disposed = true;
      clearTimeout(retryTimer);
      source?.close();
    };
  }, [host]);

  return { metrics, connected, error };
}
