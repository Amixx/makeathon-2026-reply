import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';
import styles from './AgentCard.module.css';
import { Pill } from './Pill';
import type { PillVariant } from './Pill';
import type { ToolCall } from '../../lib/types';

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
  toolCalls?: ToolCall[];
  /** Show tool trail expanded by default */
  toolsExpanded?: boolean;
  borderAccent?: boolean;
  /** Stagger delay index — the parent passes the card index so each card is offset */
  index?: number;
  className?: string;
  style?: CSSProperties;
}

const MARKER_CHARS: Record<BulletStatus, string> = {
  queued: '○',
  running: '↻',
  done: '✓',
  alert: '!',
};

const MARKER_CLASS: Record<BulletStatus, string> = {
  queued: styles.markerQueued,
  running: styles.markerRunning,
  done: styles.markerDone,
  alert: styles.markerAlert,
};

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

const TOOL_DOT_CLASS: Record<ToolCall['status'], string> = {
  running: styles.toolStatusRunning,
  done: styles.toolStatusDone,
  error: styles.toolStatusError,
};

export function AgentCard({
  name,
  emoji,
  status,
  bullets,
  toolCalls = [],
  toolsExpanded = false,
  borderAccent = false,
  index = 0,
  className = '',
  style,
}: AgentCardProps) {
  const hasTools = toolCalls.length > 0;
  const isRunning = toolCalls.some((tc) => tc.status === 'running');
  return (
    <motion.div
      className={[styles.card, borderAccent ? styles.greenBorder : '', className]
        .filter(Boolean)
        .join(' ')}
      style={style}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: 'easeOut', delay: index * 0.09 }}
    >
      <div className={styles.header}>
        <div className={styles.left}>
          <span className={styles.iconCircle}>{emoji}</span>
          <span className={styles.name}>{name}</span>
        </div>
        <Pill variant={status}>{STATUS_LABELS[status]}</Pill>
      </div>

      {bullets.length > 0 && (
        <div className={styles.bullets}>
          {bullets.map((b, i) => (
            <motion.div
              key={i}
              className={[
                styles.bullet,
                b.status === 'alert' ? styles.bulletAlert : '',
                b.status === 'queued' ? styles.bulletMuted : '',
              ]
                .filter(Boolean)
                .join(' ')}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.24, ease: 'easeOut', delay: index * 0.09 + i * 0.06 }}
            >
              <span className={[styles.marker, MARKER_CLASS[b.status]].join(' ')}>
                {MARKER_CHARS[b.status]}
              </span>
              <span>{b.text}</span>
            </motion.div>
          ))}
        </div>
      )}

      {hasTools && (
        <div className={styles.toolTrail}>
          <details open={toolsExpanded || isRunning}>
            <summary className={styles.toolTrailSummary}>
              {toolCalls.length} tool call{toolCalls.length !== 1 ? 's' : ''}
            </summary>
            <div className={styles.toolList}>
              {toolCalls.map((tc) => (
                <div key={tc.id} className={styles.toolItem}>
                  <span className={[styles.toolStatusDot, TOOL_DOT_CLASS[tc.status]].join(' ')} />
                  <span className={styles.toolBadge}>{tc.toolName}</span>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}
    </motion.div>
  );
}
