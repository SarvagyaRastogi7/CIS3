import type { ForecastMonth } from "../types";

export interface MonthYear {
  month: number;
  year: number;
}

export const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export function toForecastDate({ month, year }: MonthYear): string {
  return `${year}-${String(month).padStart(2, "0")}-01`;
}

export function defaultRangeAfterLastMonth(lastMonthIso: string, spanMonths = 12): {
  start: MonthYear;
  end: MonthYear;
} {
  const last = new Date(lastMonthIso);
  const start = new Date(last.getFullYear(), last.getMonth() + 1, 1);
  const end = new Date(start.getFullYear(), start.getMonth() + spanMonths - 1, 1);
  return {
    start: { month: start.getMonth() + 1, year: start.getFullYear() },
    end: { month: end.getMonth() + 1, year: end.getFullYear() },
  };
}

function formatMonthYear({ month, year }: MonthYear): string {
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

export function formatForecastPeriod(forecast: ForecastMonth[]): string {
  if (!forecast.length) return "";
  const start = new Date(forecast[0].month);
  const end = new Date(forecast[forecast.length - 1].month);
  const fmt = (d: Date) => d.toLocaleDateString("en-IN", { month: "short", year: "numeric" });
  return `${fmt(start)} – ${fmt(end)}`;
}

export function formatRangeLabel(start: MonthYear, end: MonthYear): string {
  return `${formatMonthYear(start)} – ${formatMonthYear(end)}`;
}

export function rangeMonthCount(start: MonthYear, end: MonthYear): number {
  return (end.year - start.year) * 12 + (end.month - start.month) + 1;
}

export function validateForecastRange(start: MonthYear, end: MonthYear): string | null {
  const count = rangeMonthCount(start, end);
  if (count < 1) return "End month must be on or after start month.";
  if (count > 24) return "Forecast range cannot exceed 24 months.";
  return null;
}
