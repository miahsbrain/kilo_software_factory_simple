# The plan skill, merged from two upstream skills

**Date:** 2026-11-10
**Board:** BOARD-106
**Branch:** feat/port-a-merged-plan-skill
**Type:** Feature

## What changed

A new skill at `.kilo/skills/plan/`: a `SKILL.md` and twelve files under `references/`.

The content comes from two upstream skills by Jeffallan
(https://github.com/Jeffallan/claude-skills, MIT, © 2025 Jeffallan): `feature-forge`, which
carries the requirements side, and `architecture-designer`, which carries the architecture side.
They are merged into one greenfield planning procedure, not shipped as two skills.

All ten upstream references are carried over, with their text intact and an MIT credit line
naming the upstream source in every file:

| File | Upstream |
|---|---|
| `references/interview-questions.md` | `feature-forge` |
| `references/specification-template.md` | `feature-forge` |
| `references/ears-syntax.md` | `feature-forge` |
| `references/acceptance-criteria.md` | `feature-forge` |
| `references/pre-discovery-subagents.md` | `feature-forge` |
| `references/system-design.md` | `architecture-designer` |
| `references/architecture-patterns.md` | `architecture-designer` |
| `references/adr-template.md` | `architecture-designer` |
| `references/nfr-checklist.md` | `architecture-designer` |
| `references/database-selection.md` | `architecture-designer` |

Two research documents come across as background reading, MIT, © Jesse Vincent
(obra/superpowers): `references/superpowers-research.md` and
`references/superpowers-research-findings.md`.

## Why the output lands in the existing documents

A planning procedure that writes its own `specs/` folder would create a second source of truth
next to `DOMAIN.md` and the board. Each phase of the merged skill therefore names the document
it writes into, and no new document type is introduced:

| Phase | Output document |
|---|---|
| Discover | `DOMAIN.md` |
| Requirements | `docs/BUSINESS-LOGIC.md`, the spec inside `DOMAIN.md`, board rows for checkable criteria |
| Architecture | `docs/DECISIONS.md`, `docs/RISKS.md`, `docs/STACK.md` |
| The plan | `ROADMAP.md` and one board row per unit of work on `docs/BOARD.md` |
| The decision gate | `docs/DECISIONS.md` and the handover's Open Questions |

The ADRs follow this repository's format: one line per decision in `docs/DECISIONS.md`,
numbered `ADR-001`, `ADR-002`, …, append-only. The upstream ADR template stays as the
reasoning that goes into that row.

## The tools are adapted

| Upstream | Here |
|---|---|
| `AskUserQuestions` | the `question` tool |
| `Task` subagents | the `Task` tool |
| "write a spec document" | "write into the mapped document" |

EARS stays inside the specification document. A board row keeps this repository's own format:
`- [ ] criterion — proof`, with the proof a command, a `file:line`, or a sha.

## The precedence rule

The rule is stated once, in `.kilo/skills/plan/SKILL.md`, and referenced from `AGENTS.md`
§A2, §A4 and §A6 rather than repeated. `AGENTS.md` §A4 and §A6 remain the contract: a batched
interview, a decision sheet, nothing assumed. The skill adds the detail — the question banks,
the specification template, the EARS criteria, the ADR template, the NFR checklist.

## Impact

- New: `.kilo/skills/plan/` with `SKILL.md` and twelve references.
- `AGENTS.md` §A2, §A4 and §A6 gain a short pointer to the skill.
- `docs/DECISIONS.md` gains ADR-069.
- No new dependency. Standard tools only.
- The policy file and the permission map are untouched.
