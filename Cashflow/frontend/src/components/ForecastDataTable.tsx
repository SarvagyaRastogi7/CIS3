import type { ForecastMonth } from "../types";
import { formatINR, formatMetricValue } from "../utils/currency";
import { FORECAST_COMPACT_COLUMNS, FORECAST_DETAIL_COLUMNS } from "../utils/forecastColumns";
import { formatForecastMonth, formatModelMomChangePct, modelMomChangeClass } from "../utils/forecastFormat";

type ColumnKey = keyof ForecastMonth;

interface TableProps {
  data: ForecastMonth[];
  density?: "full" | "compact";
  tableClassName?: string;
  /** When set, appends a base-forecast cash flow column for month-by-month comparison. */
  baseCashFlowCompare?: ForecastMonth[];
}

function formatCell(key: ColumnKey, row: ForecastMonth): string {
  if (key === "month") return formatForecastMonth(row.month);
  if (key === "model_mom_change_pct") return formatModelMomChangePct(row.model_mom_change_pct);
  return formatMetricValue(key, row[key]);
}

export function ForecastDataTable({
  data,
  density = "full",
  tableClassName = "forecast-detail-table",
  baseCashFlowCompare,
}: TableProps) {
  const columns = density === "full" ? FORECAST_DETAIL_COLUMNS : FORECAST_COMPACT_COLUMNS;
  const baseCashFlowByMonth = new Map(
    baseCashFlowCompare?.map((row) => [row.month, row.cash_flow]) ?? [],
  );

  return (
    <table className={tableClassName}>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.key}>{c.label}</th>
          ))}
          {baseCashFlowCompare && <th>Base Cash Flow</th>}
        </tr>
      </thead>
      <tbody>
        {data.map((row) => (
          <tr key={row.month}>
            {columns.map((c) => {
              const isMom = c.key === "model_mom_change_pct";
              const isMonth = c.key === "month";
              const useFormattedCell = isMonth || isMom || density === "compact";
              return (
                <td
                  key={c.key}
                  className={
                    isMom
                      ? `pct-cell ${modelMomChangeClass(row.model_mom_change_pct) ?? ""}`
                      : c.key === "cash_flow"
                        ? "cf-cell"
                        : undefined
                  }
                >
                  {useFormattedCell ? formatCell(c.key, row) : formatINR(Number(row[c.key]))}
                </td>
              );
            })}
            {baseCashFlowCompare && (
              <td className="cf-cell cf-cell-base">
                {formatINR(baseCashFlowByMonth.get(row.month) ?? 0)}
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface ForecastTableProps {
  data: ForecastMonth[];
  exportHref?: string;
}

export function ForecastTable({ data, exportHref }: ForecastTableProps) {
  return (
    <section className="card table-card">
      <div className="card-header">
        <div>
          <h2>Period Detail Schedule</h2>
          <p className="card-subtitle">
            Line-item cashflow projection by reporting period · MoM Change is the ARIMA model&apos;s
            month-over-month % change in net cashflow
          </p>
        </div>
      </div>
      <div className="table-scroll table-scroll-pinned">
        <ForecastDataTable data={data} density="full" />
      </div>
      {exportHref && (
        <div className="section-export-actions">
          <a className="btn btn-primary" href={exportHref}>
            Export Forecast
          </a>
        </div>
      )}
    </section>
  );
}
