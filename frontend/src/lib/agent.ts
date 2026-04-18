import { config } from "./config";
import { buildSystemPrompt } from "./systemPrompt";
import type { AgentEvent, ChatRole } from "./types";

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
