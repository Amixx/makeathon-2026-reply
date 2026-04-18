import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import type { DiscoverItem, PlanOutput, PlanSegment } from "../../lib/types";
import ToolCallBadge from "../chat/ToolCallBadge";
import styles from "./PlanPanel.module.css";
import StepPath from "./StepPath";

type Props = {
  item: DiscoverItem;
  segments: PlanSegment[];
  output: PlanOutput | null;
  completedSteps: Set<number>;
  onToggleStep: (index: number) => void;
  isStreaming: boolean;
  error: string | null;
  onClose: () => void;
  onRetry: () => void;
};

export default function PlanPanel({
  item,
  segments,
  output,
  completedSteps,
  onToggleStep,
  isStreaming,
  error,
  onClose,
  onRetry,
}: Props) {
  const [trailOpen, setTrailOpen] = useState(true);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  // Auto-collapse research trail once the plan has been parsed — the user
  // wants the step path front and center, but should still be able to dig in.
  useEffect(() => {
    if (output) setTrailOpen(false);
  }, [output]);

  const hasAnything = segments.length > 0;
  const lastSegment = segments[segments.length - 1];
  const showTailCaret =
    isStreaming && lastSegment?.kind === "text" && lastSegment.content.length > 0;
  const showLoading = isStreaming && !hasAnything;
  const toolCount = segments.filter((s) => s.kind === "tool").length;

  return (
    <div
      className={styles.overlay}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <aside className={styles.panel} role="dialog" aria-modal="true">
        <header className={styles.head}>
          <div className={styles.headText}>
            <span className={styles.eyebrow}>Your step-by-step plan</span>
            <h2 className={styles.title}>{item.title}</h2>
            {item.why && <span className={styles.why}>{item.why}</span>}
          </div>
          <button
            type="button"
            className={styles.closeBtn}
            onClick={onClose}
            aria-label="Close plan"
          >
            ×
          </button>
        </header>

        <div className={styles.body}>
          {error && <div className={styles.error}>{error}</div>}

          {showLoading && (
            <div className={styles.loading}>
              Digging through TUMonline, career board, and LinkedIn…
            </div>
          )}

          {hasAnything && (
            <details
              className={styles.trail}
              open={trailOpen}
              onToggle={(e) =>
                setTrailOpen((e.target as HTMLDetailsElement).open)
              }
            >
              <summary className={styles.trailSummary}>
                <span className={styles.trailDot} />
                {isStreaming
                  ? "Thinking out loud…"
                  : `How I figured this out · ${toolCount} tool calls`}
              </summary>
              <div className={styles.timeline}>
                {segments.map((seg, idx) => {
                  const isLast = idx === segments.length - 1;
                  if (seg.kind === "text") {
                    return (
                      <div key={seg.id} className={styles.textSeg}>
                        <Markdown>{seg.content}</Markdown>
                        {isStreaming && isLast && (
                          <span className={styles.caret} aria-hidden />
                        )}
                      </div>
                    );
                  }
                  return (
                    <div key={seg.id} className={styles.toolSeg}>
                      <ToolCallBadge toolCall={seg.toolCall} />
                    </div>
                  );
                })}
                {isStreaming && !showTailCaret && !showLoading && hasAnything && (
                  <div className={styles.thinking}>thinking…</div>
                )}
              </div>
            </details>
          )}

          {output && (
            <StepPath
              output={output}
              completedSteps={completedSteps}
              onToggleStep={onToggleStep}
            />
          )}

          {!output && !isStreaming && hasAnything && !error && (
            <div className={styles.parseFallback}>
              Couldn't parse the structured plan from the agent's response. The
              research trail above still has the details.
            </div>
          )}
        </div>

        <footer className={styles.footer}>
          <button
            type="button"
            className={styles.footerBtn}
            onClick={onRetry}
            disabled={isStreaming}
          >
            Regenerate plan
          </button>
          <button
            type="button"
            className={styles.footerBtn}
            onClick={onClose}
          >
            Close
          </button>
        </footer>
      </aside>
    </div>
  );
}
