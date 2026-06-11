import { useState } from "react";
import type { ForecastMonth, InsightItem } from "../types";
import { displayEntries, formatMetricValue } from "../utils/currency";
import { formatLabelKey } from "../utils/labels";
import { CashflowAdvisoryView, type Advisory } from "./CashflowAdvisoryView";
import { ForecastDataTable } from "./ForecastDataTable";
import { InsightCards } from "./InsightCards";
import { LlmNarrative } from "./LlmNarrative";

function SummaryGrid({ data }: { data: Record<string, unknown> }) {
  const entries = displayEntries(data);
  if (!entries.length) return null;
  return (
    <div className="prompt-summary-grid">
      {entries.map(([key, value]) => (
        <div key={key} className="prompt-summary-item">
          <span className="prompt-summary-key">{formatLabelKey(key)}</span>
          <span className="prompt-summary-val">{formatMetricValue(key, value)}</span>
        </div>
      ))}
    </div>
  );
}

function KeyValueBlock({ title, data }: { title: string; data: Record<string, unknown> }) {
  const [open, setOpen] = useState(true);
  const entries = displayEntries(data);
  if (!entries.length) return null;
  return (
    <div className="prompt-block">
      <button type="button" className="prompt-block-header" onClick={() => setOpen(!open)}>
        <span>{title}</span>
        <span className="prompt-chevron">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <div className="prompt-kv-grid">
          {entries.map(([key, value]) => (
            <div key={key} className="prompt-kv-row">
              <span className="prompt-kv-key">{formatLabelKey(key)}</span>
              <span className="prompt-kv-val">{formatMetricValue(key, value)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const INTENT_LABELS: Record<string, string> = {
  base_forecast: "Base Forecast",
  trend: "Trend Forecast",
  scenarios: "Scenario Analysis",
  insights: "Insights & Recommendations",
  cashflow_advisory: "Cashflow Improvement Advisory",
  llm_chat: "Treasury Advisory",
};

interface Props {
  result: Record<string, unknown>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asForecastRows(value: unknown): ForecastMonth[] {
  return Array.isArray(value) ? (value as ForecastMonth[]) : [];
}

function asInsightItems(value: unknown): InsightItem[] {
  return Array.isArray(value) ? (value as InsightItem[]) : [];
}

export function PromptResultView({ result }: Props) {
  const [showRaw, setShowRaw] = useState(false);
  const intent = String(result.intent ?? "unknown");
  const intentLabel = INTENT_LABELS[intent] ?? intent;
  const prompt = typeof result.prompt === "string" ? result.prompt : null;
  const summary = isRecord(result.summary) ? result.summary : null;
  const assumptions = isRecord(result.assumptions) ? result.assumptions : null;
  const derivedRatios = isRecord(result.derived_ratios) ? result.derived_ratios : null;
  const forecast = asForecastRows(result.forecast);
  const scenarios = Array.isArray(result.scenarios) ? (result.scenarios as Array<Record<string, unknown>>) : [];
  const insights = isRecord(result.insights) ? result.insights : null;
  const historicalSummary = insights && isRecord(insights.historical_summary) ? insights.historical_summary : null;
  const aiInsights = insights ? asInsightItems(insights.llm_insights) : [];
  const validationWarnings = Array.isArray(result.validation_warnings)
    ? (result.validation_warnings as Array<Record<string, string>>)
    : [];
  const advisory = isRecord(result.advisory) ? (result.advisory as unknown as Advisory) : null;
  const llmNarrative = typeof result.llm_narrative === "string" ? result.llm_narrative : null;
  const llmModel = typeof result.llm_model === "string" ? result.llm_model : null;
  const llmAvailable = result.llm_available === true;
  const llmError = typeof result.llm_error === "string" ? result.llm_error : null;
  const insightsLlmNarrative =
    insights && typeof insights.llm_narrative === "string" ? insights.llm_narrative : null;

  return (
    <div className="prompt-result-view">
      <div className="prompt-result-header">
        <span className="prompt-intent-badge">{intentLabel}</span>
        {prompt && <p className="prompt-result-query">"{prompt}"</p>}
      </div>

      {summary && (
        <div className="prompt-section">
          <h3>Summary</h3>
          <SummaryGrid data={summary} />
        </div>
      )}

      {result.months_ahead !== undefined && (
        <p className="prompt-meta">Forecasting next <strong>{String(result.months_ahead)}</strong> months</p>
      )}

      {forecast.length > 0 && (
        <div className="prompt-section">
          <h3>Forecast</h3>
          <div className="prompt-table-scroll">
            <ForecastDataTable data={forecast} density="compact" tableClassName="prompt-table" />
          </div>
        </div>
      )}

      {assumptions && <KeyValueBlock title="Assumptions" data={assumptions} />}

      {derivedRatios && <KeyValueBlock title="Derived Ratios" data={derivedRatios} />}

      {scenarios.length > 0 && (
        <div className="prompt-section">
          <h3>Scenarios</h3>
          {scenarios.map((scenario) => {
            const scenarioSummary = isRecord(scenario.summary) ? scenario.summary : null;
            const scenarioForecast = asForecastRows(scenario.forecast);
            return (
              <div key={String(scenario.scenario)} className="prompt-scenario-card">
                <h4>{String(scenario.label)}</h4>
                {scenarioSummary && <SummaryGrid data={scenarioSummary} />}
                {scenarioForecast.length > 0 && (
                  <details className="prompt-details">
                    <summary>View monthly breakdown ({scenarioForecast.length} months)</summary>
                    <div className="prompt-table-scroll">
                      <ForecastDataTable
                        data={scenarioForecast}
                        density="compact"
                        tableClassName="prompt-table"
                      />
                    </div>
                  </details>
                )}
              </div>
            );
          })}
        </div>
      )}

      {intent === "llm_chat" && (
        <div className="prompt-section">
          <LlmNarrative
            narrative={llmNarrative}
            model={llmModel}
            error={llmError}
            attempted
          />
        </div>
      )}

      {advisory && (
        <div className="prompt-section advisory-section-wrap">
          <LlmNarrative
            narrative={llmNarrative}
            model={llmModel}
            error={llmError}
            attempted={llmAvailable || !!llmError || !!llmNarrative}
          />
          <CashflowAdvisoryView advisory={advisory} />
        </div>
      )}

      {insights && (
        <div className="prompt-section">
          <h3>Insights</h3>
          <LlmNarrative
            narrative={insightsLlmNarrative}
            model={typeof insights.llm_model === "string" ? insights.llm_model : null}
            error={typeof insights.llm_error === "string" ? insights.llm_error : null}
            attempted={insights.llm_available !== undefined || !!insights.llm_error}
            title="Liquidity Risk Narrative"
          />
          {historicalSummary && <KeyValueBlock title="Historical Summary" data={historicalSummary} />}
          <InsightCards items={aiInsights} variant="prompt" title="AI Insights" />
        </div>
      )}

      {validationWarnings.length > 0 && (
        <div className="prompt-section">
          <h3>Validation Warnings</h3>
          <ul className="prompt-warnings">
            {validationWarnings.map((w, i) => (
              <li key={i}>
                <strong>{w.field}</strong>: {w.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="prompt-raw-section">
        <button type="button" className="prompt-raw-toggle" onClick={() => setShowRaw(!showRaw)}>
          {showRaw ? "Hide" : "Show"} raw JSON
        </button>
        {showRaw && (
          <pre className="prompt-raw-json">{JSON.stringify(result, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}
