import { useCallback, useEffect, useRef, useState } from "react";
import { runDiscover } from "../lib/agent";
import type { DiscoverItem } from "../lib/types";

type UseDiscoverReturn = {
  items: DiscoverItem[];
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
};

export function useDiscover(): UseDiscoverReturn {
  const [items, setItems] = useState<DiscoverItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const refresh = useCallback(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);

    runDiscover(
      {},
      {
        onItems: (next) => setItems(next),
        onError: (msg) => {
          if (controller.signal.aborted) return;
          setError(msg);
          setIsLoading(false);
        },
        onDone: () => {
          if (!controller.signal.aborted) setIsLoading(false);
        },
      },
      controller.signal,
    );
  }, []);

  useEffect(() => {
    refresh();
    return () => {
      abortRef.current?.abort();
    };
  }, [refresh]);

  return { items, isLoading, error, refresh };
}
