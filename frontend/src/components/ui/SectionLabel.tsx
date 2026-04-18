import type { CSSProperties, ReactNode } from 'react';
import styles from './SectionLabel.module.css';

interface SectionLabelProps {
  children: ReactNode;
  pulsing?: boolean;
  muted?: boolean;
  className?: string;
  style?: CSSProperties;
}

export function SectionLabel({ children, pulsing, muted, className = '', style }: SectionLabelProps) {
  const cls = [styles.label, muted ? styles.muted : '', className].filter(Boolean).join(' ');
  return (
    <span className={cls} style={style}>
      <span className={[styles.dot, pulsing ? styles.pulsing : ''].filter(Boolean).join(' ')} />
      {children}
    </span>
  );
}
