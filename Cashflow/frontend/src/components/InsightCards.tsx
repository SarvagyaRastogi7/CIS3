import type { InsightItem } from "../types";

interface InsightCardProps {
  item: InsightItem;
  variant: "dashboard" | "prompt";
}

function InsightCard({ item, variant }: InsightCardProps) {
  if (variant === "prompt") {
    return (
      <article className="prompt-insight-card">
        <div className="prompt-insight-meta">
          <span className="prompt-insight-cat">{item.category}</span>
          <span className={`impact impact-${item.impact}`}>{item.impact}</span>
        </div>
        <h4>{item.title}</h4>
        <p>{item.description}</p>
      </article>
    );
  }

  return (
    <article className="insight-item">
      <div className="insight-item-header">
        <span className="insight-cat">{item.category}</span>
        <div className="insight-badges">
          <span className="insight-type insight-type-ai">AI</span>
          <span className={`impact impact-${item.impact}`}>{item.impact}</span>
        </div>
      </div>
      <h4>{item.title}</h4>
      <p>{item.description}</p>
    </article>
  );
}

interface InsightCardsProps {
  items: InsightItem[];
  variant: "dashboard" | "prompt";
  title?: string;
}

export function InsightCards({ items, variant, title }: InsightCardsProps) {
  if (items.length === 0) return null;

  if (variant === "prompt" && title) {
    return (
      <div className="prompt-block">
        <div className="prompt-block-header static">
          <span>{title}</span>
        </div>
        <div className="prompt-insight-list">
          {items.map((item) => (
            <InsightCard key={`${item.title}-${item.category}`} item={item} variant="prompt" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="insights-cards-grid">
      {items.map((item) => (
        <InsightCard key={`${item.title}-${item.category}`} item={item} variant="dashboard" />
      ))}
    </div>
  );
}
