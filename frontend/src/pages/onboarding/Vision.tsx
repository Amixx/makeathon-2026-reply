import { useState } from 'react';
import { useNavigate } from 'react-router';
import { AnimatePresence, motion } from 'framer-motion';
import { ProgressDots, SectionLabel, VoiceOrb } from '../../components/ui';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { postProfile } from '../../lib/agent';
import { transcribeAudio } from '../../lib/voice';
import { useOnboarding } from '../../store/onboarding';
import s from './onboarding.module.css';

export default function Vision() {
  const navigate = useNavigate();
  const setField = useOnboarding((st) => st.setField);
  const vision = useOnboarding((st) => st.vision);
  const interests = useOnboarding((st) => st.interests);
  const interest = useOnboarding((st) => st.interest);

  const { listening, start, stop } = useVoiceRecorder();
  const [transcribing, setTranscribing] = useState(false);
  const [showTextFallback, setShowTextFallback] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleOrbClick() {
    if (listening) {
      setTranscribing(true);
      const blob = await stop();
      if (blob) {
        try {
          const result = await transcribeAudio(blob);
          if (result.text) setField('vision', result.text);
          if (result.fields.interests?.length) setField('interests', result.fields.interests);
          if (result.fields.vision) setField('vision', result.fields.vision);
          if (!interest && result.fields.interests?.[0]) {
            setField('interest', result.fields.interests[0]);
          }
        } catch {
          // backend stub returns empty — that's fine, let user type
        }
      }
      setTranscribing(false);
    } else {
      await start();
    }
  }

  const canContinue = vision.trim().length > 0;

  async function handleContinue() {
    if (listening) {
      await handleOrbClick();
    }
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
          <SectionLabel pulsing={listening}>
            {listening ? 'LISTENING…' : 'YOUR FUTURE SELF · WISH'}
          </SectionLabel>
          <h2 className={s.qTitle}>What would Future You in 2029 be proud of?</h2>
        </div>

        {/* Orb */}
        <div className={s.orbWrap}>
          <VoiceOrb listening={listening} onClick={handleOrbClick} />
        </div>

        {/* Pause pill */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div className={s.pausePill}>
            {transcribing ? (
              <span>Transcribing…</span>
            ) : listening ? (
              <>
                <svg width="10" height="12" viewBox="0 0 10 12" fill="currentColor">
                  <rect x="0" y="0" width="3" height="12" rx="1" />
                  <rect x="7" y="0" width="3" height="12" rx="1" />
                </svg>
                <span>TAP ORB TO STOP</span>
              </>
            ) : (
              <span>TAP ORB TO START</span>
            )}
          </div>
        </div>

        {/* Live chips */}
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

        {/* Text fallback */}
        <AnimatePresence>
          {showTextFallback && (
            <motion.div
              className={s.textareaWrap}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <SectionLabel muted>TYPE YOUR VISION</SectionLabel>
              <textarea
                className={s.textarea}
                placeholder="I want to work in aerospace robotics at DLR, land a working-student role before graduation, and present at a conference…"
                value={vision}
                onChange={(e) => setField('vision', e.target.value)}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <div className={s.spacer} />

        {/* CTA row */}
        <div className={s.btnRow}>
          <button
            className={s.btnGhost}
            onClick={() => setShowTextFallback((v) => !v)}
          >
            {showTextFallback ? 'Hide text' : 'Type instead'}
          </button>
          <button
            className={s.btnPrimary}
            disabled={(!canContinue && !listening) || saving}
            onClick={handleContinue}
          >
            {saving ? 'Saving…' : listening ? 'Stop & continue' : 'Continue'}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
