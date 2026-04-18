import type { DiscoverItem } from "../../lib/types";
import styles from "./DiscoverList.module.css";

type Props = {
  items: DiscoverItem[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  onSelect: (item: DiscoverItem) => void;
};

export default function DiscoverList({
  items,
  isLoading,
  error,
  onRefresh,
  onSelect,
}: Props) {
  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>Campus Co-Pilot · Discover</span>
        <h1 className={styles.title}>Things you could do right now</h1>
        <p className={styles.subtitle}>
          Pragmatic, actionable items tailored to your program and interests —
          the kind of thing a well-connected senior would tell you over coffee.
          Pick one and we'll build a step-by-step plan (coming soon).
        </p>
        <div className={styles.toolbar}>
          <button
            type="button"
            className={styles.button}
            onClick={onRefresh}
            disabled={isLoading}
          >
            {isLoading ? "Thinking…" : "Regenerate ideas"}
          </button>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {isLoading && items.length === 0 && (
        <div className={styles.skeleton}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className={styles.skelCard} />
          ))}
        </div>
      )}

      {items.length > 0 && (
        <div className={styles.grid}>
          {items.map((item, idx) => (
            <button
              key={item.id}
              type="button"
              className={styles.card}
              onClick={() => onSelect(item)}
            >
              <span className={styles.cardIndex}>
                {String(idx + 1).padStart(2, "0")}
              </span>
              <span className={styles.cardTitle}>{item.title}</span>
              {item.why && <span className={styles.cardWhy}>{item.why}</span>}
              <span className={styles.cardCta}>Build me a plan →</span>
            </button>
          ))}
        </div>
      )}

      {!isLoading && items.length === 0 && !error && (
        <p className={styles.status}>No ideas yet — hit regenerate.</p>
      )}
    </div>
  );
}
