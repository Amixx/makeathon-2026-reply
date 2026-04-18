import type { CSSProperties, ReactNode } from 'react';
import styles from './Card.module.css';

export type CardVariant = 'default' | 'muted' | 'dark' | 'accent' | 'success-border';

interface CardProps {
  variant?: CardVariant;
  tight?: boolean;
  lg?: boolean;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  onClick?: () => void;
}

export function Card({
  variant = 'default',
  tight,
  lg,
  children,
  className = '',
  style,
  onClick,
}: CardProps) {
  const variantClass =
    variant === 'success-border'
      ? styles.successBorder
      : variant !== 'default'
      ? styles[variant]
      : '';

  const cls = [
    styles.card,
    variantClass,
    tight ? styles.tight : '',
    lg ? styles.lg : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={cls} style={style} onClick={onClick}>
      {children}
    </div>
  );
}
