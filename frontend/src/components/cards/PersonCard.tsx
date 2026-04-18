import type { DiscoverItem } from '../../lib/types';
import { Pill } from '../ui/Pill';
import { Button } from '../ui/Button';
import styles from './CardBody.module.css';

interface Props {
  item: DiscoverItem;
  onSkip: () => void;
  onAccept: () => void;
}

export function PersonCard({ item, onSkip, onAccept }: Props) {
  const meta = item.meta ?? {};
  const due = meta.due ?? meta.deadline ?? 'Apr 25';
  const role = meta.role ?? 'Researcher';
  const affiliation = meta.affiliation ?? 'TUM';
  const desc = `Cold email · ${role} · ${affiliation} · drafted and ready to send.`;

  return (
    <div className={styles.card}>
      <div className={styles.metaRow}>
        <Pill variant="person">📩 PERSON</Pill>
        <span className={styles.metaText}>due {due}</span>
      </div>
      <h3 className={styles.title}>{item.title}</h3>
      <div>
        <div className={styles.blockLabel}>WHAT IT IS</div>
        <div className={styles.blockWhat}>{item.what || meta.description || desc}</div>
      </div>
      <div>
        <div className={styles.blockLabel}>WHY IT MATTERS</div>
        <div className={styles.blockWhy}>{item.why}</div>
      </div>
      <div>
        <div className={styles.blockLabelInverted}>IF THIS LANDS</div>
        <div className={styles.blockLand}>
          {item.land || "You stop feeling stuck. Worst case: polite no. Best case: thesis advisor or job offer."}
        </div>
      </div>
      <div className={styles.btnRow}>
        <Button variant="outline" onClick={onSkip}>✕ Skip</Button>
        <Button variant="accent" onClick={onAccept}>→ Review & send</Button>
      </div>
    </div>
  );
}
