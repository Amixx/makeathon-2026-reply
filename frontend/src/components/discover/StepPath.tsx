import { useState } from "react";
import type { PlanOutput } from "../../lib/types";
import styles from "./StepPath.module.css";

type Props = {
  output: PlanOutput;
  completedSteps: Set<number>;
  onToggleStep: (index: number) => void;
};

type StepState = "done" | "current" | "locked";

function stepState(
  index: number,
  firstIncomplete: number,
  completed: Set<number>,
): StepState {
  if (completed.has(index)) return "done";
  if (index === firstIncomplete) return "current";
  return "locked";
}

function rowClass(index: number, total: number): string {
  if (total <= 1) return styles.rowCenter;
  // zig-zag: 0=center, 1=left, 2=right, 3=left, 4=right, ...
  if (index === 0) return styles.rowCenter;
  return index % 2 === 1 ? styles.rowLeft : styles.rowRight;
}

export default function StepPath({
  output,
  completedSteps,
  onToggleStep,
}: Props) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const total = output.steps.length;
  const firstIncomplete = output.steps.findIndex(
    (_, idx) => !completedSteps.has(idx),
  );
  const actualFirstIncomplete = firstIncomplete < 0 ? total : firstIncomplete;

  const progressPct =
    total > 0 ? Math.round((completedSteps.size / total) * 100) : 0;

  const copyToClipboard = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      window.setTimeout(() => setCopied((k) => (k === key ? null : k)), 1800);
    } catch {
      // ignore
    }
  };

  return (
    <div className={styles.wrap}>
      {output.intro && <p className={styles.intro}>{output.intro}</p>}

      <div className={styles.progress}>
        <span>
          {completedSteps.size} / {total} steps
        </span>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <span>{progressPct}%</span>
      </div>

      <div className={styles.path}>
        {output.steps.map((step, idx) => {
          const state = stepState(idx, actualFirstIncomplete, completedSteps);
          const isExpanded = expandedStep === idx;
          const isCurrent = state === "current";

          return (
            <div
              key={`${step.title}-${idx}`}
              className={`${styles.row} ${rowClass(idx, total)}`}
            >
              <div className={styles.nodeWrap}>
                {isCurrent && !isExpanded && (
                  <span className={styles.startLabel}>START</span>
                )}
                <button
                  type="button"
                  className={`${styles.node} ${styles[state]}`}
                  onClick={() => setExpandedStep(isExpanded ? null : idx)}
                  aria-label={`Step ${idx + 1}: ${step.title}`}
                >
                  {state === "done" ? (
                    <span className={styles.nodeIcon}>✓</span>
                  ) : state === "locked" ? (
                    <span className={styles.nodeIcon}>🔒</span>
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </button>
                {isExpanded && (
                  <div className={styles.detail}>
                    <div className={styles.detailTitle}>
                      {idx + 1}. {step.title}
                    </div>
                    <div className={styles.detailMeta}>
                      {step.duration && (
                        <span className={styles.metaTag}>{step.duration}</span>
                      )}
                      <span className={styles.metaTag}>
                        {state === "done"
                          ? "Done"
                          : state === "current"
                            ? "Next up"
                            : "Locked"}
                      </span>
                    </div>
                    <div className={styles.detailBody}>{step.detail}</div>
                    {step.why && (
                      <div className={styles.why}>
                        <span className={styles.whyLabel}>
                          Why this specifically
                        </span>
                        {step.why}
                      </div>
                    )}
                    <div className={styles.detailActions}>
                      {step.link && (
                        <a
                          className={styles.linkBtn}
                          href={step.link.href}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {step.link.label} ↗
                        </a>
                      )}
                      <button
                        type="button"
                        className={`${styles.markBtn} ${state === "done" ? styles.markBtnDone : ""}`}
                        onClick={() => onToggleStep(idx)}
                      >
                        {state === "done" ? "↺ Mark undone" : "✓ Mark done"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {output.email && (
        <section className={styles.emailCard}>
          <span className={styles.cardLabel}>Ready-to-send email</span>
          {output.email.subject && (
            <div className={styles.cardTitle}>{output.email.subject}</div>
          )}
          <div className={styles.emailMeta}>
            {output.email.to && (
              <span>
                <strong>To:</strong> {output.email.to}
              </span>
            )}
            {output.email.subject && (
              <span>
                <strong>Subject:</strong> {output.email.subject}
              </span>
            )}
          </div>
          <pre className={styles.emailBody}>{output.email.body}</pre>
          {output.email.anchor_note && (
            <span className={styles.anchor}>{output.email.anchor_note}</span>
          )}
          <button
            type="button"
            className={styles.copyBtn}
            onClick={() =>
              copyToClipboard(output.email?.body ?? "", "email-body")
            }
          >
            {copied === "email-body" ? "Copied!" : "Copy email"}
          </button>
        </section>
      )}

      {output.key_facts && output.key_facts.length > 0 && (
        <section className={styles.factsCard}>
          <span className={styles.cardLabel}>Key facts I pulled</span>
          <ul className={styles.factsList}>
            {output.key_facts.map((fact, i) => (
              <li key={`${fact.label}-${i}`} className={styles.fact}>
                <span className={styles.factLabel}>{fact.label}</span>
                <span className={styles.factValue}>{fact.value}</span>
                {fact.note && (
                  <span className={styles.factNote}>{fact.note}</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {output.reassurance && (
        <section className={styles.reassureCard}>
          <span className={styles.cardLabel}>If this feels scary</span>
          <p className={styles.reassure}>{output.reassurance}</p>
        </section>
      )}
    </div>
  );
}
