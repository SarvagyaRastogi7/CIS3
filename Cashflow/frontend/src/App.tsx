import { useCallback, useRef, useState } from "react";
import { DataUpload } from "./components/DataUpload";
import { EmptyState } from "./components/EmptyState";
import { ForecastDurationSetup } from "./components/ForecastDurationSetup";
import { ForecastChart } from "./components/ForecastChart";
import { ForecastRangeControl } from "./components/ForecastRangeControl";
import { ForecastTable } from "./components/ForecastDataTable";
import { InsightsPanel } from "./components/InsightsPanel";
import { LlmNarrative } from "./components/LlmNarrative";
import { MetricCard } from "./components/MetricCard";
import { PromptPanel } from "./components/PromptPanel";
import { ScenarioChart } from "./components/ScenarioChart";
import { ScenarioComparisonTable } from "./components/ScenarioComparisonTable";
import { ScenarioMonthlyChart } from "./components/ScenarioMonthlyChart";
import { ScenarioStressControls } from "./components/ScenarioStressControls";
import { Sidebar, type DashboardSection } from "./components/Sidebar";
import {
  exportForecastUrl,
  exportScenariosUrl,
  getBaseForecast,
  getHistory,
  getInsights,
  getScenarios,
  uploadData,
  sendPrompt,
} from "./services/api";
import type { ForecastResponse, InsightsResponse, ScenarioResponse } from "./types";
import { DEFAULT_STRESS_PARAMS } from "./utils/scenarioStress";
import type { ScenarioStressParams } from "./types";
import { formatINR, formatINRCompact } from "./utils/currency";
import { SCENARIO_COLORS } from "./utils/chartTheme";
import {
  defaultRangeAfterLastMonth,
  formatForecastPeriod,
  formatRangeLabel,
  toForecastDate,
  validateForecastRange,
  type MonthYear,
} from "./utils/forecast";

const SECTION_TITLES: Record<DashboardSection, { title: string; subtitle: string }> = {
  overview: {
    title: "Executive Summary",
    subtitle: "ARIMA-based cashflow projection and key performance indicators",
  },
  forecast: {
    title: "Cashflow Forecast",
    subtitle: "Monthly revenue, expenditure, and net cashflow for your selected period",
  },
  scenarios: {
    title: "Stress Scenario Analysis",
    subtitle: "Tune stress assumptions and compare liquidity impact against the base forecast",
  },
  insights: {
    title: "Risk & Liquidity Insights",
    subtitle: "AI-assisted liquidity insights and risk narrative from your data",
  },
  prompts: {
    title: "Advisory Assistant",
    subtitle: "Natural-language queries powered by AI and your treasury data",
  },
};

export default function App() {
  const [section, setSection] = useState<DashboardSection>("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [recordCount, setRecordCount] = useState(0);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioResponse | null>(null);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [promptResult, setPromptResult] = useState<Record<string, unknown> | null>(null);
  const [hasData, setHasData] = useState(false);
  const [durationConfirmed, setDurationConfirmed] = useState(false);
  const [forecastStart, setForecastStart] = useState<MonthYear>({
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
  });
  const [forecastEnd, setForecastEnd] = useState<MonthYear>({
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear() + 1,
  });
  const [rangeMinYear, setRangeMinYear] = useState(new Date().getFullYear());
  const [stressParams, setStressParams] = useState<ScenarioStressParams>(DEFAULT_STRESS_PARAMS);
  const stressDebounceRef = useRef<ReturnType<typeof setTimeout>>();

  const forecastParams = {
    forecastStart: toForecastDate(forecastStart),
    forecastEnd: toForecastDate(forecastEnd),
  };

  const loadAnalytics = useCallback(async (params = forecastParams, stress = stressParams) => {
    const results = await Promise.allSettled([
      getBaseForecast(params),
      getScenarios(params, stress),
      getInsights(),
    ]);
    const errors: string[] = [];
    if (results[0].status === "fulfilled") setForecast(results[0].value);
    else errors.push(`Forecast: ${results[0].reason?.message ?? "failed"}`);
    if (results[1].status === "fulfilled") {
      setScenarios(results[1].value);
      if (results[1].value.stress_params) setStressParams(results[1].value.stress_params);
    } else errors.push(`Scenarios: ${results[1].reason?.message ?? "failed"}`);
    if (results[2].status === "fulfilled") setInsights(results[2].value);
    else errors.push(`Insights: ${results[2].reason?.message ?? "failed"}`);
    if (errors.length === 3) throw new Error(errors.join("; "));
    if (errors.length > 0) setError(errors.join("; "));
  }, [forecastParams.forecastStart, forecastParams.forecastEnd, stressParams]);

  const refreshScenarios = useCallback(
    async (stress: ScenarioStressParams, params = forecastParams) => {
      const scenariosRes = await getScenarios(params, stress);
      setScenarios(scenariosRes);
      if (scenariosRes.stress_params) setStressParams(scenariosRes.stress_params);
    },
    [forecastParams],
  );

  const handleStressParamsChange = (next: ScenarioStressParams) => {
    setStressParams(next);
    if (!hasData || !durationConfirmed) return;
    if (stressDebounceRef.current) clearTimeout(stressDebounceRef.current);
    stressDebounceRef.current = setTimeout(() => {
      setLoading(true);
      setError(null);
      void refreshScenarios(next)
        .catch((err) => setError(err instanceof Error ? err.message : "Scenario update failed"))
        .finally(() => setLoading(false));
    }, 400);
  };

  const handleUpload = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const report = await uploadData(file);
      const history = await getHistory();
      const lastMonth = history.records[history.records.length - 1]?.month;
      const range = lastMonth ? defaultRangeAfterLastMonth(lastMonth) : defaultRangeAfterLastMonth(new Date().toISOString());
      setForecastStart(range.start);
      setForecastEnd(range.end);
      setRangeMinYear(range.start.year);
      setFilename(history.filename);
      setRecordCount(report.record_count);
      setForecast(null);
      setScenarios(null);
      setInsights(null);
      setPromptResult(null);
      setDurationConfirmed(false);
      setHasData(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setHasData(false);
      setDurationConfirmed(false);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDuration = async () => {
    const validationError = validateForecastRange(forecastStart, forecastEnd);
    if (validationError) {
      setError(validationError);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await loadAnalytics({
        forecastStart: toForecastDate(forecastStart),
        forecastEnd: toForecastDate(forecastEnd),
      });
      setDurationConfirmed(true);
      setSection("overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handlePrompt = async (prompt: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await sendPrompt(prompt);
      setPromptResult(result);
      if (result.intent === "base_forecast" || result.intent === "trend") {
        await loadAnalytics();
      }
      if (result.intent === "scenarios") {
        setScenarios(result as unknown as ScenarioResponse);
      }
      if (result.intent === "insights") {
        setInsights((result.insights as InsightsResponse) ?? null);
      }
      if (result.intent === "cashflow_advisory") {
        setSection("prompts");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  };

  const page = SECTION_TITLES[section];
  const forecastPeriod = forecast ? formatForecastPeriod(forecast.forecast) : "";
  const rangeLabel = formatRangeLabel(forecastStart, forecastEnd);

  const handleRangeDraftChange = (start: MonthYear, end: MonthYear) => {
    setForecastStart(start);
    setForecastEnd(end);
    setError(validateForecastRange(start, end));
  };

  const handleRangeChange = async (start: MonthYear, end: MonthYear) => {
    setForecastStart(start);
    setForecastEnd(end);
    const validationError = validateForecastRange(start, end);
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!hasData || !durationConfirmed) return;
    setLoading(true);
    setError(null);
    try {
      const params = {
        forecastStart: toForecastDate(start),
        forecastEnd: toForecastDate(end),
      };
      const [forecastRes, scenariosRes] = await Promise.all([
        getBaseForecast(params),
        getScenarios(params, stressParams),
      ]);
      setForecast(forecastRes);
      setScenarios(scenariosRes);
      if (scenariosRes.stress_params) setStressParams(scenariosRes.stress_params);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update forecast period");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <Sidebar
        active={section}
        onChange={setSection}
        hasData={durationConfirmed}
        recordCount={recordCount}
      />

      <main className="dashboard-main">
        {!hasData ? (
          <EmptyState onUpload={handleUpload} loading={loading} />
        ) : !durationConfirmed ? (
          <ForecastDurationSetup
            filename={filename}
            recordCount={recordCount}
            start={forecastStart}
            end={forecastEnd}
            minYear={rangeMinYear}
            loading={loading}
            error={error}
            onRangeChange={handleRangeDraftChange}
            onConfirm={() => void handleConfirmDuration()}
          />
        ) : (
          <>
            <header className="topbar">
              <div className="topbar-title">
                <h2>{page.title}</h2>
                <p>{page.subtitle}</p>
              </div>
              <div className="topbar-actions">
                <DataUpload
                  onUpload={handleUpload}
                  loading={loading}
                  filename={filename}
                  recordCount={recordCount}
                />
                <ForecastRangeControl
                  start={forecastStart}
                  end={forecastEnd}
                  minYear={rangeMinYear}
                  maxYear={rangeMinYear + 10}
                  disabled={loading}
                  onChange={(start, end) => void handleRangeChange(start, end)}
                />
              </div>
            </header>

            {error && <div className="alert error">{error}</div>}
            {loading && <div className="loading-bar" />}

            {section === "overview" && forecast && (
              <div className="dashboard-content">
                <div className="metrics-row">
                  <MetricCard
                    label="Projected Revenue"
                    value={formatINRCompact(forecast.summary.total_sales)}
                    sub={`${rangeLabel} aggregate`}
                    variant="navy"
                    trend="up"
                  />
                  <MetricCard
                    label="Net Cashflow"
                    value={formatINRCompact(forecast.summary.net_cash_flow)}
                    sub={`${formatINR(forecast.summary.avg_monthly_cash_flow)} monthly avg`}
                    variant="forest"
                    trend="up"
                  />
                  <MetricCard
                    label="Minimum Monthly Position"
                    value={formatINR(forecast.summary.min_monthly_cash_flow)}
                    sub="Lowest projected period"
                    variant="gold"
                  />
                  <MetricCard
                    label="Data Integrity"
                    value={forecast.validation.valid ? "Validated" : "Review Required"}
                    sub={`${forecast.validation.record_count} periods analyzed`}
                    variant="slate"
                  />
                </div>
                <ForecastChart
                  data={forecast.forecast}
                  title={`Cashflow Trajectory (${forecastPeriod})`}
                  subtitle={`ARIMA-projected revenue, expenditure, and net cashflow · ${rangeLabel} · Net cashflow is cash inflows minus cash outflows, not revenue minus expenditure`}
                />
                <LlmNarrative
                  narrative={forecast.llm_narrative}
                  model={forecast.llm_model}
                  error={forecast.llm_error}
                  attempted={forecast.llm_available != null || !!forecast.llm_error}
                  title="Cashflow Trajectory Analysis"
                />
              </div>
            )}

            {section === "forecast" && forecast && (
              <div className="dashboard-content">
                <ForecastChart data={forecast.forecast} />
                <ForecastTable
                  data={forecast.forecast}
                  exportHref={exportForecastUrl(forecastParams)}
                />
              </div>
            )}

            {section === "scenarios" && scenarios && (
              <div className="dashboard-content">
                <div className="scenario-layout">
                  <aside className="scenario-layout-side">
                    <ScenarioStressControls
                      params={stressParams}
                      disabled={loading}
                      onChange={handleStressParamsChange}
                    />
                    <div className="scenario-cards scenario-cards-side">
                      {scenarios.scenarios.map((s, i) => (
                        <div
                          key={s.scenario}
                          className="scenario-summary-card"
                          style={{ borderTopColor: SCENARIO_COLORS[i] }}
                        >
                          <h4>{s.label}</h4>
                          <div className="scenario-metrics">
                            <div>
                              <span>Period Net Cashflow</span>
                              <strong>{formatINR(s.summary.net_cash_flow)}</strong>
                            </div>
                            <div>
                              <span>Monthly Average</span>
                              <strong>{formatINR(s.summary.avg_monthly_cash_flow)}</strong>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </aside>
                  <div className="scenario-layout-charts">
                    <ScenarioChart scenarios={scenarios.scenarios} />
                    <ScenarioMonthlyChart scenarios={scenarios.scenarios} />
                  </div>
                </div>
                <ScenarioComparisonTable
                  scenarios={scenarios.scenarios}
                  exportHref={exportScenariosUrl(forecastParams, stressParams)}
                />
              </div>
            )}

            {section === "insights" && (
              <div className="dashboard-content">
                <InsightsPanel insights={insights} />
              </div>
            )}

            {section === "prompts" && (
              <div className="dashboard-content">
                <PromptPanel onSubmit={handlePrompt} loading={loading} result={promptResult} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
