import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useOpportunities } from '../store/opportunities';
import { SwipeStack } from '../components/ui/SwipeStack';
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

  // If no items in store (e.g. navigated directly), use fallback demo items
  const initialItems: DiscoverItem[] =
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
  const [stackKey, setStackKey] = useState(0); // force re-mount on restart
  const [finished, setFinished] = useState(false);

  function handleAccept(item: DiscoverItem) {
    navigate(`/opportunity/${item.id}`, { state: { item } });
  }

  function handleSkip(_item: DiscoverItem, remaining: DiscoverItem[]) {
    if (remaining.length === 0) {
      setFinished(true);
    } else {
      setCurrentIdx((prev) => prev + 1);
    }
  }

  function handleStackAccept(item: DiscoverItem, remaining: DiscoverItem[]) {
    if (remaining.length === 0) setFinished(true);
    handleAccept(item);
  }

  function renderCard(item: DiscoverItem) {
    switch (item.type) {
      case 'event':
        return (
          <EventCard
            item={item}
            onSkip={(i) => handleSkip(i, [])}
            onAccept={(i) => handleAccept(i)}
          />
        );
      case 'person':
        return (
          <PersonCard
            item={item}
            onSkip={(i) => handleSkip(i, [])}
            onAccept={(i) => handleAccept(i)}
          />
        );
      case 'scholarship':
        return (
          <ScholarshipCard
            item={item}
            onSkip={(i) => handleSkip(i, [])}
            onAccept={(i) => handleAccept(i)}
          />
        );
      case 'course':
      default:
        return (
          <CourseCard
            item={item}
            onSkip={(i) => handleSkip(i, [])}
            onAccept={(i) => handleAccept(i)}
          />
        );
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
                setStackKey((k) => k + 1);
              }}
            >
              Start over
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.header}>
          <span className={styles.headerLeft}>YOUR MAY · {initialItems.length} POSSIBILITIES</span>
          <span className={styles.headerRight}>{currentIdx + 1} / {initialItems.length}</span>
        </div>

        <div className={styles.stackWrap}>
          <SwipeStack
            key={stackKey}
            items={initialItems}
            renderCard={renderCard}
            onAccept={handleStackAccept}
            onSkip={(_item, remaining) => {
              setCurrentIdx((prev) => Math.min(prev + 1, initialItems.length - 1));
              if (remaining.length === 0) setFinished(true);
            }}
          />
        </div>

        <div className={styles.footer}>
          <span className={styles.footerHint}>← swipe to see the rest →</span>
          <ProgressDots
            total={initialItems.length}
            current={currentIdx}
          />
        </div>
      </div>
    </div>
  );
}
