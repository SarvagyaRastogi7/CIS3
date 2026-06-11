import { LlmMarkdownBody } from "./LlmMarkdownBody";

interface Props {
  narrative: string | null | undefined;
  model?: string | null;
  error?: string | null;
  title?: string;
  attempted?: boolean;
}

export function LlmNarrative({
  narrative,
  model,
  error,
  title = "AI Advisory",
  attempted = false,
}: Props) {
  if (!attempted && !narrative && !error) return null;

  return (
    <section className="llm-narrative">
      <div className="llm-narrative-header">
        <h3>{title}</h3>
        {model && <span className="llm-model-badge">{model}</span>}
      </div>
      {narrative ? (
        <div className="llm-narrative-body">
          <LlmMarkdownBody text={narrative} />
        </div>
      ) : (
        <p className="llm-narrative-error">
          {error ?? "AI analysis is not available right now."}
        </p>
      )}
    </section>
  );
}
