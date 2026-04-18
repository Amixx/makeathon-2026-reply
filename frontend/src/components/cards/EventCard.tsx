import type { DiscoverItem } from '../../lib/types';
import { Pill } from '../ui/Pill';
import { Button } from '../ui/Button';
import styles from './CardBody.module.css';

interface Props {
  item: DiscoverItem;
  onSkip: (item: DiscoverItem) => void;
  onAccept: (item: DiscoverItem) => void;
}

export function EventCard({ item, onSkip, onAccept }: Props) {
  const meta = item.meta ?? {};
  const date = meta.date ?? 'May 22';
  const location = meta.location ?? 'TUM Campus';
  const desc = meta.description ?? `${location}`;

  return (
    <div className={styles.card}>
      <div className={styles.metaRow}>
        <Pill variant="event">📅 EVENT</Pill>
        <span className={styles.metaText}>{date}</span>
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
          One conversation at this event could open a door you didn't even know existed.
        </div>
      </div>
      <div className={styles.btnRow}>
        <Button variant="outline" onClick={() => onSkip(item)}>✕ Skip</Button>
        <Button variant="accent" onClick={() => onAccept(item)}>→ Attend</Button>
      </div>
    </div>
  );
}
