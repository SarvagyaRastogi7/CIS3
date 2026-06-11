import type { ForecastMonth } from "../types";

type ForecastColumnKey = keyof ForecastMonth;

export const FORECAST_DETAIL_COLUMNS: Array<{ key: ForecastColumnKey; label: string }> = [
  { key: "month", label: "Month" },
  { key: "model_mom_change_pct", label: "MoM Change" },
  { key: "total_sales", label: "Sales" },
  { key: "total_credit_sales", label: "Credit" },
  { key: "total_cash_sales", label: "Cash" },
  { key: "collections", label: "Collections" },
  { key: "total_expenses", label: "Expenses" },
  { key: "total_cash_expenses", label: "Cash Exp." },
  { key: "total_credit_expenses", label: "Credit Exp." },
  { key: "cash_paid_credit_expenses", label: "Paid" },
  { key: "cash_flow", label: "Cash Flow" },
];

export const FORECAST_COMPACT_COLUMNS: Array<{ key: ForecastColumnKey; label: string }> = [
  { key: "month", label: "Month" },
  { key: "model_mom_change_pct", label: "MoM Change" },
  { key: "total_sales", label: "Total Sales" },
  { key: "total_credit_sales", label: "Credit Sales" },
  { key: "total_cash_sales", label: "Cash Sales" },
  { key: "collections", label: "Collections" },
  { key: "total_expenses", label: "Expenses" },
  { key: "cash_flow", label: "Cash Flow" },
];
