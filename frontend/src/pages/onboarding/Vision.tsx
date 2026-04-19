import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import { AnimatePresence, motion } from 'framer-motion';
import { ProgressDots, SectionLabel, VoiceOrb } from '../../components/ui';
import { extractInterests, postProfile } from '../../lib/agent';
import { useOnboarding } from '../../store/onboarding';
import s from './onboarding.module.css';

export default function Vision() {
  const navigate = useNavigate();
  const setField = useOnboarding((st) => st.setField);
  const vision = useOnboarding((st) => st.vision);
  const interests = useOnboarding((st) => st.interests);
  const interest = useOnboarding((st) => st.interest);

  const [saving, setSaving] = useState(false);

  const extractTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (extractTimer.current !== null) clearTimeout(extractTimer.current);
    if (vision.trim().length < 15) return;
    extractTimer.current = setTimeout(async () => {
      try {
        const result = await extractInterests(vision);
        if (result.length > 0) {
          setField('interests', result);
          if (!interest && result[0]) setField('interest', result[0]);
        }
      } catch {
        // ignore — chips stay as-is
      }
    }, 800);
    return () => {
      if (extractTimer.current !== null) clearTimeout(extractTimer.current);
    };
  }, [vision]);

  const canContinue = vision.trim().length > 0;

  async function handleContinue() {
    setSaving(true);
    try {
      await postProfile({
        vision,
        interests,
        interest: interest || interests[0] || undefined,
      });
    } catch {
      // carry on locally if backend is unavailable
    } finally {
      setSaving(false);
    }
    navigate('/onboarding/blockers');
  }

  return (
    <div className={s.page}>
      <div className={s.inner}>
        {/* Top nav */}
        <div className={s.topNav}>
          <button className={s.backBtn} onClick={() => navigate('/')} aria-label="Back">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <div className={s.dotsWrap}>
            <ProgressDots total={4} current={0} />
          </div>
          <span className={s.counter}>01 / 04</span>
        </div>

        {/* Heading */}
        <div className={s.heading}>
          <SectionLabel>YOUR FUTURE SELF · WISH</SectionLabel>
          <h2 className={s.qTitle}>What would Future You in 2029 be proud of?</h2>
          <p className={s.qSub}>Voice mode is coming soon. For now, type your answer below and we&apos;ll still pull out the key themes.</p>
        </div>

        {/* Orb */}
        <div className={s.orbWrap}>
          <VoiceOrb />
        </div>

        {/* Voice status */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div className={s.pausePill}>VOICE MODE COMING SOON · TYPE BELOW TO CONTINUE</div>
        </div>

        <motion.div
          className={s.textareaWrap}
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
        >
          <SectionLabel muted>TYPE YOUR VISION</SectionLabel>
          <textarea
            className={s.textarea}
            placeholder="I want to work on Mars robotics, ideally on the systems that actually move, navigate, and make decisions on the surface…"
            value={vision}
            onChange={(e) => setField('vision', e.target.value)}
          />
        </motion.div>

        {/* Extracted interest chips */}
        <AnimatePresence>
          {interests.length > 0 && (
            <motion.div
              className={s.visionCard}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <SectionLabel>YOUR VISION · EXTRACTED</SectionLabel>
              <div className={s.chips}>
                <AnimatePresence>
                  {interests.map((chip, i) => (
                    <motion.span
                      key={chip}
                      className={s.chip + (i === 0 ? ` ${s.anchor}` : '')}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ delay: i * 0.06 }}
                    >
                      {chip}
                    </motion.span>
                  ))}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className={s.spacer} />

        <button
          className={s.btnPrimary}
          style={{ width: '100%' }}
          disabled={!canContinue || saving}
          onClick={handleContinue}
        >
          {saving ? 'Saving…' : 'Continue'}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
