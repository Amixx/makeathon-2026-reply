import { useState } from 'react';
import {
  AgentCard,
  Button,
  Card,
  InputRow,
  MiniInput,
  Pill,
  ProgressDots,
  SectionLabel,
  SwipeStack,
  TypingText,
  UploadDrop,
  VoiceOrb,
} from '../components/ui';

const section: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
  marginBottom: 40,
};
const heading: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: 2,
  textTransform: 'uppercase',
  color: 'var(--fg-muted)',
  paddingBottom: 4,
  borderBottom: '1px solid var(--border-default)',
};
const row: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 10,
  alignItems: 'center',
};

const SWIPE_ITEMS = [
  { id: 1, title: 'Python for ML', org: 'TUM' },
  { id: 2, title: 'Reply Internship', org: 'Reply' },
  { id: 3, title: 'DAAD Scholarship', org: 'DAAD' },
];

export default function Playground() {
  const [pwValue, setPwValue] = useState('');
  const [textValue, setTextValue] = useState('');
  const [listening, setListening] = useState(false);
  const [dots, setDots] = useState(2);
  const [swipeLog, setSwipeLog] = useState<string[]>([]);

  return (
    <div
      style={{
        maxWidth: 720,
        margin: '0 auto',
        padding: '40px 24px 80px',
        fontFamily: 'var(--font-body)',
      }}
    >
      <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4, letterSpacing: -0.8 }}>
        UI Playground
      </h1>
      <p style={{ fontSize: 14, color: 'var(--fg-muted)', marginBottom: 40 }}>
        Visual QA for all reusable components.
      </p>

      {/* ── Buttons ─────────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Buttons</div>
        <div style={row}>
          <Button variant="primary">Primary</Button>
          <Button variant="accent">Accent</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="outline">Outline</Button>
        </div>
        <div style={row}>
          <Button variant="primary" size="sm">Small</Button>
          <Button variant="accent" size="lg">Large</Button>
          <Button variant="primary" disabled>Disabled</Button>
        </div>
      </section>

      {/* ── Pills ─────────────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Pills</div>
        <div style={row}>
          {(
            [
              'accent', 'course', 'event', 'person', 'scholar', 'success', 'dark',
              'draft', 'sent', 'pending', 'working', 'drafting', 'writing', 'scheduled', 'ready',
            ] as const
          ).map((v) => (
            <Pill key={v} variant={v}>{v}</Pill>
          ))}
        </div>
      </section>

      {/* ── Cards ─────────────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Cards</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: 12 }}>
          <Card variant="default"><div style={{ fontSize: 14 }}>Default card</div></Card>
          <Card variant="muted"><div style={{ fontSize: 14 }}>Muted card</div></Card>
          <Card variant="dark"><div style={{ fontSize: 14, color: 'var(--fg-inverted)' }}>Dark card</div></Card>
          <Card variant="accent"><div style={{ fontSize: 14 }}>Accent card</div></Card>
          <Card variant="success-border"><div style={{ fontSize: 14 }}>Success border</div></Card>
        </div>
      </section>

      {/* ── Progress Dots ─────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Progress Dots</div>
        <div style={row}>
          <ProgressDots total={5} current={dots} />
          <Button variant="ghost" size="sm" onClick={() => setDots((d) => (d + 1) % 6)}>
            Advance
          </Button>
        </div>
        <div style={row}>
          <ProgressDots total={3} current={0} />
          <ProgressDots total={3} current={1} />
          <ProgressDots total={3} current={2} />
        </div>
      </section>

      {/* ── Section Labels ─────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Section Labels</div>
        <div style={row}>
          <SectionLabel>Opportunities</SectionLabel>
          <SectionLabel pulsing>Live agents</SectionLabel>
          <SectionLabel muted>Archived</SectionLabel>
        </div>
      </section>

      {/* ── Voice Orb ─────────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Voice Orb</div>
        <div style={row}>
          <VoiceOrb listening={listening} onClick={() => setListening((l) => !l)} />
          <span style={{ fontSize: 13, color: 'var(--fg-muted)' }}>
            {listening ? 'Listening…' : 'Click to toggle'}
          </span>
        </div>
      </section>

      {/* ── Typing Text ──────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Typing Text</div>
        <Card variant="muted" tight>
          <p style={{ fontSize: 16, lineHeight: 1.6 }}>
            <TypingText
              text="Hey! I'm WayTum. Let's figure out where you want to go."
              speed={40}
            />
          </p>
        </Card>
      </section>

      {/* ── Agent Cards ──────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Agent Cards</div>
        <AgentCard
          index={0}
          name="Course Scout"
          emoji="📚"
          status="success"
          bullets={[
            { text: 'Found 3 matching electives', status: 'done' },
            { text: 'Ranked by match score', status: 'done' },
          ]}

        />
        <AgentCard
          index={1}
          name="Application Agent"
          emoji="✍️"
          status="working"
          bullets={[
            { text: 'Drafted cover letter', status: 'done' },
            { text: 'Filling application form…', status: 'running' },
            { text: 'Submit final PDF', status: 'queued' },
          ]}
        />
        <AgentCard
          index={2}
          name="Scholarship Finder"
          emoji="🎓"
          status="pending"
          bullets={[
            { text: 'Waiting for deadline window', status: 'queued' },
            { text: 'Missing transcript', status: 'alert' },
          ]}
        />
      </section>

      {/* ── Swipe Stack ──────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Swipe Stack</div>
        <div style={{ height: 280, position: 'relative' }}>
          <SwipeStack
            items={SWIPE_ITEMS}
            renderCard={(item) => (
              <div>
                <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: -0.5, marginBottom: 6 }}>
                  {item.title}
                </div>
                <div style={{ fontSize: 13, color: 'var(--fg-muted)' }}>{item.org}</div>
              </div>
            )}
            onAccept={(item) => setSwipeLog((l) => [`✓ ${item.title}`, ...l])}
            onSkip={(item) => setSwipeLog((l) => [`✗ ${item.title}`, ...l])}
          />
        </div>
        {swipeLog.length > 0 && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: 1, color: 'var(--fg-muted)' }}>
            {swipeLog.map((s, i) => <div key={i}>{s}</div>)}
          </div>
        )}
      </section>

      {/* ── Input Row ─────────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Input Row</div>
        <InputRow label="Target role" value="Software Engineer" />
        <InputRow label="Target company" placeholder="e.g. Reply" selected />
        <InputRow label="Graduation year" value="2026" action="Edit" onAction={() => {}} required />
      </section>

      {/* ── Mini Input ─────────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Mini Input</div>
        <MiniInput value={textValue} onChange={setTextValue} placeholder="Your TUM email" type="email" />
        <MiniInput value={pwValue} onChange={setPwValue} placeholder="Password" type="password" />
      </section>

      {/* ── Upload Drop ─────────────────────────────────────────── */}
      <section style={section}>
        <div style={heading}>Upload Drop</div>
        <UploadDrop
          label="Drop your CV here, or click to browse"
          accept=".pdf,.doc,.docx"
          onFile={(f) => alert(`File selected: ${f.name}`)}
        />
      </section>
    </div>
  );
}
