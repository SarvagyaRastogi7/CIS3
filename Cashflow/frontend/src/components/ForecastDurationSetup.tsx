import { ForecastRangeControl } from "./ForecastRangeControl";
import { formatRangeLabel, rangeMonthCount, validateForecastRange, type MonthYear } from "../utils/forecast";

interface Props {
  filename: string | null;
  recordCount: number;
  start: MonthYear;
  end: MonthYear;
  minYear: number;
  loading: boolean;
  error: string | null;
  onRangeChange: (start: MonthYear, end: MonthYear) => void;
  onConfirm: () => void;
}

export function ForecastDurationSetup({
  filename,
  recordCount,
  start,
  end,
  minYear,
  loading,
  error,
  onRangeChange,
  onConfirm,
}: Props) {
  const monthCount = rangeMonthCount(start, end);
  const rangeError = validateForecastRange(start, end);
  const rangeValid = !rangeError;

  return (
    <div className="duration-setup">
      <div className="duration-setup-card">
        <header className="duration-setup-header">
          <h2>Select Forecast Period</h2>
          <p className="duration-setup-lead">
            Your data is loaded. Choose the start and end month for the cashflow projection before
            analysis begins.
          </p>
        </header>

        <div className="duration-setup-meta">
          <div>
            <span>File</span>
            <strong>{filename ?? "—"}</strong>
          </div>
          <div>
            <span>Historical periods</span>
            <strong>{recordCount}</strong>
          </div>
        </div>

        <div className="duration-setup-range">
          <ForecastRangeControl
            start={start}
            end={end}
            minYear={minYear}
            maxYear={minYear + 10}
            disabled={loading}
            onChange={onRangeChange}
          />
          <p className={`duration-setup-summary ${rangeValid ? "" : "invalid"}`}>
            {rangeValid
              ? `${formatRangeLabel(start, end)} · ${monthCount} month${monthCount === 1 ? "" : "s"}`
              : rangeError}
          </p>
        </div>

        {error && <div className="alert error duration-setup-error">{error}</div>}

        <button
          type="button"
          className="btn btn-primary duration-setup-btn"
          disabled={loading || !rangeValid}
          onClick={onConfirm}
        >
          {loading ? "Running analysis…" : "Generate Forecast & Analysis"}
        </button>
      </div>
    </div>
  );
}
