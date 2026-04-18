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

export type DiscoverItem = {
  id: string;
  title: string;
  why: string;
};

export type PlanSegment =
  | { kind: "text"; id: string; content: string }
  | { kind: "tool"; id: string; toolCall: ToolCall };

export type PlanLink = {
  label: string;
  href: string;
};

export type PlanStep = {
  title: string;
  detail: string;
  why: string;
  duration?: string;
  link?: PlanLink;
};

export type PlanEmail = {
  to?: string;
  subject?: string;
  body: string;
  anchor_note?: string;
};

export type PlanFact = {
  label: string;
  value: string;
  note?: string;
};

export type PlanOutput = {
  intro?: string;
  steps: PlanStep[];
  email?: PlanEmail;
  key_facts?: PlanFact[];
  reassurance?: string;
};
