import type { CSSProperties, MouseEvent, ReactNode } from 'react';
import styles from './Button.module.css';

export type ButtonVariant = 'primary' | 'accent' | 'ghost' | 'outline';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  onClick?: (e: MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => void;
  children: ReactNode;
  disabled?: boolean;
  as?: 'button' | 'a';
  href?: string;
  full?: boolean;
  className?: string;
  style?: CSSProperties;
  type?: 'button' | 'submit' | 'reset';
}

export function Button({
  variant = 'primary',
  size = 'md',
  onClick,
  children,
  disabled = false,
  as: Tag = 'button',
  href,
  full = false,
  className = '',
  style,
  type = 'button',
}: ButtonProps) {
  const cls = [
    styles.btn,
    styles[variant],
    size === 'lg' ? styles.sizeLg : size === 'sm' ? styles.sizeSm : '',
    full ? styles.full : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  if (Tag === 'a') {
    return (
      <a href={href} className={cls} style={style} onClick={onClick as (e: MouseEvent<HTMLAnchorElement>) => void}>
        {children}
      </a>
    );
  }

  return (
    <button type={type} className={cls} style={style} onClick={onClick as (e: MouseEvent<HTMLButtonElement>) => void} disabled={disabled}>
      {children}
    </button>
  );
}
