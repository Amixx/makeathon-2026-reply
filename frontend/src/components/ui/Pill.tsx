import type { CSSProperties, ReactNode } from 'react';
import styles from './Pill.module.css';

export type PillVariant =
  | 'accent'
  | 'course'
  | 'event'
  | 'person'
  | 'scholar'
  | 'success'
  | 'dark'
  | 'draft'
  | 'sent'
  | 'pending'
  | 'working'
  | 'drafting'
  | 'writing'
  | 'scheduled'
  | 'ready';

interface PillProps {
  variant?: PillVariant;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function Pill({ variant = 'accent', icon, children, className = '', style }: PillProps) {
  const cls = [styles.pill, styles[variant], className].filter(Boolean).join(' ');
  return (
    <span className={cls} style={style}>
      {icon && <span>{icon}</span>}
      {children}
    </span>
  );
}
