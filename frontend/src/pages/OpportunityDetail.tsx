import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router';
import Markdown from 'react-markdown';
import { usePlan } from '../hooks/usePlan';
import { useOpportunities } from '../store/opportunities';
import { Pill } from '../components/ui/Pill';
import { Button } from '../components/ui/Button';
import { SectionLabel } from '../components/ui/SectionLabel';
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

const ACTION_EMOJI: Record<string, string> = {
  enrolled: '✓',
  registered: '✓',
  calendar_added: '📅',
  email_ready: '✉️',
  applied: '✓',
  application_ready: '📄',
  enrollment_ready: '📋',
  registration_ready: '📋',
  calendar_ready: '📅',
};

const ACTION_CTA: Record<string, string> = {
  enrolled: 'View on TUMonline',
  registered: 'View on TUMonline',
  calendar_added: 'Open calendar',
  email_ready: 'Send email →',
  applied: 'View application',
  application_ready: 'Review & apply',
  enrollment_ready: 'Enroll manually',
  registration_ready: 'Register manually',
  calendar_ready: 'Add to calendar',
};

export default function OpportunityDetail() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const storeItems = useOpportunities((s) => s.items);
  const [copied, setCopied] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const item: DiscoverItem | null =
    (location.state as { item?: DiscoverItem } | null)?.item ??
    storeItems.find((i) => i.id === id) ??
    null;

  const { open, close, segments, output, isStreaming, error, retry } =
    usePlan();

  useEffect(() => {
    if (item) open(item);
    return () => close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item?.id]);

  // Auto-scroll content to bottom while streaming
  useEffect(() => {
    if (!isStreaming) return;
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [segments, isStreaming]);

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

  const handleCta = () => {
    if (!output) return;
    const action = output.action;

    if (action.type === 'email_ready' && output.email) {
      const mailtoUrl = `mailto:${output.email.to ?? ''}?subject=${encodeURIComponent(output.email.subject ?? '')}&body=${encodeURIComponent(output.email.body)}`;
      window.location.href = mailtoUrl;
      return;
    }

    if (action.link?.href) {
      window.open(action.link.href, '_blank');
      return;
    }

    if (action.type === 'calendar_added' || action.type === 'calendar_ready') {
      window.open(
        'https://calendar.google.com/calendar/render?action=TEMPLATE&text=' +
          encodeURIComponent(item.title),
        '_blank',
      );
      return;
    }

    if (action.type === 'enrolled' || action.type === 'registered' || action.type === 'enrollment_ready' || action.type === 'registration_ready') {
      window.open('https://campus.tum.de', '_blank');
    }
  };

  const copyToClipboard = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      window.setTimeout(() => setCopied((k) => (k === key ? null : k)), 1800);
    } catch { /* ignore */ }
  };

  const isDone = action_type_is_done(output?.action?.type);

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

        <div className={styles.scrollArea} ref={scrollRef}>
        {/* Streaming agent output (also shown as fallback when parsing fails) */}
        {segments.length > 0 && (isStreaming || !output) && (
          <div className={styles.streamCard}>
            <div className={styles.streamHeader}>
              <SectionLabel>AGENT RESEARCH</SectionLabel>
              {isStreaming && <span className={styles.trailMeta}>Working…</span>}
            </div>
            <div className={styles.streamBody}>
              {segments.map((seg) => {
                if (seg.kind === 'text') {
                  return <Markdown key={seg.id}>{seg.content}</Markdown>;
                }
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
            </div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className={styles.streamCard}>
            <p style={{ color: 'var(--accent-700)', margin: 0, fontSize: 13 }}>{error}</p>
            <Button variant="outline" size="sm" onClick={retry} style={{ marginTop: 8 }}>
              Retry
            </Button>
          </div>
        )}

        {/* Action result */}
        {output && !isStreaming && (
          <div className={styles.resultCard}>
            {/* Action status */}
            <div className={styles.actionHeader}>
              <span className={styles.actionEmoji}>
                {ACTION_EMOJI[output.action.type] ?? '✓'}
              </span>
              <div className={styles.actionHeaderText}>
                <h2 className={styles.actionTitle}>{output.action.title}</h2>
                {isDone && <span className={styles.doneBadge}>DONE</span>}
                {!isDone && <span className={styles.readyBadge}>READY</span>}
              </div>
            </div>

            {/* Intro */}
            {output.intro && (
              <div className={styles.blockWhat}><Markdown>{output.intro}</Markdown></div>
            )}

            {/* Action detail */}
            <div className={styles.blockWhy}><Markdown>{output.action.detail}</Markdown></div>

            {/* Key facts */}
            {output.key_facts && output.key_facts.length > 0 && (
              <div>
                <div className={styles.blockLabel}>KEY FACTS</div>
                <div className={styles.factsList}>
                  {output.key_facts.map((fact, i) => (
                    <div key={`${fact.label}-${i}`} className={styles.factRow}>
                      <span className={styles.factLabel}>{fact.label}</span>
                      <span className={styles.factValue}>{fact.value}</span>
                      {fact.note && <span className={styles.factNote}>{fact.note}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Email draft */}
            {output.email && (
              <div>
                <div className={styles.blockLabel}>
                  {item.type === 'person' ? 'DRAFTED EMAIL' : 'MOTIVATION LETTER'}
                </div>
                <div className={styles.emailCard}>
                  {output.email.to && (
                    <div className={styles.emailMeta}>To: {output.email.to}</div>
                  )}
                  {output.email.subject && (
                    <div className={styles.emailMeta}>Subject: {output.email.subject}</div>
                  )}
                  <pre className={styles.emailBody}>{output.email.body}</pre>
                  {output.email.anchor_note && (
                    <span className={styles.anchorNote}>{output.email.anchor_note}</span>
                  )}
                  <button
                    className={styles.copyBtn}
                    onClick={() => copyToClipboard(output.email?.body ?? '', 'email')}
                  >
                    {copied === 'email' ? 'Copied!' : 'Copy email'}
                  </button>
                </div>
              </div>
            )}

            {/* Reassurance */}
            {output.reassurance && (
              <div className={styles.blockLand}><Markdown>{output.reassurance}</Markdown></div>
            )}
          </div>
        )}
        </div>

        {/* Footer actions */}
        <div className={styles.footer}>
          <Button variant="outline" onClick={() => navigate('/opportunities')}>
            ← Back
          </Button>
          <Button
            variant="accent"
            onClick={output ? handleCta : retry}
            disabled={isStreaming}
          >
            {isStreaming
              ? 'Working…'
              : output
                ? `${ACTION_CTA[output.action.type] ?? 'Continue'}`
                : 'Retry'}
          </Button>
        </div>
      </div>
    </div>
  );
}

function action_type_is_done(type?: string): boolean {
  if (!type) return false;
  return ['enrolled', 'registered', 'calendar_added', 'applied'].includes(type);
}
