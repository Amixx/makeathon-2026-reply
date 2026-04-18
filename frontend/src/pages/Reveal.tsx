import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'framer-motion';
import { useOpportunities } from '../store/opportunities';
import { Button } from '../components/ui/Button';
import styles from './Reveal.module.css';

export default function Reveal() {
  const navigate = useNavigate();
  const items = useOpportunities((s) => s.items);
  const count = Math.max(items.length, 5); // show at least 5 for demo appeal

  const [displayCount, setDisplayCount] = useState(0);
  const [phase, setPhase] = useState<'opening' | 'ready'>('opening');
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    let n = 0;
    const tick = () => {
      n++;
      setDisplayCount(n);
      if (n < count) {
        rafRef.current = window.setTimeout(tick, 120);
      } else {
        // Final pop animation handled by CSS
        rafRef.current = window.setTimeout(() => setPhase('ready'), 600);
      }
    };
    rafRef.current = window.setTimeout(tick, 400);
    return () => {
      if (rafRef.current) clearTimeout(rafRef.current);
    };
  }, [count]);

  return (
    <div className={styles.page}>
      <div className={styles.glow} />
      <div className={styles.inner}>
        <div className={styles.top}>
          <span className={styles.label}>· YOUR MAY</span>
          <span className={styles.sub}>shaped around what you said</span>
        </div>

        <motion.div
          className={styles.bigNumber}
          animate={displayCount >= count ? { scale: [1, 1.1, 1] } : {}}
          transition={{ duration: 0.4 }}
        >
          {displayCount}
        </motion.div>
        <div className={styles.oppsLabel}>opportunities</div>

        <blockquote className={styles.quote}>
          "The month you'd normally spend procrastinating — now has five doors open."
        </blockquote>

        <div className={styles.spacer} />

        <div className={styles.bottom}>
          <div className={styles.progressBar}>
            <div className={styles.fill} />
          </div>
          <span className={styles.openingLabel}>
            {phase === 'ready' ? 'READY.' : 'OPENING…'}
          </span>
          <Button
            variant="accent"
            size="lg"
            onClick={() => navigate('/opportunities')}
            style={{ marginTop: 14 }}
          >
            Open your May →
          </Button>
        </div>
      </div>
    </div>
  );
}
