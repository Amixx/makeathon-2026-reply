import { useState } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'framer-motion';
import { ProgressDots, SectionLabel, VoiceOrb } from '../../components/ui';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { postProfile } from '../../lib/agent';
import { transcribeAudio } from '../../lib/voice';
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

export default function Blockers() {
  const navigate = useNavigate();
  const setField = useOnboarding((st) => st.setField);
  const blockers = useOnboarding((st) => st.blockers);

  const [activePresets, setActivePresets] = useState<Set<string>>(new Set());

  const { listening, start, stop } = useVoiceRecorder();
  const [transcribing, setTranscribing] = useState(false);
  const [saving, setSaving] = useState(false);

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

  async function handleOrbClick() {
    if (listening) {
      setTranscribing(true);
      const blob = await stop();
      if (blob) {
        try {
          const result = await transcribeAudio(blob);
          if (result.text) setField('blockers', result.text);
          if (result.fields.blockers) setField('blockers', result.fields.blockers);
        } catch {
          // stub — ignore
        }
      }
      setTranscribing(false);
    } else {
      await start();
    }
  }

  async function handleContinue() {
    if (listening) await handleOrbClick();
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
          <SectionLabel pulsing={listening}>
            {listening ? 'LISTENING…' : 'WOOP · OBSTACLE'}
          </SectionLabel>
          <h2 className={s.qTitle}>What's the part that feels heaviest?</h2>
          <p className={s.qSub}>Speak what's there. We'll pick out the weight — no scoring.</p>
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

        <div className={s.spacer} />

        <button
          className={s.btnPrimary}
          style={{ width: '100%' }}
          disabled={saving}
          onClick={handleContinue}
        >
          {saving ? 'Saving…' : listening ? 'Stop & continue' : 'Continue'}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
