import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router";
import { clearProfile, resetDemoProfile } from "../lib/agent";
import { useOnboarding } from "../store/onboarding";
import styles from "./Landing.module.css";

function fadeUp(delay: number) {
  return {
    initial: { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: { delay, duration: 0.5, ease: "easeOut" as const },
  };
}

export default function Landing() {
  const navigate = useNavigate();
  const reset = useOnboarding((state) => state.reset);
  const hydrate = useOnboarding((state) => state.hydrate);
  const [loadingDemo, setLoadingDemo] = useState(false);

  function handleStart() {
    reset();
    clearProfile().catch(() => {});
    navigate("/onboarding/vision");
  }

  async function handleDemo() {
    setLoadingDemo(true);
    try {
      const bootstrap = await resetDemoProfile();
      hydrate(bootstrap.profile);
      navigate("/onboarding/vision");
    } catch {
      // fall back to fresh start
      navigate("/onboarding/vision");
    } finally {
      setLoadingDemo(false);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.top}>
          <motion.div {...fadeUp(0)} className={styles.logo}>
            <span className={styles.mark} />
            WayTum
          </motion.div>

          <motion.div {...fadeUp(0.12)}>
            <span className={styles.betaPill}>BETA · TUM CAREER SERVICES</span>
          </motion.div>

          <motion.h1 {...fadeUp(0.24)} className={styles.heroTitle}>
            Who do you want to become?
          </motion.h1>

          <motion.p {...fadeUp(0.36)} className={styles.heroSub}>
            One minute is enough. We listen, the agents act. You review what
            they did.
          </motion.p>
        </div>

        <div className={styles.spacer} />

        <motion.div {...fadeUp(0.48)} className={styles.ctaGroup}>
          <button className={styles.ctaBtn} onClick={handleStart}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
            Tell us your goals
          </button>
          <button
            className={styles.ctaBtnGhost}
            onClick={handleDemo}
            disabled={loadingDemo}
          >
            {loadingDemo ? "Loading…" : "✨ Use sample demo data"}
          </button>
          <a className={styles.docsLink} href="/mcp/docs">
            Read the MCP docs
          </a>
        </motion.div>

        <motion.p {...fadeUp(0.6)} className={styles.footerCaption}>
          No right answer · No lock-in · 6-month experiment
        </motion.p>
      </div>
    </div>
  );
}
