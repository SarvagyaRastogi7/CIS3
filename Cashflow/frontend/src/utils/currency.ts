const inrCompactFormatter = new Intl.NumberFormat("en-IN", {
  notation: "compact",
  maximumFractionDigits: 2,
});

export function formatINR(value: number, maximumFractionDigits = 0): string {
  return `₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits }).format(value)}`;
}

export function formatINRCompact(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1e7) return `₹${(value / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `₹${(value / 1e5).toFixed(2)} L`;
  return formatINR(value);
}

export function formatINRChart(value: number): string {
  return inrCompactFormatter.format(value);
}

const INR_SUMMARY_KEYS = new Set(["avg_monthly_sales", "avg_monthly_cash_flow"]);

function isRatioKey(key: string): boolean {
  const lowered = key.toLowerCase();
  return lowered.includes("ratio") || lowered.includes("percent") || lowered.includes("rate");
}

function isDaysKey(key: string): boolean {
  const lowered = key.toLowerCase();
  return lowered.includes("days") || lowered.includes("lag");
}

function isCountKey(key: string): boolean {
  const lowered = key.toLowerCase();
  return (
    lowered.includes("months") ||
    lowered.includes("window") ||
    lowered.includes("count") ||
    lowered.endsWith("_num")
  );
}

function hasDisplayValue(value: unknown): boolean {
  return value !== null && value !== undefined && value !== "";
}

export function displayEntries(data: Record<string, unknown>): Array<[string, unknown]> {
  return Object.entries(data).filter(([, value]) => hasDisplayValue(value));
}

export function formatSummaryValue(key: string, value: string | number): string {
  if (typeof value === "number" && INR_SUMMARY_KEYS.has(key)) return formatINR(value);
  if (typeof value === "number") return value.toLocaleString("en-IN");
  return String(value);
}

export function formatMetricValue(key: string, value: unknown): string {
  if (!hasDisplayValue(value)) return "—";
  if (typeof value === "number") {
    if (isRatioKey(key)) return `${(value * 100).toFixed(1)}%`;
    if (isDaysKey(key)) return `${Math.round(value)} days`;
    if (isCountKey(key)) return value.toLocaleString("en-IN");
    return formatINR(value);
  }
  if (typeof value === "string" && /^\d{4}-\d{2}/.test(value)) {
    return new Date(value).toLocaleDateString("en-IN", { month: "short", year: "numeric" });
  }
  return String(value);
}
