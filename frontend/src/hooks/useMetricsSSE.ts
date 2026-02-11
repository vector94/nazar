import { useState, useEffect, useCallback } from 'react';

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

export function useMetricsSSE(host?: string) {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    const url = host ? `${API_URL}/stream?host=${host}` : `${API_URL}/stream`;
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      setConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const metric: Metric = JSON.parse(event.data);
        setMetrics((prev) => {
          const updated = [metric, ...prev].slice(0, 50);
          return updated;
        });
      } catch (e) {
        console.error('Failed to parse metric:', e);
      }
    };

    eventSource.onerror = () => {
      setConnected(false);
      setError('Connection lost. Reconnecting...');
      eventSource.close();
      setTimeout(connect, 3000);
    };

    return eventSource;
  }, [host]);

  useEffect(() => {
    const eventSource = connect();
    return () => eventSource.close();
  }, [connect]);

  return { metrics, connected, error };
}
