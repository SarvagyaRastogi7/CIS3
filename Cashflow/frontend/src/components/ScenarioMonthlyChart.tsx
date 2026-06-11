import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ScenarioForecast } from "../types";
import { SCENARIO_COLORS } from "../utils/chartTheme";
import { formatINR, formatINRChart } from "../utils/currency";
import { formatForecastMonth } from "../utils/forecastFormat";

const COLORS = [SCENARIO_COLORS[0], SCENARIO_COLORS[3]];

interface Props {
  scenarios: ScenarioForecast[];
}

export function ScenarioMonthlyChart({ scenarios }: Props) {
  if (scenarios.length < 2) return null;

  const base = scenarios.find((s) => s.scenario === "base") ?? scenarios[0];
  const stress = scenarios.find((s) => s.scenario !== "base") ?? scenarios[1];

  const chartData = base.forecast.map((row, i) => ({
    month: formatForecastMonth(row.month, "2-digit"),
    base: row.cash_flow,
    stress: stress.forecast[i]?.cash_flow ?? 0,
  }));

  return (
    <section className="card card-chart">
      <div className="card-header">
        <div>
          <h2>Monthly Cashflow Comparison</h2>
          <p className="card-subtitle">Base ARIMA forecast vs your custom stress scenario</p>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="4 4" stroke="#d8dfe8" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 10, fill: "#5c6b7f" }}
              axisLine={{ stroke: "#d8dfe8" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={formatINRChart}
              tick={{ fontSize: 11, fill: "#5c6b7f" }}
              axisLine={false}
              tickLine={false}
              width={64}
            />
            <Tooltip
              formatter={(v: number, name: string) => [formatINR(v), name]}
              contentStyle={{ borderRadius: 4, border: "1px solid #d8dfe8", fontFamily: "IBM Plex Sans" }}
            />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            <Line
              type="monotone"
              dataKey="base"
              name={base.label}
              stroke={COLORS[0]}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="stress"
              name={stress.label}
              stroke={COLORS[1]}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
