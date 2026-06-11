import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ScenarioForecast } from "../types";
import { SCENARIO_COLORS } from "../utils/chartTheme";
import { formatINR, formatINRChart } from "../utils/currency";

interface Props {
  scenarios: ScenarioForecast[];
}

export function ScenarioChart({ scenarios }: Props) {
  const chartData = scenarios.map((s, i) => ({
    name: s.label.split(" (")[0],
    net_cash_flow: s.summary.net_cash_flow,
    avg_monthly: s.summary.avg_monthly_cash_flow,
    color: SCENARIO_COLORS[i % SCENARIO_COLORS.length],
  }));

  return (
    <section className="card card-chart">
      <div className="card-header">
        <div>
          <h2>Stress Scenario Analysis</h2>
          <p className="card-subtitle">Period totals for base vs your configured stress scenario</p>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={chartData} barGap={6} barCategoryGap="18%">
            <CartesianGrid strokeDasharray="4 4" stroke="#d8dfe8" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#5c6b7f" }} axisLine={{ stroke: "#d8dfe8" }} tickLine={false} interval={0} angle={-12} textAnchor="end" height={70} />
            <YAxis tickFormatter={formatINRChart} tick={{ fontSize: 11, fill: "#5c6b7f" }} axisLine={false} tickLine={false} width={64} />
            <Tooltip
              formatter={(v: number) => [formatINR(v), ""]}
              contentStyle={{ borderRadius: 4, border: "1px solid #d8dfe8", fontFamily: "IBM Plex Sans" }}
            />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 16 }} />
            <Bar dataKey="net_cash_flow" name="Annual Net Cashflow" radius={[2, 2, 0, 0]}>
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Bar>
            <Bar dataKey="avg_monthly" fill="#b8c4d4" name="Avg Monthly Cashflow" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
