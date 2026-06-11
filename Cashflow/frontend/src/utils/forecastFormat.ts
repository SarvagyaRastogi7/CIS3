export function formatForecastMonth(iso: string, year: "numeric" | "2-digit" = "numeric"): string {
  return new Date(iso).toLocaleDateString("en-IN", { month: "short", year });
}

export function formatModelMomChangePct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function modelMomChangeClass(value: number | null | undefined): string | undefined {
  if (value == null || Number.isNaN(value)) return undefined;
  if (value > 0) return "pct-up";
  if (value < 0) return "pct-down";
  return "pct-flat";
}
