import type { ReactNode } from "react";

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts
    .filter((part) => part.length > 0)
    .map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={`${keyPrefix}-b-${index}`}>{part.slice(2, -2)}</strong>;
      }
      return <span key={`${keyPrefix}-t-${index}`}>{part}</span>;
    });
}

function normalizeListLine(line: string): string {
  return line.replace(/^[\*+\-]\s+/, "").replace(/\s+\+\s+/g, " ");
}

interface Props {
  text: string;
}

export function LlmMarkdownBody({ text }: Props) {
  const blocks: ReactNode[] = [];
  const lines = text.split("\n");
  let listBuffer: string[] = [];
  let blockIndex = 0;

  const flushList = () => {
    if (!listBuffer.length) return;
    blocks.push(
      <ul key={`list-${blockIndex++}`}>
        {listBuffer.map((item, index) => (
          <li key={index}>{renderInline(normalizeListLine(item), `li-${index}`)}</li>
        ))}
      </ul>,
    );
    listBuffer = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      continue;
    }

    if (/^[\*+\-]\s/.test(line)) {
      listBuffer.push(line);
      continue;
    }

    flushList();

    const headingMatch = line.match(/^\*\*(.+)\*\*:?\s*$/);
    if (headingMatch) {
      blocks.push(<h4 key={`h-${blockIndex++}`}>{headingMatch[1]}</h4>);
      continue;
    }

    blocks.push(<p key={`p-${blockIndex++}`}>{renderInline(line, `p-${blockIndex}`)}</p>);
  }

  flushList();
  return <div className="llm-markdown">{blocks}</div>;
}
