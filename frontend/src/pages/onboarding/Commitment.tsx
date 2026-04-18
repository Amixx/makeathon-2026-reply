import { useState } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'framer-motion';
import { ProgressDots, SectionLabel } from '../../components/ui';
import { postProfile } from '../../lib/agent';
import { useOnboarding } from '../../store/onboarding';
import s from './onboarding.module.css';

type CommitmentLevel = 'whisper' | 'steady' | 'push';

const OPTIONS: {
  key: CommitmentLevel;
  name: string;
  desc: string;
  hours: string;
  icon: React.ReactNode;
}[] = [
  {
    key: 'whisper',
    name: 'Keep me on the map',
    desc: 'A nudge a week.',
    hours: '30 MIN',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5l6.74-6.76z" />
        <line x1="16" y1="8" x2="2" y2="22" />
        <line x1="17.5" y1="15" x2="9" y2="15" />
      </svg>
    ),
  },
  {
    key: 'steady',
    name: 'Make real moves',
    desc: 'A tangible step each week.',
    hours: '2–3 H',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
      </svg>
    ),
  },
  {
    key: 'push',
    name: 'Big push month',
    desc: 'Run with what you have.',
    hours: '5+ H',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
        <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
        <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
      </svg>
    ),
  },
];

export default function Commitment() {
  const navigate = useNavigate();
  const store = useOnboarding();
  const [selected, setSelected] = useState<CommitmentLevel>(store.commitment);
  const [posting, setPosting] = useState(false);

  async function handleContinue() {
    store.setField('commitment', selected);
    setPosting(true);
    try {
      const profile = await postProfile({
        vision: store.vision,
        blockers: store.blockers,
        program: store.program,
        interest: store.interest,
        semester: store.semester,
        cvFileName: store.cvFileName,
        githubUrl: store.githubUrl,
        linkedinUrl: store.linkedinUrl,
        interests: store.interests,
        tumSsoId: store.tumSsoId,
        tumSsoConnected: store.tumSsoConnected,
        commitment: selected,
      });
      if (profile.commitment) {
        store.hydrate(profile);
      }
    } catch {
      // backend may not be running in demo — carry on
    }
    setPosting(false);
    navigate('/swarm');
  }

  return (
    <div className={s.page}>
      <div className={s.inner}>
        {/* Top nav */}
        <div className={s.topNav}>
          <button className={s.backBtn} onClick={() => navigate('/onboarding/ground')} aria-label="Back">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <div className={s.dotsWrap}>
            <ProgressDots total={4} current={3} />
          </div>
          <span className={s.counter}>04 / 04</span>
        </div>

        {/* Heading */}
        <div className={s.heading}>
          <SectionLabel>COMMITMENT</SectionLabel>
          <h2 className={s.qTitle}>How much room does May have?</h2>
        </div>

        <p className={s.commitCopy}>
          Every week I'll nudge you on the things you agreed to. Skip a week by telling me why.
        </p>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {OPTIONS.map((opt, i) => (
            <motion.div
              key={opt.key}
              custom={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.4 } }}
              className={[s.commitCard, selected === opt.key ? s.selected : ''].filter(Boolean).join(' ')}
              onClick={() => setSelected(opt.key)}
            >
              <div className={s.commitIcon}>{opt.icon}</div>
              <div className={s.commitContent}>
                <div className={s.commitName}>{opt.name}</div>
                <div className={s.commitDesc}>{opt.desc}</div>
              </div>
              <div className={s.commitHours}>{opt.hours}</div>
            </motion.div>
          ))}
        </div>

        <div className={s.spacer} />

        {/* CTA */}
        <button
          className={s.btnAccent}
          style={{ width: '100%' }}
          onClick={handleContinue}
          disabled={posting}
        >
          {posting ? 'Saving…' : 'Continue'}
          {!posting && (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
