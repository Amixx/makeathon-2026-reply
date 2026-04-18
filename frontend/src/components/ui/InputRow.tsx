import type { CSSProperties, ReactNode } from 'react';
import styles from './InputRow.module.css';

interface InputRowProps {
  label: string;
  value?: ReactNode;
  placeholder?: string;
  selected?: boolean;
  required?: boolean;
  /** Optional action button label (e.g. "Edit") */
  action?: string;
  onAction?: () => void;
  onClick?: () => void;
  className?: string;
  style?: CSSProperties;
}

export function InputRow({
  label,
  value,
  placeholder,
  selected = false,
  required = false,
  action,
  onAction,
  onClick,
  className = '',
  style,
}: InputRowProps) {
  const hasValue = value !== undefined && value !== null && value !== '';
  return (
    <div
      className={[styles.row, selected ? styles.selected : '', className].filter(Boolean).join(' ')}
      style={style}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
    >
      <span className={[styles.label, required ? styles.labelRequired : ''].filter(Boolean).join(' ')}>
        {label}
      </span>
      <div className={styles.split}>
        <span className={[styles.value, !hasValue ? styles.valueMuted : ''].filter(Boolean).join(' ')}>
          {hasValue ? value : placeholder ?? '—'}
        </span>
        {action && (
          <button className={styles.miniBtn} onClick={(e) => { e.stopPropagation(); onAction?.(); }}>
            {action}
          </button>
        )}
      </div>
    </div>
  );
}
