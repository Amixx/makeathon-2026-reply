import { useCallback, useEffect, useRef, useState } from "react";
import type { AgentHistoryEntry } from "../lib/agent";
import { runAgent } from "../lib/agent";
import type { ChatMessage, ToolCall } from "../lib/types";
import { speak, startRecording, transcribe } from "../lib/voice";

type UseChatOptions = {
  autoSpeakReplies?: boolean;
};

type UseChatReturn = {
  messages: ChatMessage[];
  isStreaming: boolean;
  isRecording: boolean;
  error: string | null;
  sendText: (text: string) => void;
  toggleRecording: () => Promise<void>;
  cancel: () => void;
  replayLastReply: () => Promise<void>;
};

let nextId = 0;
const newId = () => `m-${Date.now().toString(36)}-${(nextId++).toString(36)}`;

type Recording = { stop: () => Promise<Blob> };

function toHistory(messages: ChatMessage[]): AgentHistoryEntry[] {
  return messages
    .filter((m) => m.text.trim().length > 0)
    .map<AgentHistoryEntry>((m) => ({ role: m.role, content: m.text }));
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const { autoSpeakReplies = false } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesRef = useRef<ChatMessage[]>([]);
  messagesRef.current = messages;

  const abortRef = useRef<AbortController | null>(null);
  const recordingRef = useRef<Recording | null>(null);

  const pendingTextRef = useRef<string>("");
  const currentAssistantIdRef = useRef<string | null>(null);
  const rafHandleRef = useRef<number | null>(null);

  const flushText = useCallback(() => {
    rafHandleRef.current = null;
    const delta = pendingTextRef.current;
    const id = currentAssistantIdRef.current;
    if (!delta || !id) return;
    pendingTextRef.current = "";
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, text: m.text + delta } : m)),
    );
  }, []);

  const scheduleFlush = useCallback(() => {
    if (rafHandleRef.current !== null) return;
    rafHandleRef.current = requestAnimationFrame(flushText);
  }, [flushText]);

  useEffect(() => {
    return () => {
      if (rafHandleRef.current !== null) {
        cancelAnimationFrame(rafHandleRef.current);
      }
      abortRef.current?.abort();
    };
  }, []);

  const updateAssistant = useCallback(
    (id: string, patch: (msg: ChatMessage) => ChatMessage) => {
      setMessages((prev) => prev.map((m) => (m.id === id ? patch(m) : m)));
    },
    [],
  );

  const handleToolStart = useCallback(
    (toolCallId: string, name: string, input: unknown) => {
      const id = currentAssistantIdRef.current;
      if (!id) return;
      const toolCall: ToolCall = {
        id: toolCallId,
        toolName: name,
        input,
        status: "running",
      };
      updateAssistant(id, (m) => ({
        ...m,
        toolCalls: [...m.toolCalls, toolCall],
      }));
    },
    [updateAssistant],
  );

  const handleToolResult = useCallback(
    (toolCallId: string, content: string, isError: boolean) => {
      const id = currentAssistantIdRef.current;
      if (!id) return;
      updateAssistant(id, (m) => ({
        ...m,
        toolCalls: m.toolCalls.map((tc) =>
          tc.id === toolCallId
            ? {
                ...tc,
                status: isError ? "error" : "done",
                result: content,
              }
            : tc,
        ),
      }));
    },
    [updateAssistant],
  );

  const finishAssistant = useCallback(
    (id: string) => {
      if (rafHandleRef.current !== null) {
        cancelAnimationFrame(rafHandleRef.current);
        rafHandleRef.current = null;
      }
      flushText();
      updateAssistant(id, (m) => ({ ...m, done: true }));
    },
    [flushText, updateAssistant],
  );

  const sendText = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      setError(null);
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const userMessage: ChatMessage = {
        id: newId(),
        role: "user",
        text: trimmed,
        toolCalls: [],
        done: true,
      };
      const assistantId = newId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        text: "",
        toolCalls: [],
        done: false,
      };
      currentAssistantIdRef.current = assistantId;
      pendingTextRef.current = "";

      const history: AgentHistoryEntry[] = [
        ...toHistory(messagesRef.current),
        { role: "user", content: trimmed },
      ];

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      runAgent(
        history,
        {
          onTextDelta: (delta) => {
            pendingTextRef.current += delta;
            scheduleFlush();
          },
          onToolStart: handleToolStart,
          onToolResult: handleToolResult,
          onError: (msg) => {
            setError(msg);
            finishAssistant(assistantId);
            setIsStreaming(false);
          },
          onDone: () => {
            finishAssistant(assistantId);
            setIsStreaming(false);
            if (autoSpeakReplies) {
              const finalMsg = messagesRef.current.find(
                (m) => m.id === assistantId,
              );
              const finalText = (finalMsg?.text ?? "") + pendingTextRef.current;
              if (finalText.trim()) {
                speak(finalText).catch(() => {});
              }
            }
          },
        },
        controller.signal,
      );
    },
    [
      autoSpeakReplies,
      finishAssistant,
      handleToolResult,
      handleToolStart,
      isStreaming,
      scheduleFlush,
    ],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    const id = currentAssistantIdRef.current;
    if (id) finishAssistant(id);
    setIsStreaming(false);
  }, [finishAssistant]);

  const toggleRecording = useCallback(async () => {
    if (isRecording) {
      const rec = recordingRef.current;
      recordingRef.current = null;
      setIsRecording(false);
      if (!rec) return;
      try {
        const blob = await rec.stop();
        const text = await transcribe(blob);
        if (text) sendText(text);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    } else {
      try {
        setError(null);
        const rec = await startRecording();
        recordingRef.current = rec;
        setIsRecording(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    }
  }, [isRecording, sendText]);

  const replayLastReply = useCallback(async () => {
    const lastAssistant = [...messagesRef.current]
      .reverse()
      .find((m) => m.role === "assistant" && m.done && m.text.trim());
    if (!lastAssistant) return;
    try {
      await speak(lastAssistant.text);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  return {
    messages,
    isStreaming,
    isRecording,
    error,
    sendText,
    toggleRecording,
    cancel,
    replayLastReply,
  };
}
