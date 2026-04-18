import type { DiscoverItem } from '../../lib/types';
import { Pill } from '../ui/Pill';
import { Button } from '../ui/Button';
import styles from './CardBody.module.css';

interface Props {
  item: DiscoverItem;
  onSkip: (item: DiscoverItem) => void;
  onAccept: (item: DiscoverItem) => void;
}

export function CourseCard({ item, onSkip, onAccept }: Props) {
  const meta = item.meta ?? {};
  const due = meta.due ?? meta.deadline ?? 'Apr 28';
  const desc = meta.description ?? meta.detail ?? `${meta.code ?? ''} ${meta.provider ?? 'TUM course'}`.trim();

  return (
    <div className={styles.card}>
      <div className={styles.metaRow}>
        <Pill variant="course">🎓 COURSE</Pill>
        <span className={styles.metaText}>due {due}</span>
      </div>
      <h3 className={styles.title}>{item.title}</h3>
      <div>
        <div className={styles.blockLabel}>WHAT IT IS</div>
        <div className={styles.blockWhat}>{desc}</div>
      </div>
      <div>
        <div className={styles.blockLabel}>WHY IT MATTERS</div>
        <div className={styles.blockWhy}>{item.why}</div>
      </div>
      <div>
        <div className={styles.blockLabelInverted}>IF THIS LANDS</div>
        <div className={styles.blockLand}>
          You'll graduate with this sought-after skill — and it goes straight on your thesis foundation.
        </div>
      </div>
      <div className={styles.btnRow}>
        <Button variant="outline" onClick={() => onSkip(item)}>✕ Skip</Button>
        <Button variant="accent" onClick={() => onAccept(item)}>→ Enroll</Button>
      </div>
    </div>
  );
}
