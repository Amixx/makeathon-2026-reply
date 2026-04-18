import { useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { SwipeCard } from './SwipeCard';
import styles from './SwipeStack.module.css';

interface SwipeStackProps<T> {
  items: T[];
  renderCard: (item: T) => ReactNode;
  onAccept: (item: T, remaining: T[]) => void;
  onSkip: (item: T, remaining: T[]) => void;
  className?: string;
  style?: CSSProperties;
}

export function SwipeStack<T>({
  items: initialItems,
  renderCard,
  onAccept,
  onSkip,
  className = '',
  style,
}: SwipeStackProps<T>) {
  const [items, setItems] = useState<T[]>(initialItems);

  function pop() {
    const [_top, ...rest] = items;
    setItems(rest);
    return { top: _top, rest };
  }

  function handleAccept() {
    const { top, rest } = pop();
    onAccept(top, rest);
  }

  function handleSkip() {
    const { top, rest } = pop();
    onSkip(top, rest);
  }

  // Show at most 3 cards in the stack
  const visible = items.slice(0, 3);

  return (
    <div className={[styles.stack, className].filter(Boolean).join(' ')} style={style}>
      <AnimatePresence>
        {visible.map((item, i) => {
          const isTop = i === 0;
          const offset = i; // 0 for top, 1, 2 for behind
          return (
            <motion.div
              key={`${i}-${String(item)}`}
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{
                opacity: 0,
                x: 0,
                transition: { duration: 0.2 },
              }}
              transition={{ duration: 0.3, ease: [0.34, 1.56, 0.64, 1] }}
              style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10 - i, display: 'flex', justifyContent: 'center' }}
            >
              {isTop ? (
                <SwipeCard
                  onAccept={handleAccept}
                  onSkip={handleSkip}
                  zIndex={10 - i}
                  offset={0}
                >
                  {renderCard(item)}
                </SwipeCard>
              ) : (
                // Behind cards: not draggable, just visual offset
                <div
                  style={{
                    width: 'min(320px, calc(100vw - 48px))',
                    transform: `translate(${offset * 6}px, ${offset * 10}px) scale(${1 - offset * 0.02})`,
                    opacity: offset === 1 ? 0.6 : 0.3,
                    pointerEvents: 'none',
                    background: 'var(--bg-card)',
                    borderRadius: 18,
                    border: '1px solid var(--border-default)',
                    padding: 18,
                    boxShadow: '0 8px 30px -12px rgba(11, 14, 24, 0.18)',
                    minHeight: 80,
                    boxSizing: 'border-box',
                  }}
                />
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>

      {items.length === 0 && (
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-muted)', letterSpacing: 2, textTransform: 'uppercase' }}>
          All done
        </span>
      )}
    </div>
  );
}
