export type ChatRole = "user" | "assistant";

export type ToolCallStatus = "running" | "done" | "error";

export type ToolCall = {
  id: string;
  toolName: string;
  input: unknown;
  status: ToolCallStatus;
  result?: string;
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  toolCalls: ToolCall[];
  done: boolean;
};

export type AgentEvent =
  | { type: "text"; delta: string }
  | { type: "tool_start"; id: string; name: string; input: unknown }
  | { type: "tool_result"; id: string; content: string; isError: boolean }
  | { type: "done" }
  | { type: "error"; message: string };
