import { useMetricsSSE } from './hooks/useMetricsSSE';
import type { Metric } from './hooks/useMetricsSSE';
import './App.css';

function MetricCard({ label, value, unit, color }: {
  label: string;
  value: number | null;
  unit: string;
  color: string;
}) {
  const displayValue = value !== null ? value.toFixed(1) : '-';
  const isHigh = value !== null && value > 80;

  return (
    <div className={`metric-card ${isHigh ? 'high' : ''}`} style={{ borderColor: color }}>
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={{ color }}>
        {displayValue}<span className="metric-unit">{unit}</span>
      </div>
    </div>
  );
}

function HostMetrics({ metric }: { metric: Metric }) {
  const time = new Date(metric.timestamp).toLocaleTimeString();

  return (
    <div className="host-card">
      <div className="host-header">
        <span className="host-name">{metric.host}</span>
        <span className="host-time">{time}</span>
      </div>
      <div className="metrics-grid">
        <MetricCard label="CPU" value={metric.cpu_percent} unit="%" color="#3b82f6" />
        <MetricCard label="Memory" value={metric.memory_percent} unit="%" color="#10b981" />
        <MetricCard label="Disk" value={metric.disk_percent} unit="%" color="#f59e0b" />
      </div>
    </div>
  );
}

function App() {
  const { metrics, connected, error } = useMetricsSSE();

  // Group metrics by host, keeping only the latest for each
  const latestByHost = metrics.reduce((acc, metric) => {
    if (!acc[metric.host]) {
      acc[metric.host] = metric;
    }
    return acc;
  }, {} as Record<string, Metric>);

  const hosts = Object.values(latestByHost);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Nazar Dashboard</h1>
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? 'Live' : 'Disconnected'}
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="hosts-section">
        <h2>Monitored Hosts ({hosts.length})</h2>
        <div className="hosts-grid">
          {hosts.map((metric) => (
            <HostMetrics key={metric.host} metric={metric} />
          ))}
        </div>
        {hosts.length === 0 && (
          <div className="no-data">Waiting for metrics...</div>
        )}
      </section>

      <section className="recent-section">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          {metrics.slice(0, 10).map((metric, i) => (
            <div key={`${metric.host}-${metric.timestamp}-${i}`} className="activity-item">
              <span className="activity-host">{metric.host}</span>
              <span className="activity-metrics">
                CPU: {metric.cpu_percent?.toFixed(1) ?? '-'}% |
                Mem: {metric.memory_percent?.toFixed(1) ?? '-'}%
              </span>
              <span className="activity-time">
                {new Date(metric.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
