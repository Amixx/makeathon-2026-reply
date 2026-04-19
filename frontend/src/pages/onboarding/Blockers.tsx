import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { AnimatePresence, motion } from 'framer-motion';
import { ProgressDots, SectionLabel, VoiceOrb } from '../../components/ui';
import { postProfile } from '../../lib/agent';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { transcribeBlockers } from '../../lib/voice';
import { useOnboarding } from '../../store/onboarding';
import s from './onboarding.module.css';

const PRESET_BLOCKERS = [
  { key: 'time', label: 'TIME' },
  { key: 'money', label: 'MONEY' },
  { key: 'confidence', label: 'CONFIDENCE' },
  { key: 'info', label: 'INFO OVERLOAD' },
  { key: 'avoidance', label: 'AVOIDANCE' },
  { key: 'burnout', label: 'BURNOUT' },
];

const HEAVY_THINKING_PHRASES = [
  'Sitting with what you said…',
  'Sorting feelings from facts…',
  'Finding the real weight…',
  'Separating the blocker from the backstory…',
  'Giving it a name…',
  'Writing it back gently…',
  'Almost there — one more pass…',
];

export default function Blockers() {
  const navigate = useNavigate();
  const setField = useOnboarding((st) => st.setField);
  const blockers = useOnboarding((st) => st.blockers);

  const [activePresets, setActivePresets] = useState<Set<string>>(new Set());

  const [saving, setSaving] = useState(false);
  const [voiceBusy, setVoiceBusy] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceTags, setVoiceTags] = useState<string[]>([]);
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const recorder = useVoiceRecorder();

  useEffect(() => {
    if (!voiceBusy) return;
    setThinkingIndex(0);
    const id = setInterval(() => {
      setThinkingIndex((i) => (i + 1) % HEAVY_THINKING_PHRASES.length);
    }, 1600);
    return () => clearInterval(id);
  }, [voiceBusy]);

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
      const result = await transcribeBlockers(blob);
      const nextBlockers = result.fields.blockers?.trim() || result.text.trim();
      if (nextBlockers) setField('blockers', nextBlockers);
      setVoiceTranscript(result.text);

      const tags = (result.fields.tags ?? []).map((t) => t.toUpperCase());
      setVoiceTags(tags);
      if (tags.length > 0) {
        const matchedKeys = new Set(
          PRESET_BLOCKERS.filter((p) => tags.includes(p.label)).map((p) => p.key),
        );
        setActivePresets(matchedKeys);
      }

      await postProfile({ blockers: nextBlockers || undefined });
    } catch (error) {
      setVoiceError(error instanceof Error ? error.message : 'Voice memo processing failed.');
    } finally {
      setVoiceBusy(false);
    }
  }

  function togglePreset(key: string) {
    const next = new Set(activePresets);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setActivePresets(next);
    // append preset to blockers text
    const label = PRESET_BLOCKERS.find((p) => p.key === key)?.label ?? key;
    const current = blockers;
    if (!next.has(key)) {
      // remove from text
      const cleaned = current.replace(new RegExp(`\\b${label}\\b[,;]?\\s*`, 'gi'), '').trim();
      setField('blockers', cleaned);
    } else {
      setField('blockers', current ? `${current}, ${label}` : label);
    }
  }

  async function handleContinue() {
    setSaving(true);
    try {
      await postProfile({ blockers });
    } catch {
      // fallback to local onboarding state if backend is unavailable
    } finally {
      setSaving(false);
    }
    navigate('/onboarding/ground');
  }

  return (
    <div className={s.page}>
      <div className={s.inner}>
        {/* Top nav */}
        <div className={s.topNav}>
          <button className={s.backBtn} onClick={() => navigate('/onboarding/vision')} aria-label="Back">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <div className={s.dotsWrap}>
            <ProgressDots total={4} current={1} />
          </div>
          <span className={s.counter}>02 / 04</span>
        </div>

        {/* Heading */}
        <div className={s.heading}>
          <SectionLabel>WOOP · OBSTACLE</SectionLabel>
          <h2 className={s.qTitle}>What's the part that feels heaviest?</h2>
          <p className={s.qSub}>Record one memo — we&apos;ll name the weight, not the career path. Edit below if it&apos;s not quite right.</p>
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
                    {HEAVY_THINKING_PHRASES[thinkingIndex]}
                  </motion.span>
                </AnimatePresence>
              </>
            ) : recorder.listening ? (
              'RECORDING · TAP AGAIN TO STOP'
            ) : (
              'TAP THE ORB TO RECORD WHAT FEELS HEAVY'
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
            {voiceTags.length > 0 && (
              <div className={s.chips} style={{ marginTop: 8 }}>
                {voiceTags.map((tag) => (
                  <span key={tag} className={s.chip}>
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </motion.div>
        )}

        <motion.div
          className={s.textareaWrap}
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
        >
          <SectionLabel muted>TYPE WHAT'S HEAVY</SectionLabel>
          <textarea
            className={s.textarea}
            placeholder="The heavy part is comparison. Everyone around me feels more polished and more obvious about where they are going…"
            value={blockers}
            onChange={(e) => setField('blockers', e.target.value)}
          />
        </motion.div>

        {/* Preset chips */}
        <div className={s.visionCard}>
          <SectionLabel>TAP TO TOGGLE BLOCKERS</SectionLabel>
          <div className={s.blockerChips}>
            {PRESET_BLOCKERS.map((p) => (
              <button
                key={p.key}
                className={[s.blockerChip, activePresets.has(p.key) ? s.active : ''].filter(Boolean).join(' ')}
                onClick={() => togglePreset(p.key)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className={s.spacer} />

        <button
          className={s.btnPrimary}
          style={{ width: '100%' }}
          disabled={saving}
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
