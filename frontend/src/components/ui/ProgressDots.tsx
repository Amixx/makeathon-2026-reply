import type { CSSProperties } from 'react';
import styles from './ProgressDots.module.css';

interface ProgressDotsProps {
  total: number;
  /** 0-indexed current step */
  current: number;
  className?: string;
  style?: CSSProperties;
}

export function ProgressDots({ total, current, className = '', style }: ProgressDotsProps) {
  return (
    <div className={[styles.wrap, className].filter(Boolean).join(' ')} style={style}>
      {Array.from({ length: total }).map((_, i) => {
        const isDone = i < current;
        const isActive = i === current;
        const cls = [styles.dot, isDone ? styles.done : '', isActive ? styles.active : '']
          .filter(Boolean)
          .join(' ');
        return <span key={i} className={cls} />;
      })}
    </div>
  );
}
