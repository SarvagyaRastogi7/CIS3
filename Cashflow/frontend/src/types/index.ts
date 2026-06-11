export interface MonthlyRecord {
  month: string;
  total_sales: number;
  total_credit_sales: number;
  total_cash_sales: number;
  collections: number;
  total_expenses: number;
  total_cash_expenses: number;
  total_credit_expenses: number;
  cash_paid_credit_expenses: number;
  cash_flow?: number;
}

export interface ForecastMonth extends MonthlyRecord {
  cash_flow: number;
  model_mom_change_pct?: number | null;
}

export interface ForecastResponse {
  assumptions: Record<string, unknown>;
  derived_ratios: Record<string, number>;
  validation: { valid: boolean; issues: ValidationIssue[]; record_count: number };
  forecast: ForecastMonth[];
  summary: Record<string, number>;
  model_metadata?: Record<string, unknown>;
  llm_narrative?: string | null;
  llm_model?: string | null;
  llm_available?: boolean;
  llm_error?: string | null;
}

export interface ValidationIssue {
  severity: string;
  field: string;
  message: string;
}

export interface ScenarioForecast {
  scenario: string;
  label: string;
  forecast: ForecastMonth[];
  summary: Record<string, number>;
}

export interface ScenarioStressParams {
  stress_receivables: boolean;
  receivables_delay_months: number;
  receivables_collection_factor: number;
  stress_supplier_payout: boolean;
  supplier_payout_increase_pct: number;
  stress_expenses: boolean;
  expense_increase_pct: number;
}

export interface ScenarioResponse {
  base_assumptions: Record<string, unknown>;
  stress_params: ScenarioStressParams;
  scenarios: ScenarioForecast[];
}

export interface InsightItem {
  category: string;
  title: string;
  description: string;
  impact: string;
  source?: string;
}

export interface InsightsResponse {
  seasonal_patterns: Array<Record<string, number | string>>;
  llm_insights: InsightItem[];
  historical_summary: Record<string, number | string>;
  llm_narrative?: string | null;
  llm_model?: string | null;
  llm_available?: boolean;
  llm_error?: string | null;
}

export interface HistoryResponse {
  filename: string | null;
  record_count: number;
  records: MonthlyRecord[];
}
