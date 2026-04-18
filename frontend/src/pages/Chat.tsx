import { Flex } from "@adobe/react-spectrum";
import ChatInput from "../components/chat/ChatInput";
import MessageList from "../components/chat/MessageList";
import { useChat } from "../hooks/useChat";
import styles from "./Chat.module.css";

export default function Chat() {
  const chat = useChat({ autoSpeakReplies: false });

  return (
    <Flex direction="column" height="calc(100vh - 4rem)">
      <MessageList messages={chat.messages} isStreaming={chat.isStreaming} />
      {chat.error && <div className={styles.error}>{chat.error}</div>}
      <ChatInput
        onSend={chat.sendText}
        onCancel={chat.cancel}
        onToggleRecording={chat.toggleRecording}
        isStreaming={chat.isStreaming}
        isRecording={chat.isRecording}
      />
    </Flex>
  );
}
