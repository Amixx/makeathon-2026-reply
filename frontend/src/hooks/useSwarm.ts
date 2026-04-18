import { useCallback, useRef, useState } from 'react';
import { config } from '../lib/config';
import { extractJsonArray, normalizeItems } from '../lib/agent';
import type { DiscoverItem, AgentEvent, ToolCall } from '../lib/types';
import type { PillVariant } from '../components/ui/Pill';
import type { BulletStatus } from '../components/ui/AgentCard';

export type AgentId = 'study' | 'career' | 'university' | 'scholarship';

type AgentCategory = 'course' | 'event' | 'person' | 'scholarship';

export type SwarmAgent = {
  id: AgentId;
  name: string;
  emoji: string;
  category: AgentCategory;
  status: PillVariant;
  bullets: { text: string; status: BulletStatus }[];
  toolCalls: ToolCall[];
  items: DiscoverItem[];
};

const AGENT_CONFIGS: Omit<SwarmAgent, 'status' | 'bullets' | 'toolCalls' | 'items'>[] = [
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
                    }));
                    break;
                  case 'error':
                    updateAgent(agentId, (a) => ({
                      ...a,
                      status: 'scheduled',
                      bullets: [...a.bullets, { text: ev.message, status: 'alert' }],
                    }));
                    break;
                  case 'done':
                    break;
                }
              } catch {
                // malformed line
              }
            }
            idx = buf.indexOf('\n');
          }
        }

        if (controller.signal.aborted) return;

        // Parse final items
        const parsed = normalizeItems(extractJsonArray(fullText));
        updateAgent(agentId, (a) => ({
          ...a,
          status: 'ready',
          items: parsed,
          bullets:
            parsed.length > 0
              ? parsed.slice(0, 3).map((item) => ({
                  text: item.title,
                  status: 'done' as BulletStatus,
                }))
              : [{ text: 'No opportunities found', status: 'queued' as BulletStatus }],
        }));
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
