import { MONTH_NAMES, type MonthYear } from "../utils/forecast";

interface Props {
  start: MonthYear;
  end: MonthYear;
  minYear?: number;
  maxYear?: number;
  onChange: (start: MonthYear, end: MonthYear) => void;
  disabled?: boolean;
}

function yearOptions(minYear: number, maxYear: number): number[] {
  return Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i);
}

export function ForecastRangeControl({
  start,
  end,
  minYear = new Date().getFullYear(),
  maxYear = new Date().getFullYear() + 10,
  onChange,
  disabled,
}: Props) {
  const years = yearOptions(minYear, maxYear);

  const updateStart = (patch: Partial<MonthYear>) => {
    const nextStart = { ...start, ...patch };
    onChange(nextStart, end);
  };

  const updateEnd = (patch: Partial<MonthYear>) => {
    const nextEnd = { ...end, ...patch };
    onChange(start, nextEnd);
  };

  return (
    <div className="forecast-range">
      <div className="forecast-range-group">
        <span className="forecast-range-label">From</span>
        <label className="forecast-horizon-field">
          <span>Month</span>
          <select
            value={start.month}
            disabled={disabled}
            onChange={(e) => updateStart({ month: Number(e.target.value) })}
          >
            {MONTH_NAMES.map((name, i) => (
              <option key={name} value={i + 1}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <label className="forecast-horizon-field">
          <span>Year</span>
          <select
            value={start.year}
            disabled={disabled}
            onChange={(e) => updateStart({ year: Number(e.target.value) })}
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="forecast-range-group">
        <span className="forecast-range-label">To</span>
        <label className="forecast-horizon-field">
          <span>Month</span>
          <select
            value={end.month}
            disabled={disabled}
            onChange={(e) => updateEnd({ month: Number(e.target.value) })}
          >
            {MONTH_NAMES.map((name, i) => (
              <option key={name} value={i + 1}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <label className="forecast-horizon-field">
          <span>Year</span>
          <select
            value={end.year}
            disabled={disabled}
            onChange={(e) => updateEnd({ year: Number(e.target.value) })}
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
