import type { KeyboardEvent } from "react";
import { useState } from "react";
import { isVoiceConfigured } from "../../lib/config";
import styles from "./ChatInput.module.css";

type Props = {
  onSend: (text: string) => void;
  onCancel: () => void;
  onToggleRecording: () => void;
  isStreaming: boolean;
  isRecording: boolean;
  disabled?: boolean;
};

export default function ChatInput({
  onSend,
  onCancel,
  onToggleRecording,
  isStreaming,
  isRecording,
  disabled,
}: Props) {
  const [value, setValue] = useState("");
  const voiceAvailable = isVoiceConfigured();

  const send = () => {
    const text = value.trim();
    if (!text || isStreaming) return;
    onSend(text);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className={styles.wrap}>
      <textarea
        className={styles.input}
        value={value}
        placeholder={
          isRecording
            ? "Recording… click the mic again to stop"
            : "Ask WayTum…"
        }
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={2}
        disabled={disabled || isStreaming || isRecording}
      />
      <div className={styles.buttons}>
        {voiceAvailable && (
          <button
            type="button"
            onClick={onToggleRecording}
            disabled={disabled || isStreaming}
          >
            {isRecording ? "Stop" : "🎙"}
          </button>
        )}
        {isStreaming ? (
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        ) : (
          <button
            type="button"
            onClick={send}
            disabled={disabled || value.trim().length === 0}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
