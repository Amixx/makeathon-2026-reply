import { config } from "./config";
import { buildSystemPrompt } from "./systemPrompt";
import type { AgentEvent, ChatRole, DiscoverItem, Profile } from "./types";

function profileEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/profile`;
}

function demoResetEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/profile/demo-reset`;
}


async function readErrorMessage(res: Response): Promise<string> {
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const data = (await res.json().catch(() => null)) as
      | { detail?: string }
      | null;
    if (typeof data?.detail === "string" && data.detail.trim()) {
      return data.detail;
    }
  }
  return (await res.text().catch(() => res.statusText)) || res.statusText;
}

export async function extractInterests(text: string): Promise<string[]> {
  const res = await fetch(`${config.agentUrl.replace(/\/+$/, "")}/agent/extract-interests`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) return [];
  const data = (await res.json()) as { interests: string[] };
  return data.interests ?? [];
}

export async function postProfile(patch: Partial<Profile>): Promise<Profile> {
  const res = await fetch(profileEndpoint(), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error(`postProfile failed: ${res.status}`);
  return res.json() as Promise<Profile>;
}

export async function getProfile(): Promise<Profile> {
  const res = await fetch(profileEndpoint(), { method: "GET" });
  if (!res.ok) throw new Error(`getProfile failed: ${res.status}`);
  return res.json() as Promise<Profile>;
}

export async function clearProfile(): Promise<void> {
  await fetch(`${config.agentUrl.replace(/\/+$/, "")}/agent/profile/clear`, {
    method: "POST",
  });
}

export type DemoProfileBootstrap = {
  profile: Profile;
};

export async function resetDemoProfile(): Promise<DemoProfileBootstrap> {
  const res = await fetch(demoResetEndpoint(), { method: "POST" });
  if (!res.ok) throw new Error(`resetDemoProfile failed: ${res.status}`);
  return res.json() as Promise<DemoProfileBootstrap>;
}


function tumConnectEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/onboarding/tum-connect`;
}

function cvUploadEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/onboarding/cv`;
}

export async function connectTumAccount(payload: {
  tumSsoId: string;
  password: string;
}): Promise<Profile> {
  const res = await fetch(tumConnectEndpoint(), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await readErrorMessage(res);
    throw new Error(text || `tum connect failed: ${res.status}`);
  }
  return res.json() as Promise<Profile>;
}

function tumSessionStatusEndpoint(): string {
  return `${config.agentUrl.replace(/\/+$/, "")}/agent/onboarding/tum-status`;
}

export async function getTumSessionStatus(tumSsoId: string): Promise<{ valid: boolean }> {
  const res = await fetch(tumSessionStatusEndpoint(), {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ tumSsoId }),
  });
  if (!res.ok) {
    const text = await readErrorMessage(res);
    throw new Error(text || `tum session status failed: ${res.status}`);
  }
  return res.json() as Promise<{ valid: boolean }>;
}

export async function uploadCv(file: File): Promise<Profile> {
  const form = new FormData();
  form.append("file", file, file.name);
  const res = await fetch(cvUploadEndpoint(), {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await readErrorMessage(res);
    throw new Error(text || `cv upload failed: ${res.status}`);
  }
  return res.json() as Promise<Profile>;
}

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

export function extractJsonArray(text: string): unknown {
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

export function normalizeItems(raw: unknown): DiscoverItem[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((entry, idx) => {
      if (!entry || typeof entry !== "object") return null;
      const e = entry as Record<string, unknown>;
      const title = typeof e.title === "string" ? e.title.trim() : "";
      if (!title) return null;
      const why = typeof e.why === "string" ? e.why.trim() : "";
      const what = typeof e.what === 'string' ? e.what.trim() : undefined;
      const land = typeof e.land === 'string' ? e.land.trim() : undefined;
      const id =
        typeof e.id === "string" && e.id.trim().length > 0
          ? e.id.trim()
          : `item-${idx}`;
      const validTypes = ["course", "event", "person", "scholarship"] as const;
      const rawType = typeof e.type === "string" ? e.type : "";
      const type: DiscoverItem["type"] = (validTypes as readonly string[]).includes(rawType)
        ? (rawType as DiscoverItem["type"])
        : "course";
      const meta: DiscoverItem["meta"] =
        e.meta && typeof e.meta === "object" && !Array.isArray(e.meta)
          ? (e.meta as DiscoverItem["meta"])
          : {};
      return { id, title, why, what, land, type, meta };
    })
    .filter((x): x is NonNullable<typeof x> => x !== null);
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
