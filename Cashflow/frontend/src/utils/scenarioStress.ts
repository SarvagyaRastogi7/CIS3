import type { ScenarioStressParams } from "../types";

export const DEFAULT_STRESS_PARAMS: ScenarioStressParams = {
  stress_receivables: true,
  receivables_delay_months: 2,
  receivables_collection_factor: 0.7,
  stress_supplier_payout: true,
  supplier_payout_increase_pct: 0.2,
  stress_expenses: false,
  expense_increase_pct: 0.2,
};

export const STRESS_PRESETS: Record<string, { label: string; params: ScenarioStressParams }> = {
  balanced: {
    label: "Balanced",
    params: { ...DEFAULT_STRESS_PARAMS },
  },
  delayedReceivables: {
    label: "Delayed collections",
    params: {
      ...DEFAULT_STRESS_PARAMS,
      stress_receivables: true,
      stress_supplier_payout: false,
      stress_expenses: false,
    },
  },
  supplierPayout: {
    label: "Higher supplier payout",
    params: {
      ...DEFAULT_STRESS_PARAMS,
      stress_receivables: false,
      stress_supplier_payout: true,
      stress_expenses: false,
    },
  },
  combined: {
    label: "Combined stress",
    params: {
      ...DEFAULT_STRESS_PARAMS,
      stress_receivables: true,
      stress_supplier_payout: true,
      stress_expenses: true,
    },
  },
};
