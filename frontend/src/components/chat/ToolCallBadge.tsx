import { useState } from "react";
import type { ToolCall } from "../../lib/types";
import styles from "./ToolCallBadge.module.css";

const STATUS_LABEL: Record<ToolCall["status"], string> = {
  running: "running",
  done: "done",
  error: "error",
};

function formatInput(input: unknown): string {
  if (!input || typeof input !== "object") return "";
  const entries = Object.entries(input as Record<string, unknown>);
  if (entries.length === 0) return "";
  return entries.map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(", ");
}

type Props = {
  toolCall: ToolCall;
};

export default function ToolCallBadge({ toolCall }: Props) {
  const [expanded, setExpanded] = useState(false);
  const args = formatInput(toolCall.input);
  const hasResult = typeof toolCall.result === "string";

  return (
    <div className={styles.badge}>
      <button
        type="button"
        className={`${styles.summary} ${styles[toolCall.status]}`}
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className={styles.icon} aria-hidden>
          ⚙
        </span>
        <span className={styles.name}>{toolCall.toolName}</span>
        {args && <span className={styles.args}>({args})</span>}
        <span className={styles.status}>{STATUS_LABEL[toolCall.status]}</span>
      </button>
      {expanded && hasResult && (
        <pre className={styles.result}>{toolCall.result}</pre>
      )}
    </div>
  );
}
