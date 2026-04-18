import { config } from "./config";
import { buildSystemPrompt } from "./systemPrompt";
import type { AgentEvent, ChatRole, DiscoverItem } from "./types";

export type AgentCallbacks = {
  onTextDelta: (delta: string) => void;
  onToolStart: (id: string, name: string, input: unknown) => void;
  onToolResult: (id: string, content: string, isError: boolean) => void;
  onError: (message: string) => void;
  onDone: () => void;
};

export type AgentHistoryEntry = { role: ChatRole; content: string };

function chatEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/chat`;
}

function discoverEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/discover`;
}

function planEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/plan`;
}

export type DiscoverOptions = {
  program?: string;
  interest?: string;
};

export type DiscoverCallbacks = {
  onTextDelta?: (delta: string) => void;
  onItems: (items: DiscoverItem[]) => void;
  onError: (message: string) => void;
  onDone: () => void;
};

function extractJsonArray(text: string): unknown {
  const start = text.indexOf("[");
  const end = text.lastIndexOf("]");
  if (start < 0 || end <= start) return null;
  const slice = text.slice(start, end + 1);
  try {
    return JSON.parse(slice);
  } catch {
    return null;
  }
}

function normalizeItems(raw: unknown): DiscoverItem[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((entry, idx) => {
      if (!entry || typeof entry !== "object") return null;
      const e = entry as Record<string, unknown>;
      const title = typeof e.title === "string" ? e.title.trim() : "";
      if (!title) return null;
      const why = typeof e.why === "string" ? e.why.trim() : "";
      const id =
        typeof e.id === "string" && e.id.trim().length > 0
          ? e.id.trim()
          : `item-${idx}`;
      return { id, title, why };
    })
    .filter((x): x is DiscoverItem => x !== null);
}

export async function runDiscover(
  options: DiscoverOptions,
  callbacks: DiscoverCallbacks,
  signal: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(discoverEndpoint(), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        program: options.program ?? null,
        interest: options.interest ?? null,
      }),
      signal,
    });
  } catch (err) {
    if (signal.aborted) return;
    callbacks.onError(err instanceof Error ? err.message : String(err));
    return;
  }

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    callbacks.onError(`${response.status}: ${text}`);
    return;
  }
  if (!response.body) {
    callbacks.onError("No response body from agent backend");
    return;
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let fullText = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;
      let newlineIdx = buffer.indexOf("\n");
      while (newlineIdx >= 0) {
        const line = buffer.slice(0, newlineIdx).trim();
        buffer = buffer.slice(newlineIdx + 1);
        if (line.length > 0) {
          try {
            const event = JSON.parse(line) as AgentEvent;
            if (event.type === "text") {
              fullText += event.delta;
              callbacks.onTextDelta?.(event.delta);
            } else if (event.type === "error") {
              callbacks.onError(event.message);
            }
          } catch {
            // malformed line — ignore
          }
        }
        newlineIdx = buffer.indexOf("\n");
      }
    }
  } catch (err) {
    if (!signal.aborted) {
      callbacks.onError(err instanceof Error ? err.message : String(err));
    }
    return;
  }

  const items = normalizeItems(extractJsonArray(fullText));
  if (items.length === 0) {
    callbacks.onError("Could not parse items from agent response.");
    return;
  }
  callbacks.onItems(items);
  callbacks.onDone();
}

export type PlanCallbacks = {
  onTextDelta: (delta: string) => void;
  onToolStart: (id: string, name: string, input: unknown) => void;
  onToolResult: (id: string, content: string, isError: boolean) => void;
  onError: (message: string) => void;
  onDone: () => void;
};

export async function runPlan(
  item: DiscoverItem,
  options: DiscoverOptions,
  callbacks: PlanCallbacks,
  signal: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(planEndpoint(), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        item,
        program: options.program ?? null,
        interest: options.interest ?? null,
      }),
      signal,
    });
  } catch (err) {
    if (signal.aborted) return;
    callbacks.onError(err instanceof Error ? err.message : String(err));
    return;
  }

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    callbacks.onError(`${response.status}: ${text}`);
    return;
  }
  if (!response.body) {
    callbacks.onError("No response body from agent backend");
    return;
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let doneEmitted = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;
      let newlineIdx = buffer.indexOf("\n");
      while (newlineIdx >= 0) {
        const line = buffer.slice(0, newlineIdx).trim();
        buffer = buffer.slice(newlineIdx + 1);
        if (line.length > 0) {
          try {
            const event = JSON.parse(line) as AgentEvent;
            switch (event.type) {
              case "text":
                callbacks.onTextDelta(event.delta);
                break;
              case "tool_start":
                callbacks.onToolStart(event.id, event.name, event.input);
                break;
              case "tool_result":
                callbacks.onToolResult(event.id, event.content, event.isError);
                break;
              case "error":
                callbacks.onError(event.message);
                break;
              case "done":
                doneEmitted = true;
                callbacks.onDone();
                break;
            }
          } catch {
            // malformed line — ignore
          }
        }
        newlineIdx = buffer.indexOf("\n");
      }
    }
  } catch (err) {
    if (!signal.aborted) {
      callbacks.onError(err instanceof Error ? err.message : String(err));
    }
    return;
  }

  if (!doneEmitted && !signal.aborted) callbacks.onDone();
}

function dispatch(event: AgentEvent, cb: AgentCallbacks): void {
  switch (event.type) {
    case "text":
      cb.onTextDelta(event.delta);
      break;
    case "tool_start":
      cb.onToolStart(event.id, event.name, event.input);
      break;
    case "tool_result":
      cb.onToolResult(event.id, event.content, event.isError);
      break;
    case "error":
      cb.onError(event.message);
      break;
    case "done":
      cb.onDone();
      break;
  }
}

export async function runAgent(
  history: AgentHistoryEntry[],
  callbacks: AgentCallbacks,
  signal: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(chatEndpoint(), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        messages: history,
        system: buildSystemPrompt(),
      }),
      signal,
    });
  } catch (err) {
    if (signal.aborted) return;
    callbacks.onError(err instanceof Error ? err.message : String(err));
    return;
  }

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    callbacks.onError(`${response.status}: ${text}`);
    return;
  }
  if (!response.body) {
    callbacks.onError("No response body from agent backend");
    return;
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let doneEmitted = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;
      let newlineIdx = buffer.indexOf("\n");
      while (newlineIdx >= 0) {
        const line = buffer.slice(0, newlineIdx).trim();
        buffer = buffer.slice(newlineIdx + 1);
        if (line.length > 0) {
          try {
            const event = JSON.parse(line) as AgentEvent;
            if (event.type === "done") doneEmitted = true;
            dispatch(event, callbacks);
          } catch {
            // malformed line — ignore
          }
        }
        newlineIdx = buffer.indexOf("\n");
      }
    }
  } catch (err) {
    if (!signal.aborted) {
      callbacks.onError(err instanceof Error ? err.message : String(err));
    }
    return;
  }

  if (!doneEmitted && !signal.aborted) {
    callbacks.onDone();
  }
}
