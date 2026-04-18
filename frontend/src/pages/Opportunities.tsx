import { useState } from 'react';
import { useNavigate } from 'react-router';
import { AnimatePresence, motion } from 'framer-motion';
import { useOpportunities } from '../store/opportunities';
import { ProgressDots } from '../components/ui/ProgressDots';
import { Button } from '../components/ui/Button';
import { CourseCard } from '../components/cards/CourseCard';
import { EventCard } from '../components/cards/EventCard';
import { PersonCard } from '../components/cards/PersonCard';
import { ScholarshipCard } from '../components/cards/ScholarshipCard';
import type { DiscoverItem } from '../lib/types';
import styles from './Opportunities.module.css';

export default function Opportunities() {
  const navigate = useNavigate();
  const storeItems = useOpportunities((s) => s.items);

  const items: DiscoverItem[] =
    storeItems.length > 0
      ? storeItems
      : [
          {
            id: 'demo-1',
            title: 'Enroll in IN2320 · Autonomous Mobile Systems',
            why: 'Matches your robotics interest and fills the gap towards your thesis.',
            type: 'course',
            meta: { code: 'IN2320', provider: 'TUM', due: 'Apr 28' },
          },
          {
            id: 'demo-2',
            title: 'ESA/DLR Career Day · May 22',
            why: 'Direct line to space-sector employers — exactly your field.',
            type: 'event',
            meta: { date: 'May 22', location: 'DLR, Oberpfaffenhofen' },
          },
          {
            id: 'demo-3',
            title: 'Email Prof. Walter',
            why: 'The email you have been rewriting in your head for six weeks.',
            type: 'person',
            meta: { role: 'Professor', affiliation: 'TUM LRT', due: 'Apr 25' },
          },
          {
            id: 'demo-4',
            title: 'Apply to Deutschlandstipendium',
            why: 'You match the criteria and a draft is already waiting.',
            type: 'scholarship',
            meta: { amount: '300 €/month · 12 months', deadline: 'Apr 30' },
          },
        ];

  const [currentIdx, setCurrentIdx] = useState(0);
  const [finished, setFinished] = useState(false);

  function handleAccept(item: DiscoverItem) {
    navigate(`/opportunity/${item.id}`, { state: { item } });
  }

  function handleSkip() {
    if (currentIdx >= items.length - 1) {
      setFinished(true);
    } else {
      setCurrentIdx((prev) => prev + 1);
    }
  }

  function renderCard(item: DiscoverItem) {
    switch (item.type) {
      case 'event':
        return <EventCard item={item} onSkip={handleSkip} onAccept={() => handleAccept(item)} />;
      case 'person':
        return <PersonCard item={item} onSkip={handleSkip} onAccept={() => handleAccept(item)} />;
      case 'scholarship':
        return <ScholarshipCard item={item} onSkip={handleSkip} onAccept={() => handleAccept(item)} />;
      case 'course':
      default:
        return <CourseCard item={item} onSkip={handleSkip} onAccept={() => handleAccept(item)} />;
    }
  }

  if (finished) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <div className={styles.emptyState}>
            <span className={styles.emptyEmoji}>✓</span>
            <h2 className={styles.emptyTitle}>That's all for May</h2>
            <p className={styles.emptyBody}>You've reviewed everything your agents found.</p>
            <Button
              variant="primary"
              onClick={() => {
                setFinished(false);
                setCurrentIdx(0);
              }}
            >
              Start over
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const currentItem = items[currentIdx];

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.header}>
          <span className={styles.headerLeft}>YOUR MAY · {items.length} POSSIBILITIES</span>
          <span className={styles.headerRight}>{currentIdx + 1} / {items.length}</span>
        </div>

        <div className={styles.cardWrap}>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentItem.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.2 }}
            >
              {renderCard(currentItem)}
            </motion.div>
          </AnimatePresence>
        </div>

        <div className={styles.footer}>
          <ProgressDots total={items.length} current={currentIdx} />
        </div>
      </div>
    </div>
  );
}
