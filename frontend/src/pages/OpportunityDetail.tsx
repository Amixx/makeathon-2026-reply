import { useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router';
import { usePlan } from '../hooks/usePlan';
import { useOpportunities } from '../store/opportunities';
import { Pill } from '../components/ui/Pill';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { SectionLabel } from '../components/ui/SectionLabel';
import StepPath from '../components/discover/StepPath';
import type { DiscoverItem } from '../lib/types';
import type { PillVariant } from '../components/ui/Pill';
import styles from './OpportunityDetail.module.css';

const TYPE_PILL: Record<DiscoverItem['type'], PillVariant> = {
  course: 'course',
  event: 'event',
  person: 'person',
  scholarship: 'scholar',
};

const TYPE_LABEL: Record<DiscoverItem['type'], string> = {
  course: '🎓 COURSE',
  event: '📅 EVENT',
  person: '📩 PERSON',
  scholarship: '🎓 SCHOLARSHIP',
};

const TYPE_CTA: Record<DiscoverItem['type'], string> = {
  course: 'Enroll now',
  event: 'Add to calendar',
  person: 'Send email',
  scholarship: 'Review & apply',
};

export default function OpportunityDetail() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const storeItems = useOpportunities((s) => s.items);

  // Resolve the item from route state or the store
  const item: DiscoverItem | null =
    (location.state as { item?: DiscoverItem } | null)?.item ??
    storeItems.find((i) => i.id === id) ??
    null;

  const { open, close, segments, output, completedSteps, toggleStep, isStreaming, error, retry } =
    usePlan();

  useEffect(() => {
    if (item) open(item);
    return () => close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item?.id]);

  if (!item) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <p style={{ color: 'var(--fg-muted)' }}>Item not found.</p>
          <Button variant="outline" onClick={() => navigate('/opportunities')}>
            ← Back
          </Button>
        </div>
      </div>
    );
  }

  const pillVariant = TYPE_PILL[item.type] ?? 'accent';
  const pillLabel = TYPE_LABEL[item.type] ?? item.type.toUpperCase();
  const ctaLabel = TYPE_CTA[item.type] ?? 'Review & send';

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        {/* Header nav */}
        <div className={styles.topNav}>
          <button className={styles.backBtn} onClick={() => navigate('/opportunities')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back to May
          </button>
          <span className={styles.counter}>DETAIL</span>
        </div>

        <Pill variant={pillVariant}>{pillLabel}</Pill>
        <h1 className={styles.title}>{item.title}</h1>

        {/* Streaming tool trail */}
        {(isStreaming || segments.length > 0) && (
          <div className={styles.trailSection}>
            <SectionLabel>AGENT RESEARCH</SectionLabel>
            <div className={styles.trail}>
              {segments.map((seg) => {
                if (seg.kind === 'tool') {
                  const tc = seg.toolCall;
                  return (
                    <div key={seg.id} className={styles.toolBadge} data-status={tc.status}>
                      <span className={styles.toolName}>{tc.toolName.replace(/_/g, ' ')}</span>
                      <span className={styles.toolStatus}>
                        {tc.status === 'running' ? '↻' : tc.status === 'error' ? '!' : '✓'}
                      </span>
                    </div>
                  );
                }
                return null;
              })}
              {isStreaming && (
                <div className={styles.toolBadge} data-status="running">
                  <span className={styles.toolName}>thinking…</span>
                  <span className={styles.toolStatus}>↻</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <Card variant="default" style={{ padding: 16 }}>
            <p style={{ color: 'var(--accent-700)', margin: 0, fontSize: 13 }}>{error}</p>
            <Button variant="outline" size="sm" onClick={retry} style={{ marginTop: 8 }}>
              Retry
            </Button>
          </Card>
        )}

        {/* Plan output */}
        {output && !isStreaming && (
          <div className={styles.planSection}>
            <StepPath
              output={output}
              completedSteps={completedSteps}
              onToggleStep={toggleStep}
            />

            {/* Email draft card */}
            {output.email && (
              <Card variant="default" style={{ marginTop: 16 }}>
                <div className={styles.letterHead}>
                  <SectionLabel>AGENT DRAFT · {item.type === 'person' ? 'EMAIL' : 'MOTIVATION LETTER'}</SectionLabel>
                  <span className={styles.readyBadge}>ready</span>
                </div>
                <blockquote className={styles.letterBody}>{output.email.body}</blockquote>
                {output.email.anchor_note && (
                  <p className={styles.letterMeta}>{output.email.anchor_note}</p>
                )}
              </Card>
            )}
          </div>
        )}

        {/* Footer actions */}
        <div className={styles.footer}>
          <Button variant="outline" onClick={() => navigate('/opportunities')}>
            ← Back
          </Button>
          <Button
            variant="accent"
            onClick={() => {
              console.log('[OpportunityDetail] CTA clicked for:', item.id);
            }}
          >
            {ctaLabel} →
          </Button>
        </div>
      </div>
    </div>
  );
}
