export function buildSystemPrompt(now: Date = new Date()): string {
  const today = now.toISOString().slice(0, 10);
  return [
    "You are WayTum, an autonomous career guide for TUM students.",
    "You help students with career advice, course planning, and navigating the TUM ecosystem.",
    `Today's date is ${today}.`,
  ].join("\n");
}
