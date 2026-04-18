import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'framer-motion';
import { useSwarm } from '../hooks/useSwarm';
import { useOnboarding } from '../store/onboarding';
import { useOpportunities } from '../store/opportunities';
import { AgentCard } from '../components/ui/AgentCard';
import { Button } from '../components/ui/Button';
import { SectionLabel } from '../components/ui/SectionLabel';
import styles from './Swarm.module.css';

export default function Swarm() {
  const navigate = useNavigate();
  const { program, interest } = useOnboarding();
  const setItems = useOpportunities((s) => s.set);
  const { agents, items, isDiscovering, discoveryReady, done, error, start } = useSwarm();

  useEffect(() => {
    start({ program: program || undefined, interest: interest || undefined });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When done, persist items to the shared store
  useEffect(() => {
    if (done && items.length > 0) {
      setItems(items);
    }
  }, [done, items, setItems]);

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <SectionLabel pulsing>AGENT SWARM · LIVE</SectionLabel>

        {isDiscovering && (
          <motion.div
            className={styles.thinkingWrap}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <motion.div
              className={styles.thinkingBubble}
              animate={{ scale: [1, 1.02, 1] }}
              transition={{ duration: 1.8, repeat: Number.POSITIVE_INFINITY, ease: 'easeInOut' }}
            >
              <span className={styles.thinkingDot} />
              <span>Thinking about opportunities</span>
            </motion.div>
          </motion.div>
        )}

        <motion.div
          className={styles.grid}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: discoveryReady ? 1 : 0, y: discoveryReady ? 0 : 10 }}
          transition={{ duration: 0.32 }}
          style={{ pointerEvents: discoveryReady ? 'auto' : 'none' }}
        >
          {agents.map((agent, i) => (
            <AgentCard
              key={agent.id}
              name={agent.name}
              emoji={agent.emoji}
              status={agent.status}
              bullets={agent.bullets}
              borderAccent={agent.id === 'scholarship'}
              index={i}
            />
          ))}
        </motion.div>

        {error && (
          <motion.div
            className={styles.errorBox}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <span>{error}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => start({ program: program || undefined, interest: interest || undefined })}
            >
              Retry
            </Button>
          </motion.div>
        )}

        <motion.div
          className={styles.continueWrap}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: done ? 1 : 0, y: done ? 0 : 8 }}
          transition={{ duration: 0.32 }}
          style={{ pointerEvents: done ? 'auto' : 'none' }}
        >
          <Button
            variant="primary"
            size="lg"
            full
            onClick={() => navigate('/reveal')}
          >
            See what they found →
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
