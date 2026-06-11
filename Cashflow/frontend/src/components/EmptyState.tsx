interface Props {
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
}

export function EmptyState({ onUpload, loading }: Props) {
  return (
    <div className="empty-state">
      <div className="empty-layout">
        <header className="empty-header">
          <p className="empty-eyebrow">Treasury &amp; Corporate Finance</p>
          <h2>Cashflow Intelligence Platform</h2>
          <p className="empty-lead">
            Upload institutional monthly cashflow data to generate ARIMA-based forecasts,
            regulatory-grade scenario analysis, and treasury risk insights.
          </p>
        </header>

        <div className="empty-card">
          <div className="empty-card-header">
            <h3>Data Onboarding</h3>
          </div>
          <ul className="empty-checklist">
            <li>Minimum 12 consecutive months of history</li>
            <li>Microsoft Excel format (.xlsx)</li>
            <li>Standard columns: sales, collections, expenses</li>
          </ul>
          <label className={`empty-upload-btn ${loading ? "loading" : ""}`}>
            <input
              type="file"
              accept=".xlsx,.xls"
              disabled={loading}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void onUpload(file);
              }}
            />
            {loading ? "Validating dataset…" : "Select institutional data file"}
          </label>
        </div>

        <div className="empty-trust">
          <div className="trust-item">
            <strong>Validated ingestion</strong>
            <span>Automated schema and quality checks</span>
          </div>
          <div className="trust-item">
            <strong>ARIMA forecasting</strong>
            <span>Statistical models with AIC selection</span>
          </div>
          <div className="trust-item">
            <strong>Audit-ready export</strong>
            <span>Excel output for committee review</span>
          </div>
        </div>
      </div>
    </div>
  );
}
