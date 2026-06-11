import { formatINR, formatMetricValue } from "../utils/currency";
import { formatLabelKey } from "../utils/labels";

interface Lever {
  category: string;
  title: string;
  description: string;
  impact: string;
}

export interface Advisory {
  executive_summary: string;
  formula: string;
  current_position: Record<string, string | number>;
  levers: Lever[];
  priority_actions: string[];
  scenario_context: {
    annual_base_cashflow: number;
    impact_if_receivables_delayed: number;
    message: string;
  };
}

interface Props {
  advisory: Advisory;
}

export function CashflowAdvisoryView({ advisory }: Props) {
  return (
    <div className="advisory-writeup">
      <section className="advisory-section">
        <h3>Executive Summary</h3>
        <p className="advisory-prose">{advisory.executive_summary}</p>
      </section>

      <section className="advisory-section advisory-formula">
        <h3>Cashflow Formula</h3>
        <p>{advisory.formula}</p>
      </section>

      <section className="advisory-section">
        <h3>Current Position</h3>
        <div className="advisory-position-grid">
          {Object.entries(advisory.current_position).map(([key, value]) => (
            <div key={key} className="advisory-position-item">
              <span>{formatLabelKey(key)}</span>
              <strong>{formatMetricValue(key, value)}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="advisory-section">
        <h3>Recommended Levers to Increase Cashflow</h3>
        <div className="advisory-levers">
          {advisory.levers.map((lever) => (
            <article key={lever.title} className="advisory-lever-card">
              <div className="advisory-lever-header">
                <span className="advisory-lever-cat">{lever.category}</span>
                <span className={`impact impact-${lever.impact}`}>{lever.impact} impact</span>
              </div>
              <h4>{lever.title}</h4>
              <p>{lever.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="advisory-section">
        <h3>Priority Action Checklist</h3>
        <ol className="advisory-checklist">
          {advisory.priority_actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ol>
      </section>

      <section className="advisory-section advisory-risk">
        <h3>Scenario Context</h3>
        <p>{advisory.scenario_context.message}</p>
        <div className="advisory-position-grid">
          <div className="advisory-position-item">
            <span>annual base cashflow</span>
            <strong>{formatINR(advisory.scenario_context.annual_base_cashflow)}</strong>
          </div>
          <div className="advisory-position-item">
            <span>receivables delay risk</span>
            <strong>{formatINR(advisory.scenario_context.impact_if_receivables_delayed)}</strong>
          </div>
        </div>
      </section>
    </div>
  );
}
