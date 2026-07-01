import type { MetricRow, MetricTable } from "../types";

export default function MetricsPanel({ metrics }: { metrics: MetricTable }) {
  const numericMetrics = metrics.rows.filter(isNumericMetric).slice(0, 8);
  return (
    <section className="panel">
      <header className="panel-header">
        <h2>Metrics</h2>
        <span>{metrics.rows.length}</span>
      </header>
      <div className="metric-list">
        {numericMetrics.map((metric) => (
          <div className="metric-row" key={metric.name}>
            <div>
              <span className="metric-name">{metric.name}</span>
              {metric.unit ? <span className="metric-unit">{metric.unit}</span> : null}
            </div>
            <strong>{formatMetricValue(metric.value)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function isNumericMetric(metric: MetricRow): boolean {
  return typeof metric.value === "number";
}

function formatMetricValue(value: unknown): string {
  if (typeof value !== "number") {
    return String(value);
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}
