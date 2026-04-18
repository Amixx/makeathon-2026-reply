import type { DiscoverItem } from '../../lib/types';
import { Pill } from '../ui/Pill';
import { Button } from '../ui/Button';
import styles from './CardBody.module.css';

interface Props {
  item: DiscoverItem;
  onSkip: (item: DiscoverItem) => void;
  onAccept: (item: DiscoverItem) => void;
}

export function ScholarshipCard({ item, onSkip, onAccept }: Props) {
  const meta = item.meta ?? {};
  const deadline = meta.deadline ?? meta.due ?? 'Apr 30';
  const amount = meta.amount ?? '300 €/month';
  const desc = meta.description ?? `${amount} · merit + vision based. Drafted from your profile.`;

  return (
    <div className={styles.card}>
      <div className={styles.metaRow}>
        <Pill variant="scholar">🎓 SCHOLARSHIP</Pill>
        <span className={styles.metaText}>due {deadline}</span>
      </div>
      <h3 className={styles.title}>{item.title}</h3>
      <div>
        <div className={styles.blockLabel}>WHAT IT IS</div>
        <div className={styles.blockWhat}>{item.what || desc}</div>
      </div>
      <div>
        <div className={styles.blockLabel}>WHY IT MATTERS</div>
        <div className={styles.blockWhy}>{item.why}</div>
      </div>
      <div>
        <div className={styles.blockLabelInverted}>IF THIS LANDS</div>
        <div className={styles.blockLand}>
          {item.land || "One semester of breathing room — without having to compromise on the work that matters."}
        </div>
      </div>
      <div className={styles.btnRow}>
        <Button variant="outline" onClick={() => onSkip(item)}>✕ Skip</Button>
        <Button variant="accent" onClick={() => onAccept(item)}>→ Step in</Button>
      </div>
    </div>
  );
}
