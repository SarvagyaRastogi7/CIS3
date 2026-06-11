import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ForecastMonth } from "../types";
import { formatINR, formatINRChart } from "../utils/currency";
import { formatForecastMonth } from "../utils/forecastFormat";

const CHART = {
  cashFlow: "#1e6b4f",
  sales: "#1a3358",
  expenses: "#8b6914",
  grid: "#d8dfe8",
  tick: "#5c6b7f",
};

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-label">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: <strong>{formatINR(entry.value)}</strong>
        </p>
      ))}
    </div>
  );
};

interface Props {
  data: ForecastMonth[];
  title?: string;
  subtitle?: string;
}

export function ForecastChart({
  data,
  title = "Cashflow Projection",
  subtitle,
}: Props) {
  const chartData = data.map((d) => ({
    month: formatForecastMonth(d.month, "2-digit"),
    cash_flow: d.cash_flow,
    total_sales: d.total_sales,
    total_expenses: d.total_expenses,
  }));

  return (
    <section className="card card-chart">
      <div className="card-header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={360}>
          <ComposedChart data={chartData} margin={{ top: 12, right: 16, left: 4, bottom: 0 }}>
            <defs>
              <linearGradient id="cfGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={CHART.cashFlow} stopOpacity={0.18} />
                <stop offset="100%" stopColor={CHART.cashFlow} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="4 4" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: CHART.tick }} axisLine={{ stroke: CHART.grid }} tickLine={false} />
            <YAxis tickFormatter={formatINRChart} tick={{ fontSize: 11, fill: CHART.tick }} axisLine={false} tickLine={false} width={56} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 16, fontFamily: "IBM Plex Sans, sans-serif" }} />
            <Area
              type="monotone"
              dataKey="cash_flow"
              name="Net Cashflow"
              stroke={CHART.cashFlow}
              strokeWidth={2.5}
              fill="url(#cfGradient)"
              dot={false}
            />
            <Line type="monotone" dataKey="total_sales" stroke={CHART.sales} strokeWidth={2} dot={false} name="Revenue" />
            <Line type="monotone" dataKey="total_expenses" stroke={CHART.expenses} strokeWidth={2} dot={false} name="Expenditure" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
