import { useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import styles from './TypingText.module.css';

interface TypingTextProps {
  text: string;
  /** ms per character, default 45 */
  speed?: number;
  onDone?: () => void;
  className?: string;
  style?: CSSProperties;
}

export function TypingText({ text, speed = 45, onDone, className = '', style }: TypingTextProps) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Reset on text change
    indexRef.current = 0;
    setDisplayed('');
    setDone(false);

    function step() {
      const i = indexRef.current;
      if (i >= text.length) {
        setDone(true);
        onDone?.();
        return;
      }
      const ch = text[i];
      indexRef.current = i + 1;
      setDisplayed((prev) => prev + ch);
      const pause = ch === '.' || ch === ',' || ch === '\n' ? 180 : 0;
      const jitter = Math.random() * 30;
      timerRef.current = setTimeout(step, speed + jitter + pause);
    }

    timerRef.current = setTimeout(step, speed);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, speed]);

  return (
    <span className={[styles.root, className].filter(Boolean).join(' ')} style={style}>
      {displayed}
      {!done && <span className={styles.cursor} aria-hidden="true" />}
    </span>
  );
}
