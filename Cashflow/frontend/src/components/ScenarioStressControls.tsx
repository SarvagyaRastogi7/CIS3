import type { ScenarioStressParams } from "../types";
import { DEFAULT_STRESS_PARAMS, STRESS_PRESETS } from "../utils/scenarioStress";

interface Props {
  params: ScenarioStressParams;
  disabled?: boolean;
  onChange: (params: ScenarioStressParams) => void;
}

export function ScenarioStressControls({ params, disabled, onChange }: Props) {
  const patch = (partial: Partial<ScenarioStressParams>) => onChange({ ...params, ...partial });

  return (
    <section className="card scenario-controls-card">
      <div className="card-header">
        <div>
          <h2>Stress Assumptions</h2>
          <p className="card-subtitle">
            Adjust parameters to model adverse conditions on the ARIMA base forecast
          </p>
        </div>
      </div>

      <div className="scenario-presets">
        {Object.entries(STRESS_PRESETS).map(([key, preset]) => (
          <button
            key={key}
            type="button"
            className="btn btn-outline btn-sm"
            disabled={disabled}
            onClick={() => onChange({ ...preset.params })}
          >
            {preset.label}
          </button>
        ))}
        <button
          type="button"
          className="btn btn-outline btn-sm"
          disabled={disabled}
          onClick={() => onChange({ ...DEFAULT_STRESS_PARAMS })}
        >
          Reset
        </button>
      </div>

      <div className="scenario-controls-grid">
        <label className="scenario-toggle">
          <input
            type="checkbox"
            checked={params.stress_receivables}
            disabled={disabled}
            onChange={(e) => patch({ stress_receivables: e.target.checked })}
          />
          <span>Delayed / reduced collections</span>
        </label>

        <label className={`scenario-field ${params.stress_receivables ? "" : "disabled"}`}>
          <span>Collection delay (months)</span>
          <input
            type="range"
            min={0}
            max={6}
            step={1}
            value={params.receivables_delay_months}
            disabled={disabled || !params.stress_receivables}
            onChange={(e) => patch({ receivables_delay_months: Number(e.target.value) })}
          />
          <strong>{params.receivables_delay_months}</strong>
        </label>

        <label className={`scenario-field ${params.stress_receivables ? "" : "disabled"}`}>
          <span>Collections vs credit sales (%)</span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={Math.round(params.receivables_collection_factor * 100)}
            disabled={disabled || !params.stress_receivables}
            onChange={(e) =>
              patch({ receivables_collection_factor: Number(e.target.value) / 100 })
            }
          />
          <strong>{Math.round(params.receivables_collection_factor * 100)}%</strong>
        </label>

        <label className="scenario-toggle">
          <input
            type="checkbox"
            checked={params.stress_supplier_payout}
            disabled={disabled}
            onChange={(e) => patch({ stress_supplier_payout: e.target.checked })}
          />
          <span>Higher supplier payout</span>
        </label>

        <label className={`scenario-field ${params.stress_supplier_payout ? "" : "disabled"}`}>
          <span>Supplier payout increase (%)</span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={Math.round(params.supplier_payout_increase_pct * 100)}
            disabled={disabled || !params.stress_supplier_payout}
            onChange={(e) =>
              patch({ supplier_payout_increase_pct: Number(e.target.value) / 100 })
            }
          />
          <strong>+{Math.round(params.supplier_payout_increase_pct * 100)}%</strong>
        </label>

        <label className="scenario-toggle">
          <input
            type="checkbox"
            checked={params.stress_expenses}
            disabled={disabled}
            onChange={(e) => patch({ stress_expenses: e.target.checked })}
          />
          <span>Additional operating expenses</span>
        </label>

        <label className={`scenario-field ${params.stress_expenses ? "" : "disabled"}`}>
          <span>Expense increase (%)</span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={Math.round(params.expense_increase_pct * 100)}
            disabled={disabled || !params.stress_expenses}
            onChange={(e) => patch({ expense_increase_pct: Number(e.target.value) / 100 })}
          />
          <strong>+{Math.round(params.expense_increase_pct * 100)}%</strong>
        </label>
      </div>
    </section>
  );
}
