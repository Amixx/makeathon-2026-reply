import { useState } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'framer-motion';
import { ProgressDots, SectionLabel, MiniInput, UploadDrop } from '../../components/ui';
import { connectTumAccount, postProfile, uploadCv } from '../../lib/agent';
import { useOnboarding } from '../../store/onboarding';
import s from './onboarding.module.css';

function fadeUp(delay: number) {
  return {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    transition: { delay, duration: 0.4, ease: 'easeOut' as const },
  };
}

export default function Ground() {
  const navigate = useNavigate();
  const setField = useOnboarding((st) => st.setField);

  const tumSsoId = useOnboarding((st) => st.tumSsoId);
  const tumPassword = useOnboarding((st) => st.tumPassword);
  const tumSsoConnected = useOnboarding((st) => st.tumSsoConnected);
  const cvFileName = useOnboarding((st) => st.cvFileName);
  const githubUrl = useOnboarding((st) => st.githubUrl);
  const linkedinUrl = useOnboarding((st) => st.linkedinUrl);

  const [connecting, setConnecting] = useState(false);
  const [uploadingCv, setUploadingCv] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tumError, setTumError] = useState<string | null>(null);
  const [cvError, setCvError] = useState<string | null>(null);

  async function handleConnect() {
    if (!tumSsoId.trim() || !tumPassword.trim()) {
      setTumError('Enter your TUM ID and password.');
      return;
    }
    setTumError(null);
    setConnecting(true);
    try {
      const profile = await connectTumAccount({ tumSsoId, password: tumPassword });
      setField('tumSsoId', profile.tumSsoId ?? tumSsoId);
      setField('tumSsoConnected', profile.tumSsoConnected ?? true);
    } catch (error) {
      setTumError(error instanceof Error ? error.message : 'Could not connect right now.');
    } finally {
      setConnecting(false);
    }
  }

  async function handleCvFile(file: File) {
    setCvError(null);
    setUploadingCv(true);
    try {
      const profile = await uploadCv(file);
      setField('cvFileName', profile.cvFileName ?? file.name);
    } catch (error) {
      setCvError(error instanceof Error ? error.message : 'Could not upload the file.');
    } finally {
      setUploadingCv(false);
    }
  }

  async function handleContinue() {
    setSaving(true);
    try {
      await postProfile({

        githubUrl,
        linkedinUrl,
        cvFileName,
        tumSsoId,
        tumSsoConnected,
      });
    } catch {
      // local state remains the source of truth when backend is unavailable
    } finally {
      setSaving(false);
    }
    navigate('/onboarding/commitment');
  }

  const canContinue = tumSsoConnected;

  return (
    <div className={s.page}>
      <div className={s.inner} style={{ overflowY: 'auto' }}>
        {/* Top nav */}
        <div className={s.topNav}>
          <button className={s.backBtn} onClick={() => navigate('/onboarding/blockers')} aria-label="Back">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <div className={s.dotsWrap}>
            <ProgressDots total={4} current={2} />
          </div>
          <span className={s.counter}>03 / 04</span>
        </div>

        {/* Heading */}
        <div className={s.heading}>
          <SectionLabel>GROUND ME</SectionLabel>
          <h2 className={s.qTitle}>Sharper suggestions.</h2>
        </div>

        <span className={s.sectionHead}>REQUIRED</span>


        {/* TUM SSO */}
        <motion.div {...fadeUp(0.1)} className={s.groupCard}>
          <div className={s.groupHead}>
            <div className={s.groupIcon}>🎓</div>
            <div className={s.groupInfo}>
              <div className={s.groupTitle}>TUM SSO login · required</div>
              <div className={s.groupSub}>Enter your TUM login and password</div>
            </div>
            {tumSsoConnected && (
              <span className={s.successBadge}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Logged in
              </span>
            )}
          </div>
          <div className={s.fieldGroup}>
            <div>
              <span className={s.fieldLabel}>TUM ID · REQUIRED</span>
              <MiniInput
                value={tumSsoId}
                onChange={(v) => setField('tumSsoId', v)}
                placeholder="ga12xyz"
                autoComplete="username"
              />
            </div>
            <div>
              <span className={s.fieldLabel}>PASSWORD · REQUIRED</span>
              <MiniInput
                value={tumPassword}
                onChange={(v) => setField('tumPassword', v)}
                placeholder="••••••••"
                type="password"
                autoComplete="current-password"
              />
            </div>
            <button
              className={s.connectBtn}
              onClick={handleConnect}
              disabled={connecting}
              style={{ alignSelf: 'flex-end' }}
            >
              {connecting ? 'Logging in…' : tumSsoConnected ? 'Log in again' : 'Log in'}
            </button>
          </div>
          {tumError && <p className={s.inlineError}>{tumError}</p>}
        </motion.div>

        {/* CV Upload */}
        <motion.div {...fadeUp(0.2)} className={s.groupCard}>
          <div className={s.groupHead}>
            <div className={s.groupIcon}>📄</div>
            <div className={s.groupInfo}>
              <div className={s.groupTitle}>Your CV</div>
              <div className={s.groupSub}>PDF or DOCX · we'll read it after you continue</div>
            </div>
            {cvFileName && (
              <span className={s.successBadge}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Loaded
              </span>
            )}
          </div>
          {cvFileName ? (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--fg-inverted-muted)', wordBreak: 'break-all' }}>
              {cvFileName}
            </div>
          ) : (
            <UploadDrop
              label={uploadingCv ? 'Uploading…' : 'Drop a file or tap to browse'}
              onFile={handleCvFile}
              accept=".pdf,.doc,.docx"
            />
          )}
          {cvError && <p className={s.inlineError}>{cvError}</p>}
        </motion.div>

        <span className={s.sectionHeadOptional}>OPTIONAL · LINK TO YOURSELF</span>

        {/* GitHub */}
        <motion.div {...fadeUp(0.3)} className={s.optCard}>
          <div className={s.optHead}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.218.694.825.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12" />
            </svg>
            GitHub
            <span className={s.optTag}>optional</span>
          </div>
          <MiniInput
            value={githubUrl}
            onChange={(v) => setField('githubUrl', v)}
            placeholder="github.com/yourhandle"
          />
        </motion.div>

        {/* LinkedIn */}
        <motion.div {...fadeUp(0.4)} className={s.optCard}>
          <div className={s.optHead}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            LinkedIn
            <span className={s.optTag}>optional</span>
          </div>
          <MiniInput
            value={linkedinUrl}
            onChange={(v) => setField('linkedinUrl', v)}
            placeholder="Paste LinkedIn URL"
          />
        </motion.div>

        {/* CTA */}
        <motion.button
          {...fadeUp(0.5)}
          className={s.btnPrimary}
          style={{ width: '100%', marginTop: '8px' }}
          disabled={!canContinue || saving}
          onClick={handleContinue}
        >
          {saving ? 'Saving…' : 'Continue — work with what we have'}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </motion.button>
      </div>
    </div>
  );
}
