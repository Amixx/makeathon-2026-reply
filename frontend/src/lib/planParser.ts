import type { PlanOutput, PlanSegment, PlanStep } from "./types";

function extractJsonBlock(text: string): string | null {
  const fenceMatch = text.match(/```json\s*([\s\S]*?)```/i);
  if (fenceMatch) return fenceMatch[1].trim();

  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start >= 0 && end > start) return text.slice(start, end + 1);

  return null;
}

function normalizeStep(raw: unknown): PlanStep | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  const title = typeof r.title === "string" ? r.title.trim() : "";
  const detail = typeof r.detail === "string" ? r.detail.trim() : "";
  if (!title || !detail) return null;

  const step: PlanStep = {
    title,
    detail,
    why: typeof r.why === "string" ? r.why.trim() : "",
  };
  if (typeof r.duration === "string" && r.duration.trim()) {
    step.duration = r.duration.trim();
  }
  const link = r.link as Record<string, unknown> | undefined;
  if (
    link &&
    typeof link.label === "string" &&
    typeof link.href === "string" &&
    link.href.trim()
  ) {
    step.link = { label: link.label.trim(), href: link.href.trim() };
  }
  return step;
}

function normalizeOutput(raw: unknown): PlanOutput | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;

  const stepsRaw = Array.isArray(r.steps) ? r.steps : [];
  const steps = stepsRaw
    .map(normalizeStep)
    .filter((s): s is PlanStep => s !== null);
  if (steps.length === 0) return null;

  const output: PlanOutput = { steps };

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
