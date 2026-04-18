import { Button } from "@adobe/react-spectrum";
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
            : "Ask Campus Co-Pilot…"
        }
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={2}
        disabled={disabled || isStreaming || isRecording}
      />
      <div className={styles.buttons}>
        {voiceAvailable && (
          <Button
            variant={isRecording ? "negative" : "secondary"}
            onPress={onToggleRecording}
            isDisabled={disabled || isStreaming}
          >
            {isRecording ? "Stop" : "🎙"}
          </Button>
        )}
        {isStreaming ? (
          <Button variant="negative" onPress={onCancel}>
            Cancel
          </Button>
        ) : (
          <Button
            variant="accent"
            onPress={send}
            isDisabled={disabled || value.trim().length === 0}
          >
            Send
          </Button>
        )}
      </div>
    </div>
  );
}
