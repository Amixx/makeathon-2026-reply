import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { runPlan } from "../lib/agent";
import { parsePlanFromSegments } from "../lib/planParser";
import type { DiscoverItem, PlanOutput, PlanSegment } from "../lib/types";

type UsePlanReturn = {
  item: DiscoverItem | null;
  segments: PlanSegment[];
  output: PlanOutput | null;
  isStreaming: boolean;
  error: string | null;
  open: (item: DiscoverItem) => void;
  close: () => void;
  retry: () => void;
};

let segCounter = 0;
const nextSegId = () => `seg-${Date.now().toString(36)}-${(segCounter++).toString(36)}`;

export function usePlan(): UsePlanReturn {
  const [item, setItem] = useState<DiscoverItem | null>(null);
  const [segments, setSegments] = useState<PlanSegment[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const pendingRef = useRef("");
  const rafRef = useRef<number | null>(null);

  const flush = useCallback(() => {
    rafRef.current = null;
    const buffer = pendingRef.current;
    if (!buffer) return;
    pendingRef.current = "";
    setSegments((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.kind === "text") {
        return [
          ...prev.slice(0, -1),
          { ...last, content: last.content + buffer },
        ];
      }
      return [...prev, { kind: "text", id: nextSegId(), content: buffer }];
    });
  }, []);

  const schedule = useCallback(() => {
    if (rafRef.current !== null) return;
    rafRef.current = requestAnimationFrame(flush);
  }, [flush]);

  const flushNow = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    flush();
  }, [flush]);

  const start = useCallback(
    (target: DiscoverItem) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      pendingRef.current = "";
      setSegments([]);
      setError(null);
      setIsStreaming(true);

      runPlan(
        target,
        {},
        {
          onTextDelta: (delta) => {
            pendingRef.current += delta;
            schedule();
          },
          onToolStart: (id, name, input) => {
            flushNow();
            setSegments((prev) => [
              ...prev,
              {
                kind: "tool",
                id,
                toolCall: { id, toolName: name, input, status: "running" },
              },
            ]);
          },
          onToolResult: (id, content, isError) => {
            setSegments((prev) =>
              prev.map((seg) =>
                seg.kind === "tool" && seg.id === id
                  ? {
                      ...seg,
                      toolCall: {
                        ...seg.toolCall,
                        status: isError ? "error" : "done",
                        result: content,
                      },
                    }
                  : seg,
              ),
            );
          },
          onError: (msg) => {
            if (controller.signal.aborted) return;
            setError(msg);
            setIsStreaming(false);
          },
          onDone: () => {
            if (controller.signal.aborted) return;
            flushNow();
            setIsStreaming(false);
          },
        },
        controller.signal,
      );
    },
    [flushNow, schedule],
  );

  const open = useCallback(
    (target: DiscoverItem) => {
      setItem(target);
      start(target);
    },
    [start],
  );

  const close = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    pendingRef.current = "";
    setItem(null);
    setSegments([]);
    setError(null);
    setIsStreaming(false);
  }, []);

  const output = useMemo<PlanOutput | null>(() => {
    if (isStreaming) return null;
    return parsePlanFromSegments(segments);
  }, [isStreaming, segments]);

  const retry = useCallback(() => {
    if (item) start(item);
  }, [item, start]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return {
    item,
    segments,
    output,
    isStreaming,
    error,
    open,
    close,
    retry,
  };
}
