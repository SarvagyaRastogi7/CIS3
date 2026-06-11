type Variant = "navy" | "gold" | "forest" | "slate";

interface Props {
  label: string;
  value: string;
  sub?: string;
  variant?: Variant;
  trend?: "up" | "down" | "neutral";
}

export function MetricCard({ label, value, sub, variant = "navy", trend }: Props) {
  const trendLabel = trend === "up" ? "Favorable" : trend === "down" ? "Adverse" : undefined;

  return (
    <div className={`metric-card metric-${variant}`}>
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        {trendLabel && <span className={`metric-trend trend-${trend}`}>{trendLabel}</span>}
      </div>
      <span className="metric-value">{value}</span>
      {sub && <span className="metric-sub">{sub}</span>}
    </div>
  );
}
