import { useCallback, useRef, useState } from 'react';
import { config } from '../lib/config';
import type { DiscoverItem, AgentEvent } from '../lib/types';
import type { PillVariant } from '../components/ui/Pill';
import type { BulletStatus } from '../components/ui/AgentCard';

export type AgentId =
  | 'study'
  | 'career'
  | 'university'
  | 'scholarship';

export type SwarmAgent = {
  id: AgentId;
  name: string;
  emoji: string;
  status: PillVariant;
  bullets: { text: string; status: BulletStatus }[];
};

const AGENT_DEFAULTS: SwarmAgent[] = [
  {
    id: 'study',
    name: 'Study Buddy',
    emoji: '🛰️',
    status: 'working',
    bullets: [
      { text: 'Scanning TUM module catalogue…', status: 'queued' },
      { text: 'Matching with your program & interests…', status: 'queued' },
      { text: 'Checking enrollment windows…', status: 'queued' },
    ],
  },
  {
    id: 'career',
    name: 'Career Agent',
    emoji: '💼',
    status: 'working',
    bullets: [
      { text: 'Scanning recent open roles & PRs…', status: 'queued' },
      { text: 'Filtering matches to your profile…', status: 'queued' },
      { text: 'Drafting outreach copy…', status: 'queued' },
    ],
  },
  {
    id: 'university',
    name: 'University Nav',
    emoji: '🏛️',
    status: 'working',
    bullets: [
      { text: 'Looking up campus resources…', status: 'queued' },
      { text: 'Pulling room & mensa data…', status: 'queued' },
      { text: 'Composing intro email…', status: 'queued' },
    ],
  },
  {
    id: 'scholarship',
    name: 'Scholarship',
    emoji: '🎓',
    status: 'working',
    bullets: [
      { text: 'Matching criteria for funded positions…', status: 'queued' },
      { text: 'Drafting motivation letter…', status: 'queued' },
      { text: 'Flagging deadlines…', status: 'queued' },
    ],
  },
];

function freshAgents(): SwarmAgent[] {
  return AGENT_DEFAULTS.map((a) => ({
    ...a,
    bullets: a.bullets.map((b) => ({ ...b })),
  }));
}

function extractJsonArray(text: string): unknown {
  const start = text.indexOf('[');
  const end = text.lastIndexOf(']');
  if (start < 0 || end <= start) return null;
  try { return JSON.parse(text.slice(start, end + 1)); } catch { return null; }
}

function normalizeItems(raw: unknown): DiscoverItem[] {
  if (!Array.isArray(raw)) return [];
  const validTypes = ['course', 'event', 'person', 'scholarship'] as const;
  return raw
    .map((e, idx) => {
      if (!e || typeof e !== 'object') return null;
      const entry = e as Record<string, unknown>;
      const title = typeof entry.title === 'string' ? entry.title.trim() : '';
      if (!title) return null;
      const why = typeof entry.why === 'string' ? entry.why.trim() : '';
      const id = typeof entry.id === 'string' && entry.id.trim() ? entry.id.trim() : `item-${idx}`;
      const rawType = typeof entry.type === 'string' ? entry.type : '';
      const type: DiscoverItem['type'] =
        (validTypes as readonly string[]).includes(rawType)
          ? (rawType as DiscoverItem['type'])
          : 'course';
      const meta: DiscoverItem['meta'] =
        entry.meta && typeof entry.meta === 'object' && !Array.isArray(entry.meta)
          ? (entry.meta as DiscoverItem['meta'])
          : {};
      return { id, title, why, type, meta };
    })
    .filter((x): x is DiscoverItem => x !== null);
}

function itemToAgentId(item: DiscoverItem): AgentId {
  switch (item.type) {
    case 'course':
      return 'study';
    case 'person':
      return 'career';
    case 'event':
      return 'university';
    case 'scholarship':
      return 'scholarship';
    default:
      return 'study';
  }
}

function buildAgentsFromItems(items: DiscoverItem[]): SwarmAgent[] {
  const grouped = new Map<AgentId, DiscoverItem[]>();
  for (const item of items) {
    const agentId = itemToAgentId(item);
    const existing = grouped.get(agentId) ?? [];
    existing.push(item);
    grouped.set(agentId, existing);
  }

  return freshAgents().map((agent) => {
    const matched = grouped.get(agent.id) ?? [];
    if (matched.length === 0) {
      return {
        ...agent,
        status: 'scheduled',
        bullets: [{ text: 'No matching opportunities in this pass', status: 'done' }],
      };
    }

    return {
      ...agent,
      status: 'ready',
      bullets: matched.slice(0, 3).map((item) => ({
        text: JSON.stringify(
          {
            id: item.id,
            title: item.title,
            why: item.why,
            type: item.type,
            meta: item.meta,
          },
          null,
          2,
        ),
        status: 'done' as BulletStatus,
      })),
    };
  });
}

export function useSwarm() {
  const [agents, setAgents] = useState<SwarmAgent[]>(freshAgents);
  const [items, setItems] = useState<DiscoverItem[]>([]);
  const [discoveryDraft, setDiscoveryDraft] = useState('');
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback((params: { program?: string; interest?: string }) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setAgents(freshAgents());
    setItems([]);
    setDiscoveryDraft('');
    setIsDiscovering(true);
    setDone(false);
    setError(null);

    const endpoint = `${config.agentUrl.replace(/\/+$/, '')}/agent/discover`;

    fetch(endpoint, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        program: params.program ?? null,
        interest: params.interest ?? null,
      }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text().catch(() => res.statusText);
          if (!controller.signal.aborted) setError(`${res.status}: ${text}`);
          return;
        }
        if (!res.body) {
          if (!controller.signal.aborted) setError('No response body');
          return;
        }

        const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
        let buf = '';
        let fullText = '';

        while (true) {
          const { done: rdone, value } = await reader.read();
          if (rdone) break;
          buf += value;
          let idx = buf.indexOf('\n');
          while (idx >= 0) {
            const line = buf.slice(0, idx).trim();
            buf = buf.slice(idx + 1);
            if (line) {
              try {
                const ev = JSON.parse(line) as AgentEvent;
                switch (ev.type) {
                  case 'text':
                    fullText += ev.delta;
                    setDiscoveryDraft(fullText);
                    break;
                  case 'error':
                    if (!controller.signal.aborted) setError(ev.message);
                    break;
                  case 'done':
                    // handled after loop
                    break;
                }
              } catch {
                // malformed line — ignore
              }
            }
            idx = buf.indexOf('\n');
          }
        }

        if (controller.signal.aborted) return;

        // Parse items from accumulated text
        const parsed = normalizeItems(extractJsonArray(fullText));
        if (parsed.length > 0) {
          setItems(parsed);
          setAgents(buildAgentsFromItems(parsed));
        }
        if (parsed.length > 0) {
          setDiscoveryDraft(JSON.stringify(parsed, null, 2));
        }
        setIsDiscovering(false);
        setDone(true);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setIsDiscovering(false);
        setError(err instanceof Error ? err.message : String(err));
      });
  }, []);

  return {
    agents,
    items,
    discoveryDraft,
    isDiscovering,
    discoveryReady: items.length > 0,
    done,
    error,
    start,
  };
}
