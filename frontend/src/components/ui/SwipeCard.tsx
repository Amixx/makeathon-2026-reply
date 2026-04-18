import type { CSSProperties, ReactNode } from 'react';
import { motion, useMotionValue, useTransform } from 'framer-motion';
import styles from './SwipeCard.module.css';

const THRESHOLD = 120;

interface SwipeCardProps {
  onAccept: () => void;
  onSkip: () => void;
  children: ReactNode;
  zIndex?: number;
  /** Pixel offset for stack illusion (behind cards) */
  offset?: number;
  className?: string;
  style?: CSSProperties;
}

export function SwipeCard({
  onAccept,
  onSkip,
  children,
  zIndex = 0,
  offset = 0,
  className = '',
  style,
}: SwipeCardProps) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-300, 0, 300], [-14, 0, 14]);
  const opacity = useTransform(x, [-300, -150, 0, 150, 300], [0, 0.5, 1, 0.5, 0]);

  function handleDragEnd(_: never, info: { offset: { x: number } }) {
    const dx = info.offset.x;
    if (dx > THRESHOLD) {
      onAccept();
    } else if (dx < -THRESHOLD) {
      onSkip();
    }
    // snap back is automatic — framer returns to 0 if dragSnapToOrigin
  }

  return (
    <motion.div
      className={[styles.card, className].filter(Boolean).join(' ')}
      style={{
        x,
        rotate,
        opacity,
        zIndex,
        scale: 1 - offset * 0.01,
        y: offset * 5,
        ...style,
      }}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.9}
      onDragEnd={handleDragEnd}
      dragSnapToOrigin
      whileDrag={{ cursor: 'grabbing' }}
    >
      {children}
    </motion.div>
  );
}
