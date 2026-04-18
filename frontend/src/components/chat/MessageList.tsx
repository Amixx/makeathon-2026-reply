import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../lib/types";
import MessageBubble from "./MessageBubble";
import styles from "./MessageList.module.css";

type Props = {
  messages: ChatMessage[];
  isStreaming: boolean;
};

export default function MessageList({ messages, isStreaming }: Props) {
  const endRef = useRef<HTMLDivElement | null>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll on every message change
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className={styles.empty}>
        <p>
          Ask about courses, the mensa, campus rooms, departures, or your career
          path.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.list}>
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} streaming={isStreaming} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
