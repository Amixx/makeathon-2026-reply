import { useEffect, useRef, type CSSProperties } from 'react';
import { motion } from 'framer-motion';
import Markdown from 'react-markdown';
import styles from './AgentCard.module.css';
import { Pill } from './Pill';
import type { PillVariant } from './Pill';
import type { StreamEntry } from '../../hooks/useSwarm';
import type { DiscoverItem } from '../../lib/types';

export type BulletStatus = 'queued' | 'running' | 'done' | 'alert';

export interface AgentBullet {
  text: string;
  status: BulletStatus;
}

interface AgentCardProps {
  name: string;
  emoji: string;
  status: PillVariant;
  bullets: AgentBullet[];
  streamLog?: StreamEntry[];
  items?: DiscoverItem[];
  /** Stagger delay index */
  index?: number;
  className?: string;
  style?: CSSProperties;
}

/** Strip fenced JSON blocks and bare JSON arrays from display text */
function stripJson(text: string): string {
  // Remove ```json ... ``` blocks
  let cleaned = text.replace(/```json\s*\n[\s\S]*?```/g, '');
  // Remove bare JSON arrays starting with [ on its own line
  cleaned = cleaned.replace(/^\[[\s\S]*\]$/m, '');
  return cleaned.trim();
}

const STATUS_LABELS: Record<PillVariant, string> = {
  accent: 'Accent',
  course: 'Course',
  event: 'Event',
  person: 'Person',
  scholar: 'Scholar',
  success: 'Done',
  dark: 'Dark',
  draft: 'Draft',
  sent: 'Sent',
  pending: 'Pending',
  working: 'Working',
  drafting: 'Drafting',
  writing: 'Writing',
  scheduled: 'Scheduled',
  ready: 'Ready',
};

export function AgentCard({
  name,
  emoji,
  status,
  streamLog = [],
  items = [],
  index = 0,
  className = '',
  style,
}: AgentCardProps) {
  const isWorking = status === 'working';
  const isDone = status === 'ready';
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll stream log to bottom while working
  useEffect(() => {
    if (!isWorking) return;
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [streamLog, isWorking]);

  return (
    <motion.div
      className={[styles.card, isWorking ? styles.cardWorking : '', className].filter(Boolean).join(' ')}
      style={style}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: 'easeOut', delay: index * 0.09 }}
    >
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.left}>
          <span className={styles.iconCircle}>{emoji}</span>
          <span className={styles.name}>{name}</span>
        </div>
        <Pill variant={status}>{STATUS_LABELS[status]}</Pill>
      </div>

      {/* Body: fixed-height scrollable area */}
      <div className={styles.body}>
        {/* Collapsible stream section */}
        {streamLog.length > 0 && (
          <details className={styles.streamDetails} open={isWorking}>
            <summary className={styles.streamSummary}>
              {isWorking ? '⟳ working…' : `${streamLog.length} steps completed`}
            </summary>
            <div className={styles.streamScroll} ref={scrollRef}>
              {streamLog.map((entry, i) => {
                if (entry.kind === 'text') {
                  const cleaned = stripJson(entry.content);
                  if (!cleaned) return null;
                  return (
                    <div key={i} className={styles.streamText}>
                      <Markdown>{cleaned}</Markdown>
                    </div>
                  );
                }
                if (entry.kind === 'tool_start') {
                  return (
                    <div key={i} className={styles.streamTool}>
                      <span className={styles.toolDotRunning} />
                      <span className={styles.toolBadge}>{entry.name}</span>
                    </div>
                  );
                }
                if (entry.kind === 'tool_done') {
                  return (
                    <div key={i} className={styles.streamTool}>
                      <span className={entry.error ? styles.toolDotError : styles.toolDotDone} />
                      <span className={styles.toolBadge}>{entry.name}</span>
                      <span className={styles.toolCheck}>{entry.error ? '✗' : '✓'}</span>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          </details>
        )}

        {/* Items shown when done — title only, expandable */}
        {isDone && items.length > 0 && (
          <div className={styles.itemList}>
            {items.map((item) => (
              <details key={item.id} className={styles.itemDetails}>
                <summary className={styles.itemTitle}>{item.title}</summary>
                <div className={styles.itemBody}>
                  {item.what && <p>{item.what}</p>}
                  {item.why && <p className={styles.itemWhy}>{item.why}</p>}
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
