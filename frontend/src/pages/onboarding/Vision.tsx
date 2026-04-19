import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import { AnimatePresence, motion } from 'framer-motion';
import { ProgressDots, SectionLabel, VoiceOrb } from '../../components/ui';
import { extractInterests, postProfile } from '../../lib/agent';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { transcribeAudio } from '../../lib/voice';
import { useOnboarding } from '../../store/onboarding';
import s from './onboarding.module.css';

const THINKING_PHRASES = [
  'Listening back to your memo…',
  'Catching the through-line…',
  'Pulling out what you actually meant…',
  'Spotting the interests hiding in there…',
  'Untangling the blockers…',
  'Sketching your first draft…',
  'Almost there — tidying it up…',
];

export default function Vision() {
  const navigate = useNavigate();
  const setField = useOnboarding((st) => st.setField);
  const vision = useOnboarding((st) => st.vision);
  const interests = useOnboarding((st) => st.interests);
  const interest = useOnboarding((st) => st.interest);

  const [saving, setSaving] = useState(false);
  const [voiceBusy, setVoiceBusy] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const recorder = useVoiceRecorder();

  useEffect(() => {
    if (!voiceBusy) return;
    setThinkingIndex(0);
    const id = setInterval(() => {
      setThinkingIndex((i) => (i + 1) % THINKING_PHRASES.length);
    }, 1600);
    return () => clearInterval(id);
  }, [voiceBusy]);

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

  async function handleVoiceTap() {
    if (voiceBusy) return;
    setVoiceError(null);

    if (!recorder.listening) {
      await recorder.start();
      return;
    }

    const blob = await recorder.stop();
    if (!blob) {
      setVoiceError('No recording was captured.');
      return;
    }

    setVoiceBusy(true);
    try {
      const result = await transcribeAudio(blob);
      const nextVision = result.fields.vision?.trim() || result.summary?.trim() || result.text.trim();
      const nextInterests = result.fields.interests ?? [];
      const nextInterest = result.fields.interest?.trim() || nextInterests[0] || '';
      const nextBlockers = result.fields.blockers?.trim() || '';

      if (nextVision) setField('vision', nextVision);
      if (nextInterests.length > 0) setField('interests', nextInterests);
      if (nextInterest) setField('interest', nextInterest);
      if (nextBlockers) setField('blockers', nextBlockers);
      if (result.fields.program?.trim()) setField('program', result.fields.program.trim());
      if (result.fields.semester?.trim()) setField('semester', result.fields.semester.trim());
      setVoiceTranscript(result.text);

      await postProfile({
        vision: nextVision || undefined,
        blockers: nextBlockers || undefined,
        interests: nextInterests.length > 0 ? nextInterests : undefined,
        interest: nextInterest || undefined,
        program: result.fields.program?.trim() || undefined,
        semester: result.fields.semester?.trim() || undefined,
      });
    } catch (error) {
      setVoiceError(error instanceof Error ? error.message : 'Voice memo processing failed.');
    } finally {
      setVoiceBusy(false);
    }
  }

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
          <p className={s.qSub}>Record one full memo if you want. We&apos;ll turn it into a first draft for your vision, interests, and blockers, then you can edit it below.</p>
        </div>

        {/* Orb */}
        <div className={s.orbWrap}>
          <VoiceOrb listening={recorder.listening} onClick={handleVoiceTap} />
        </div>

        {/* Voice status */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div className={s.pausePill} style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
            {voiceBusy ? (
              <>
                <motion.span
                  aria-hidden
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    border: '2px solid currentColor',
                    borderTopColor: 'transparent',
                    display: 'inline-block',
                  }}
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 0.9, ease: 'linear' }}
                />
                <AnimatePresence mode="wait">
                  <motion.span
                    key={thinkingIndex}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.35 }}
                  >
                    {THINKING_PHRASES[thinkingIndex]}
                  </motion.span>
                </AnimatePresence>
              </>
            ) : recorder.listening ? (
              'RECORDING · TAP AGAIN TO STOP'
            ) : (
              'TAP THE ORB TO RECORD ONE MEMO'
            )}
          </div>
        </div>

        {(voiceError || recorder.error) && <p className={s.inlineError}>{voiceError || recorder.error}</p>}

        {voiceTranscript && (
          <motion.div
            className={s.visionCard}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <SectionLabel>VOICE MEMO · TRANSCRIPT</SectionLabel>
            <p className={s.qSub}>{voiceTranscript}</p>
          </motion.div>
        )}

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
