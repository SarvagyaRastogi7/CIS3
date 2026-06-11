import type { InsightsResponse } from "../types";
import { formatSummaryValue } from "../utils/currency";
import { formatLabelKey } from "../utils/labels";
import { InsightCards } from "./InsightCards";
import { LlmNarrative } from "./LlmNarrative";

interface Props {
  insights: InsightsResponse | null;
}

export function InsightsPanel({ insights }: Props) {
  if (!insights) return null;

  const aiInsights = insights.llm_insights ?? [];
  const llmAttempted = insights.llm_available !== undefined || !!insights.llm_error;

  return (
    <section className="card">
      <div className="card-header">
        <div>
          <h2>Liquidity Risk Assessment</h2>
          <p className="card-subtitle">AI-assisted insights generated from your treasury data</p>
        </div>
      </div>
      <LlmNarrative
        narrative={insights.llm_narrative}
        model={insights.llm_model}
        error={insights.llm_error}
        attempted={llmAttempted}
        title="Liquidity Risk Narrative"
      />
      <div className="insights-layout">
        <div className="insights-summary-panel">
          <h3>Historical Summary</h3>
          <ul className="insights-stats">
            {Object.entries(insights.historical_summary).map(([k, v]) => (
              <li key={k}>
                <span>{formatLabelKey(k)}</span>
                <strong>{formatSummaryValue(k, v)}</strong>
              </li>
            ))}
          </ul>
        </div>
        <div className="insights-unified">
          <h3>AI Insights ({aiInsights.length})</h3>
          {aiInsights.length === 0 ? (
            <p className="insights-empty">
              {insights.llm_available === false
                ? "AI insights are unavailable. Set OPENAI_API_KEY and enable LLM_ENABLED to generate cards."
                : "No AI insights were returned. Try refreshing or re-running analysis."}
            </p>
          ) : (
            <InsightCards items={aiInsights} variant="dashboard" />
          )}
        </div>
      </div>
    </section>
  );
}
