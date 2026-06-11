const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, options);
  } catch {
    throw new Error(
      "Cannot reach the API server. Start the backend with ./scripts/dev.sh or uvicorn (default port 8000).",
    );
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function uploadData(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{ valid: boolean; record_count: number }>("/data/upload", {
    method: "POST",
    body: form,
  });
}

export async function getHistory() {
  return request<import("../types").HistoryResponse>("/data/history");
}

interface ForecastParams {
  forecastStart?: string;
  forecastEnd?: string;
}

export async function getBaseForecast(params: ForecastParams = {}) {
  const { forecastStart, forecastEnd } = params;
  return request<import("../types").ForecastResponse>("/forecast/base", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      forecast_start: forecastStart,
      forecast_end: forecastEnd,
    }),
  });
}

export async function getScenarios(
  params: ForecastParams = {},
  stressParams?: import("../types").ScenarioStressParams,
) {
  const { forecastStart, forecastEnd } = params;
  const body: Record<string, unknown> = {
    assumptions: {
      forecast_start: forecastStart,
      forecast_end: forecastEnd,
    },
  };
  if (stressParams) {
    body.stress_params = stressParams;
  }
  return request<import("../types").ScenarioResponse>("/forecast/scenarios", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getInsights() {
  return request<import("../types").InsightsResponse>("/insights");
}

export async function sendPrompt(prompt: string) {
  return request<Record<string, unknown>>("/prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
}

export function exportForecastUrl(params: ForecastParams = {}) {
  const { forecastStart, forecastEnd } = params;
  if (!forecastStart || !forecastEnd) return `${API_BASE}/export/forecast`;
  const query = new URLSearchParams({ forecast_start: forecastStart, forecast_end: forecastEnd });
  return `${API_BASE}/export/forecast?${query}`;
}

export function exportScenariosUrl(
  params: ForecastParams = {},
  stressParams?: import("../types").ScenarioStressParams,
) {
  const query = new URLSearchParams();
  const { forecastStart, forecastEnd } = params;
  if (forecastStart) query.set("forecast_start", forecastStart);
  if (forecastEnd) query.set("forecast_end", forecastEnd);
  if (stressParams) {
    query.set("stress_receivables", String(stressParams.stress_receivables));
    query.set("receivables_delay_months", String(stressParams.receivables_delay_months));
    query.set("receivables_collection_factor", String(stressParams.receivables_collection_factor));
    query.set("stress_supplier_payout", String(stressParams.stress_supplier_payout));
    query.set("supplier_payout_increase_pct", String(stressParams.supplier_payout_increase_pct));
    query.set("stress_expenses", String(stressParams.stress_expenses));
    query.set("expense_increase_pct", String(stressParams.expense_increase_pct));
  }
  const qs = query.toString();
  return qs ? `${API_BASE}/export/scenarios?${qs}` : `${API_BASE}/export/scenarios`;
}
