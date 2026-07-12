import { useRef, useState } from 'react';
import { useMetricsSSE } from './hooks/useMetricsSSE';
import type { Metric } from './hooks/useMetricsSSE';
import './App.css';

interface Point {
  t: string;
  v: number;
}

const SPARK_W = 260;
const SPARK_H = 52;
const SPARK_PAD = 4;

function Sparkline({ points, color }: { points: Point[]; color: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  if (points.length < 2) {
    return <div className="spark spark-empty">collecting…</div>;
  }

  const values = points.map((p) => p.v);
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (max - min < 1) {
    const mid = (max + min) / 2;
    min = mid - 0.5;
    max = mid + 0.5;
  }

  const px = (i: number) => (i / (points.length - 1)) * (SPARK_W - 2 * SPARK_PAD) + SPARK_PAD;
  const py = (v: number) => (1 - (v - min) / (max - min)) * (SPARK_H - 2 * SPARK_PAD) + SPARK_PAD;

  const line = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${px(i).toFixed(1)},${py(p.v).toFixed(1)}`)
    .join(' ');
  const area = `${line} L${px(points.length - 1).toFixed(1)},${SPARK_H} L${px(0).toFixed(1)},${SPARK_H} Z`;

  const lastIdx = points.length - 1;
  const dotIdx = hoverIdx ?? lastIdx;
  const dot = points[dotIdx];
  const dotLeft = (px(dotIdx) / SPARK_W) * 100;
  const dotTop = (py(dot.v) / SPARK_H) * 100;

  const handleMove = (e: React.MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const frac = (e.clientX - rect.left) / rect.width;
    setHoverIdx(Math.min(lastIdx, Math.max(0, Math.round(frac * lastIdx))));
  };

  return (
    <div
      ref={containerRef}
      className="spark"
      onMouseMove={handleMove}
      onMouseLeave={() => setHoverIdx(null)}
    >
      <svg viewBox={`0 0 ${SPARK_W} ${SPARK_H}`} preserveAspectRatio="none">
        <path d={area} fill={color} opacity={0.1} />
        <path
          d={line}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <span
        className="spark-dot"
        style={{ left: `${dotLeft}%`, top: `${dotTop}%`, background: color }}
      />
      {hoverIdx !== null && (
        <div
          className="spark-tooltip"
          style={{ left: `${dotLeft}%`, transform: `translateX(${dotLeft > 70 ? '-100%' : '-50%'})` }}
        >
          {dot.v.toFixed(1)}% · {new Date(dot.t).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

function StatTile({ label, color, points, windowMin, windowMax }: {
  label: string;
  color: string;
  points: Point[];
  windowMin: number | null;
  windowMax: number | null;
}) {
  const latest = points.length > 0 ? points[points.length - 1].v : null;
  const isHigh = latest !== null && latest > 80;

  return (
    <div className="tile">
      <div className="tile-head">
        <span className="key-dot" style={{ background: color }} />
        <span className="tile-label">{label}</span>
        {isHigh && <span className="badge-high">▲ High</span>}
      </div>
      <div className="tile-value">
        {latest !== null ? latest.toFixed(1) : '–'}
        <span className="tile-unit">%</span>
      </div>
      <div className="tile-range">
        {windowMin !== null && windowMax !== null
          ? `${windowMin.toFixed(1)} – ${windowMax.toFixed(1)}% over sample window`
          : ' '}
      </div>
      <Sparkline points={points} color={color} />
    </div>
  );
}

function formatRate(bytesPerSec: number): string {
  if (bytesPerSec >= 1_000_000) return `${(bytesPerSec / 1_000_000).toFixed(1)} MB/s`;
  if (bytesPerSec >= 1_000) return `${(bytesPerSec / 1_000).toFixed(1)} kB/s`;
  return `${bytesPerSec.toFixed(0)} B/s`;
}

function networkRates(series: Metric[]): { down: string; up: string } | null {
  if (series.length < 2) return null;
  const prev = series[series.length - 2];
  const curr = series[series.length - 1];
  const seconds =
    (new Date(curr.timestamp).getTime() - new Date(prev.timestamp).getTime()) / 1000;
  if (seconds <= 0 || curr.network_in === null || prev.network_in === null ||
      curr.network_out === null || prev.network_out === null) return null;
  const down = (curr.network_in - prev.network_in) / seconds;
  const up = (curr.network_out - prev.network_out) / seconds;
  if (down < 0 || up < 0) return null;
  return { down: formatRate(down), up: formatRate(up) };
}

function seriesOf(series: Metric[], field: 'cpu_percent' | 'memory_percent' | 'disk_percent'): Point[] {
  return series
    .filter((m) => m[field] !== null)
    .map((m) => ({ t: m.timestamp, v: m[field] as number }));
}

function HostCard({ series }: { series: Metric[] }) {
  const latest = series[series.length - 1];
  const rates = networkRates(series);

  return (
    <div className="host-card">
      <div className="host-header">
        <span className="host-name">{latest.host}</span>
        <span className="host-time">
          Updated {new Date(latest.timestamp).toLocaleTimeString()}
        </span>
      </div>
      <div className="tiles-grid">
        <StatTile
          label="CPU"
          color="var(--series-cpu)"
          points={seriesOf(series, 'cpu_percent')}
          windowMin={latest.cpu_min}
          windowMax={latest.cpu_max}
        />
        <StatTile
          label="Memory"
          color="var(--series-mem)"
          points={seriesOf(series, 'memory_percent')}
          windowMin={latest.memory_min}
          windowMax={latest.memory_max}
        />
        <StatTile
          label="Disk"
          color="var(--series-disk)"
          points={seriesOf(series, 'disk_percent')}
          windowMin={latest.disk_min}
          windowMax={latest.disk_max}
        />
      </div>
      {rates && (
        <div className="host-footer">
          Network&nbsp;&nbsp;↓ {rates.down}&nbsp;&nbsp;↑ {rates.up}
        </div>
      )}
    </div>
  );
}

function App() {
  const { metrics, error } = useMetricsSSE();

  // metrics arrive newest-first; group into chronological series per host
  const byHost: Record<string, Metric[]> = {};
  for (let i = metrics.length - 1; i >= 0; i--) {
    const m = metrics[i];
    (byHost[m.host] ??= []).push(m);
  }
  const hosts = Object.values(byHost);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Nazar</h1>
          <div className="subtitle">Live system metrics</div>
        </div>
      </header>

      {error && <div className="error-banner">⚠ {error}</div>}

      <section>
        <h2>Monitored hosts ({hosts.length})</h2>
        <div className="hosts-grid">
          {hosts.map((series) => (
            <HostCard key={series[0].host} series={series} />
          ))}
        </div>
        {hosts.length === 0 && <div className="no-data">Waiting for metrics…</div>}
      </section>

      {metrics.length > 0 && (
        <section>
          <h2>Recent activity</h2>
          <table className="activity-table">
            <thead>
              <tr>
                <th>Host</th>
                <th className="num">CPU</th>
                <th className="num">Memory</th>
                <th className="num">Disk</th>
                <th className="time">Time</th>
              </tr>
            </thead>
            <tbody>
              {metrics.slice(0, 10).map((m, i) => (
                <tr key={`${m.host}-${m.timestamp}-${i}`}>
                  <td>{m.host}</td>
                  <td className="num">{m.cpu_percent?.toFixed(1) ?? '–'}%</td>
                  <td className="num">{m.memory_percent?.toFixed(1) ?? '–'}%</td>
                  <td className="num">{m.disk_percent?.toFixed(1) ?? '–'}%</td>
                  <td className="time">{new Date(m.timestamp).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

export default App;
