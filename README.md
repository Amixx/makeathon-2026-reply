# Campus Career Co-Pilot

TUM.ai Makeathon 2026 — Reply track ("Campus Co-Pilot Suite").

An autonomous agent that acts as a **career guide / coach** for TUM students: audits
professional hygiene (CV, email, online presence), cross-references your transcript
against real job/workshop requirements, and scouts opportunities from the TUM
ecosystem plus external sources. It bridges disconnected systems and takes concrete
actions on the student's behalf.

## What it does

- **Profile audit** — scans CV + public profiles for red flags, gaps, weak framing.
- **Skill ↔ market gap analysis** — transcript / course history vs. modern stacks and
  posted role requirements.
- **Opportunity scouting** — Reply workshops, working-student roles, TUM career
  events, and external job boards.
- **Proactive nudges** — upcoming deadlines, new matches, application prep.

## TUM systems integrated

- TUMonline (transcript / courses)
- Moodle (completed material signal)
- TUM career / events pages
- Reply workshop listings

## Custom integrations

- CV parsing + rewrite suggestions
- External job boards / LinkedIn-style profile check
- (more — see [docs/TASK.md](docs/TASK.md) for challenge brief)

## Stack

- **Models:** Gemini (team has credits; API key provided at dev time)
- Everything else TBD.

## Structure

```
docs/          # Challenge brief
```

## Run

TBD.
