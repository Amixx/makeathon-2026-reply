import { useCallback, useRef, useState } from 'react';
import { config } from '../lib/config';
import { normalizeItems } from '../lib/agent';
import type { DiscoverItem, AgentEvent, ToolCall } from '../lib/types';
import type { PillVariant } from '../components/ui/Pill';
import type { BulletStatus } from '../components/ui/AgentCard';

export type AgentId = 'study' | 'career' | 'university' | 'scholarship';

type AgentCategory = 'course' | 'event' | 'person' | 'scholarship';

export type StreamEntry =
  | { kind: 'text'; content: string }
  | { kind: 'tool_start'; id: string; name: string }
  | { kind: 'tool_done'; id: string; name: string; error?: boolean };

export type SwarmAgent = {
  id: AgentId;
  name: string;
  emoji: string;
  category: AgentCategory;
  status: PillVariant;
  bullets: { text: string; status: BulletStatus }[];
  toolCalls: ToolCall[];
  items: DiscoverItem[];
  streamLog: StreamEntry[];
  summary: string;
};

const AGENT_CONFIGS: Omit<SwarmAgent, 'status' | 'bullets' | 'toolCalls' | 'items' | 'streamLog' | 'summary'>[] = [
  { id: 'study', name: 'Study Buddy', emoji: '🛰️', category: 'course' },
  { id: 'career', name: 'Career Agent', emoji: '💼', category: 'person' },
  { id: 'university', name: 'University Nav', emoji: '🏛️', category: 'event' },
  { id: 'scholarship', name: 'Scholarship', emoji: '🎓', category: 'scholarship' },
];

function freshAgents(): SwarmAgent[] {
  return AGENT_CONFIGS.map((a) => ({
    ...a,
    status: 'working' as PillVariant,
    bullets: [{ text: 'Starting up…', status: 'queued' as BulletStatus }],
    toolCalls: [],
    items: [],
    streamLog: [],
    summary: '',
  }));
}

export function useSwarm() {
  const [agents, setAgents] = useState<SwarmAgent[]>(freshAgents);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback((params: { program?: string; interest?: string }) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setAgents(freshAgents());

    setIsDiscovering(true);
    setDone(false);
    setError(null);

    const endpoint = `${config.agentUrl.replace(/\/+$/, '')}/agent/discover`;

    // Helper: update a single agent by id
    const updateAgent = (agentId: AgentId, updater: (agent: SwarmAgent) => SwarmAgent) => {
      setAgents((prev) => prev.map((a) => (a.id === agentId ? updater(a) : a)));
    };

    // Run a single agent stream for a given category
    async function runAgent(agentId: AgentId, category: AgentCategory) {
      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            program: params.program ?? null,
            interest: params.interest ?? null,
            category,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          const text = await res.text().catch(() => res.statusText);
          if (!controller.signal.aborted) {
            updateAgent(agentId, (a) => ({
              ...a,
              status: 'scheduled',
              bullets: [{ text: `Error: ${text}`, status: 'alert' }],
            }));
          }
          return;
        }

        if (!res.body) return;

        const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
        let buf = '';

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
                    updateAgent(agentId, (a) => {
                      const last = a.streamLog[a.streamLog.length - 1];
                      if (last && last.kind === 'text') {
                        const updated = [...a.streamLog];
                        updated[updated.length - 1] = { kind: 'text', content: last.content + ev.delta };
                        return { ...a, streamLog: updated };
                      }
                      return { ...a, streamLog: [...a.streamLog, { kind: 'text', content: ev.delta }] };
                    });
                    break;
                  case 'tool_start':
                    updateAgent(agentId, (a) => ({
                      ...a,
                      bullets: [
                        ...a.bullets.filter((b) => b.status === 'done'),
                        { text: `Using ${ev.name}…`, status: 'running' },
                      ],
                      toolCalls: [
                        ...a.toolCalls,
                        { id: ev.id, toolName: ev.name, input: ev.input, status: 'running' },
                      ],
                      streamLog: [...a.streamLog, { kind: 'tool_start', id: ev.id, name: ev.name }],
                    }));
                    break;
                  case 'tool_result':
                    updateAgent(agentId, (a) => ({
                      ...a,
                      bullets: a.bullets.map((b) =>
                        b.status === 'running' ? { ...b, status: 'done' } : b,
                      ),
                      toolCalls: a.toolCalls.map((tc) =>
                        tc.id === ev.id
                          ? { ...tc, status: ev.isError ? 'error' : 'done', result: ev.content }
                          : tc,
                      ),
                      streamLog: a.streamLog.map((e) =>
                        e.kind === 'tool_start' && e.id === ev.id
                          ? { kind: 'tool_done' as const, id: ev.id, name: e.name, error: ev.isError }
                          : e,
                      ),
                    }));
                    break;
                  case 'error':
                    updateAgent(agentId, (a) => ({
                      ...a,
                      status: 'scheduled',
                      bullets: [...a.bullets, { text: ev.message, status: 'alert' }],
                    }));
                    break;
                  case 'done': {
                    const parsed = ev.items && Array.isArray(ev.items) ? normalizeItems(ev.items) : [];
                    updateAgent(agentId, (a) => ({
                      ...a,
                      status: 'ready',
                      items: parsed,
                      summary: ev.summary ?? '',
                    }));
                    break;
                  }
                }
              } catch {
                // malformed line
              }
            }
            idx = buf.indexOf('\n');
          }
        }

        if (controller.signal.aborted) return;

        // Mark as ready if the done event didn't already do it
        updateAgent(agentId, (a) => {
          if (a.status === 'ready') return a;
          return { ...a, status: 'ready' };
        });
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        updateAgent(agentId, (a) => ({
          ...a,
          status: 'scheduled',
          bullets: [
            { text: err instanceof Error ? err.message : String(err), status: 'alert' },
          ],
        }));
      }
    }

    // Fire all 4 in parallel
    const promises = AGENT_CONFIGS.map((a) => runAgent(a.id, a.category));

    Promise.all(promises).then(() => {
      if (!controller.signal.aborted) {
        setIsDiscovering(false);
        setDone(true);
      }
    });
  }, []);

  // Flatten all items from all agents
  const items = agents.flatMap((a) => a.items);

  return {
    agents,
    items,
    isDiscovering,
    done,
    error,
    start,
  };
}
