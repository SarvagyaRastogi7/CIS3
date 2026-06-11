import type { FC } from "react";
import { IconAssistant, IconForecast, IconInsights, IconOverview, IconScenarios } from "./NavIcons";

export type DashboardSection = "overview" | "forecast" | "scenarios" | "insights" | "prompts";

const NAV: Array<{ id: DashboardSection; label: string; Icon: FC<{ className?: string }> }> = [
  { id: "overview", label: "Executive Summary", Icon: IconOverview },
  { id: "forecast", label: "Cashflow Forecast", Icon: IconForecast },
  { id: "scenarios", label: "Stress Scenarios", Icon: IconScenarios },
  { id: "insights", label: "Risk Insights", Icon: IconInsights },
  { id: "prompts", label: "Advisory Assistant", Icon: IconAssistant },
];

interface Props {
  active: DashboardSection;
  onChange: (section: DashboardSection) => void;
  hasData: boolean;
  recordCount: number;
}

export function Sidebar({ active, onChange, hasData, recordCount }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div>
          <h1>Cashflow Forecasting</h1>
        </div>
      </div>

      <div className="sidebar-divider" />

      <nav className="sidebar-nav" aria-label="Primary navigation">
        <span className="nav-section-label">Analytics</span>
        {NAV.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-item ${active === item.id ? "active" : ""}`}
            onClick={() => onChange(item.id)}
            disabled={!hasData && item.id !== "overview"}
          >
            <item.Icon className="nav-icon" />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className={`status-panel ${hasData ? "active" : ""}`}>
          <div className="status-row">
            <span className="status-dot" />
            <span className="status-label">{hasData ? "Dataset loaded" : "No dataset"}</span>
          </div>
          {hasData && (
            <span className="status-detail">{recordCount} months validated</span>
          )}
        </div>
        <p className="sidebar-compliance">SOC 2 aligned processing · Read-only analytics</p>
      </div>
    </aside>
  );
}
