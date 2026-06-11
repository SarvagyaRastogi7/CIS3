import { PromptResultView } from "./PromptResultView";

const SUGGESTED_PROMPTS = [
  "How can I increase my cashflow?",
  "Provide a five-month cashflow projection based on historical trends.",
  "Forecast cashflow from Jan 2026 to Jun 2027 using ARIMA models.",
  "Run stress scenarios with delayed receivables and increased supplier payouts.",
];

interface Props {
  onSubmit: (prompt: string) => Promise<void>;
  loading: boolean;
  result: Record<string, unknown> | null;
}

export function PromptPanel({ onSubmit, loading, result }: Props) {
  return (
    <section className="card">
      <div className="card-header">
        <div>
          <h2>Advisory Query Interface</h2>
          <p className="card-subtitle">
            Submit treasury queries in natural language — routed to forecast, scenario, risk engines, or AI advisory
          </p>
        </div>
      </div>
      <div className="prompt-chips">
        {SUGGESTED_PROMPTS.map((p) => (
          <button key={p} className="chip" disabled={loading} onClick={() => void onSubmit(p)}>
            {p.length > 60 ? `${p.slice(0, 60)}…` : p}
          </button>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          const prompt = String(fd.get("prompt") ?? "").trim();
          if (prompt) void onSubmit(prompt);
        }}
      >
        <textarea name="prompt" rows={3} placeholder="Enter your treasury or cashflow query…" disabled={loading} />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Processing…" : "Submit Query"}
        </button>
      </form>
      {result && <PromptResultView result={result} />}
    </section>
  );
}
