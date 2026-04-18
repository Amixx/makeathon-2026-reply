import Markdown from "react-markdown";
import type { ChatMessage } from "../../lib/types";
import styles from "./MessageBubble.module.css";
import ToolCallBadge from "./ToolCallBadge";

type Props = {
  message: ChatMessage;
  streaming?: boolean;
};

export default function MessageBubble({ message, streaming }: Props) {
  const isUser = message.role === "user";
  const showCaret = streaming && message.role === "assistant" && !message.done;

  return (
    <div
      className={`${styles.row} ${isUser ? styles.userRow : styles.assistantRow}`}
    >
      <div
        className={`${styles.bubble} ${isUser ? styles.user : styles.assistant}`}
      >
        {message.toolCalls.length > 0 && (
          <div className={styles.tools}>
            {message.toolCalls.map((tc) => (
              <ToolCallBadge key={tc.id} toolCall={tc} />
            ))}
          </div>
        )}
        {message.text && (
          <div className={styles.text}>
            {isUser ? (
              <p>{message.text}</p>
            ) : (
              <Markdown>{message.text}</Markdown>
            )}
            {showCaret && <span className={styles.caret} aria-hidden />}
          </div>
        )}
        {!message.text && showCaret && (
          <div className={styles.text}>
            <span className={styles.caret} aria-hidden />
          </div>
        )}
      </div>
    </div>
  );
}
