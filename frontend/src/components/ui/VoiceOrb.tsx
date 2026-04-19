import type { CSSProperties } from 'react';
import { motion } from 'framer-motion';
import styles from './VoiceOrb.module.css';

interface VoiceOrbProps {
  listening?: boolean;
  onClick?: () => void;
  className?: string;
  style?: CSSProperties;
}

export function VoiceOrb({ listening = false, onClick, className = '', style }: VoiceOrbProps) {
  return (
    <motion.div
      className={styles.wrap}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
    >
      <div
        className={[styles.orb, listening ? styles.listening : '', !onClick ? styles.staticOrb : '', className].filter(Boolean).join(' ')}
        style={style}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        aria-label={onClick ? (listening ? 'Listening…' : 'Tap to speak') : 'Voice mode coming soon'}
      />
    </motion.div>
  );
}
