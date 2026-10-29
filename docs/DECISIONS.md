# DECISIONS

Append-only. Ultra-concise approved architectural decisions. Newest first.

## How to record a decision

- **Approved** — add a row to the table below with the date and the one-line reason.
- **Assumption** — add a row with `Status: ASSUMPTION — awaiting user confirmation` and list it
  in the handover's Open Questions. Replace it with the approved decision when confirmed.

| # | Decision | Context | Consequence | Date |
|---|---|---|---|---|
| ADR-001 | `AGENTS.md` lives at the repo root; all other docs live in `docs/` (except `DOMAIN.md`, `ROADMAP.md`, `CHANGELOG.md`) | Kilo auto-loads the root file; avoids scattered docs | Root is the only place for cross-project rules | 2026-10-29 |
| ADR-002 | Two changelogs: `docs/changelog/` (engineering, updated every change) and root `CHANGELOG.md` (product-facing, user-approved only) | Different audiences and cadences | Both must be kept in sync at release time | 2026-10-29 |
| ADR-003 | No git commits, amends, pushes, or PRs by any agent | User decision | Work is left in the worktree for user review and merge | 2026-10-29 |
| ADR-004 | Functional core / imperative shell, reuse-before-creation, minimal comments | User decision | Domain logic is pure and testable; codebase stays small | 2026-10-29 |
| ADR-005 | Every change happens in a worktree named after the feature (`.kilo/worktrees/<feature-slug>/`), never in the main checkout | User decision | Worktrees are the unit of work; each carries code + doc updates together | 2026-10-29 |
| ADR-006 | Board lanes are `Backlog → Ready → In Progress → In Review → Pending Merge → Merged`, plus `Blocked`/`Dropped` | super-board concept, adapted to a local markdown board | Works offline in the CLI; `Pending Merge` is the inspection gate before the user merges | 2026-10-29 |
| ADR-007 | Guard rules (worktree confinement, secrets, key literals, destructive scope, protected branch) live as markdown in `AGENTS.md`, not as hook scripts | Kilo has no hook runner | Rules are agent responsibilities rather than enforced tooling | 2026-10-29 |
| ADR-008 | Acceptance criteria are checkboxes with a proof line; evidence before prose | super-board writing standard | Prevents "done" claims that were never verified | 2026-10-29 |
| ADR-009 | Worktree naming uses the feature slug, not an issue number | User decision | Overrides super-board's `issue-<N>` convention | 2026-10-29 |
| ADR-010 | The live board lives in the main checkout and has a single writer: the orchestrator. Worktree branches never edit `docs/BOARD.md` | User decision — recommended option over branch-carried boards | The board shows in-flight work at all times and parallel worktrees cannot conflict on it. After a merge, the orchestrator marks the row `Merged` on `main` | 2026-10-29 |
| ADR-011 | The architect asks the user for implementation decisions before building anything, and never silently assumes product, data, contract, architecture, persistence, boundary, or operations choices | User decision | A decision sheet with a recommended option goes to the user; approved decisions travel with the builder prompt; unknowns escalate back instead of being guessed | 2026-10-29 |
| ADR-012 | Frontend work builds a component factory and a gallery route first; the user approves the visual language before any screen is built | User decision | Screens reuse approved components only; a deviation from the gallery is a review finding, not a new decision | 2026-10-29 |
| ADR-013 | The QA lane for frontend work uses Playwright and produces screenshot evidence; a UI/UX critique runs alongside it against 15 anti-slop rules | super-board concept, adapted; lean version | A frontend row cannot leave `In Review` until both are green; artifacts under `apps/<scope>/artifacts/qa/` | 2026-10-29 |
| ADR-014 | `.kilo/command/*.md` are derived artifacts of `AGENTS.md`, not independent rules | User decision | A rule change updates the matching command in the same change; `AGENTS.md` wins on conflict | 2026-10-29 |
| ADR-015 | Builders commit locally on their worktree branch; agents never push, never merge into `main`, never open a PR | The previous "never commit" rule left nothing for the user to merge | The user merges; local commits make the merge real and reviewable | 2026-10-29 |
| ADR-016 | Dedicated agents in `.kilo/agent/`: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic` | User request for a multi-agent team | Builders and reviewers each carry their own scope, style, verification, and reporting rules | 2026-10-29 |
| ADR-017 | QA and UI/UX findings become board rows of type `Fix`, written by the orchestrator from the review reports | User request | Reviews are independent of the builder's claims; the board keeps a single writer | 2026-10-29 |
