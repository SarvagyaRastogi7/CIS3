type IconProps = { className?: string };

export function IconOverview({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2" y="2" width="7" height="7" rx="1" />
      <rect x="11" y="2" width="7" height="7" rx="1" />
      <rect x="2" y="11" width="7" height="7" rx="1" />
      <rect x="11" y="11" width="7" height="7" rx="1" />
    </svg>
  );
}

export function IconForecast({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 15 L8 9 L12 12 L17 5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 5 H17 V8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconScenarios({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M4 14 L10 4 L16 14 Z" strokeLinejoin="round" />
      <path d="M7 11 H13" strokeLinecap="round" />
    </svg>
  );
}

export function IconInsights({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="7" />
      <path d="M10 7 V10 L12 12" strokeLinecap="round" />
    </svg>
  );
}

export function IconAssistant({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M4 5 H16 V13 H11 L8 16 V13 H4 Z" strokeLinejoin="round" />
      <path d="M7 8 H13 M7 10.5 H11" strokeLinecap="round" />
    </svg>
  );
}
