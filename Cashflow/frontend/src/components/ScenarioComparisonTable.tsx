import type { ScenarioForecast } from "../types";
import { ForecastDataTable } from "./ForecastDataTable";

interface Props {
  scenarios: ScenarioForecast[];
  exportHref?: string;
}

export function ScenarioComparisonTable({ scenarios, exportHref }: Props) {
  const baseScenario = scenarios.find((s) => s.scenario === "base");
  const stressScenario =
    scenarios.find((s) => s.scenario !== "base") ?? scenarios[scenarios.length - 1];
  if (!stressScenario?.forecast.length) return null;

  return (
    <section className="card table-card">
      <div className="card-header">
        <div>
          <h2>Stress Scenario Schedule</h2>
          <p className="card-subtitle">
            {stressScenario.label} — line-item schedule with base cash flow in the last column for
            comparison
          </p>
        </div>
      </div>
      <div className="table-scroll table-scroll-pinned">
        <ForecastDataTable
          data={stressScenario.forecast}
          density="full"
          baseCashFlowCompare={baseScenario?.forecast}
        />
      </div>
      {exportHref && (
        <div className="section-export-actions">
          <a className="btn btn-primary" href={exportHref}>
            Export Scenarios
          </a>
        </div>
      )}
    </section>
  );
}
