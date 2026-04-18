import { useState } from "react";
import type { PlanOutput } from "../../lib/types";
import styles from "./StepPath.module.css";

type Props = {
  output: PlanOutput;
};

export default function StepPath({ output }: Props) {
  const [copied, setCopied] = useState<string | null>(null);

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

      <div className={styles.actionCard}>
        <div className={styles.detailTitle}>{output.action.title}</div>
        <div className={styles.detailBody}>{output.action.detail}</div>
        {output.action.link && (
          <a
            className={styles.linkBtn}
            href={output.action.link.href}
            target="_blank"
            rel="noreferrer"
          >
            {output.action.link.label} ↗
          </a>
        )}
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
