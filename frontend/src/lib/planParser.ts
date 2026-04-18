import type { PlanOutput, PlanSegment } from "./types";

function extractJsonBlock(text: string): string | null {
  const fenceMatch = text.match(/```json\s*([\s\S]*?)```/i);
  if (fenceMatch) return fenceMatch[1].trim();

  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start >= 0 && end > start) return text.slice(start, end + 1);

  return null;
}

function normalizeOutput(raw: unknown): PlanOutput | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;

  // Parse action (required)
  const actionRaw = r.action as Record<string, unknown> | undefined;
  if (!actionRaw || typeof actionRaw !== "object") return null;
  const actionTitle = typeof actionRaw.title === "string" ? actionRaw.title.trim() : "";
  const actionDetail = typeof actionRaw.detail === "string" ? actionRaw.detail.trim() : "";
  const actionType = typeof actionRaw.type === "string" ? actionRaw.type.trim() : "done";
  if (!actionTitle) return null;

  const action: PlanOutput["action"] = {
    type: actionType,
    title: actionTitle,
    detail: actionDetail,
  };
  const actionLink = actionRaw.link as Record<string, unknown> | undefined;
  if (
    actionLink &&
    typeof actionLink.label === "string" &&
    typeof actionLink.href === "string" &&
    actionLink.href.trim()
  ) {
    action.link = { label: actionLink.label.trim(), href: actionLink.href.trim() };
  }

  const output: PlanOutput = { action };

  if (typeof r.intro === "string" && r.intro.trim()) {
    output.intro = r.intro.trim();
  }
  if (typeof r.reassurance === "string" && r.reassurance.trim()) {
    output.reassurance = r.reassurance.trim();
  }
  const email = r.email as Record<string, unknown> | undefined;
  if (email && typeof email.body === "string" && email.body.trim()) {
    output.email = {
      to: typeof email.to === "string" ? email.to.trim() : undefined,
      subject:
        typeof email.subject === "string" ? email.subject.trim() : undefined,
      body: email.body,
      anchor_note:
        typeof email.anchor_note === "string"
          ? email.anchor_note.trim()
          : undefined,
    };
  }
  const facts = Array.isArray(r.key_facts) ? r.key_facts : [];
  const normalizedFacts = facts
    .map((f) => {
      if (!f || typeof f !== "object") return null;
      const fr = f as Record<string, unknown>;
      const label = typeof fr.label === "string" ? fr.label.trim() : "";
      const value = typeof fr.value === "string" ? fr.value.trim() : "";
      if (!label || !value) return null;
      return {
        label,
        value,
        note: typeof fr.note === "string" ? fr.note.trim() : undefined,
      };
    })
    .filter((f): f is NonNullable<typeof f> => f !== null);
  if (normalizedFacts.length > 0) output.key_facts = normalizedFacts;

  return output;
}

export function parsePlanFromSegments(
  segments: PlanSegment[],
): PlanOutput | null {
  const joined = segments
    .filter((s): s is Extract<PlanSegment, { kind: "text" }> => s.kind === "text")
    .map((s) => s.content)
    .join("\n");
  const block = extractJsonBlock(joined);
  if (!block) return null;
  try {
    return normalizeOutput(JSON.parse(block));
  } catch {
    return null;
  }
}
