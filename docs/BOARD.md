# BOARD

**The board is the only state.** Re-read it at the start of every session and every task.
One row per unit of work. Never run two orchestrators against this board.

> **This is the live board, and it lives in the main checkout.**
> Only the orchestrator session (working in the repo root) edits this file.
> Worktree branches never edit it — they update the scope docs and report; the orchestrator
> writes the board. That keeps the board conflict-free and lets you see in-flight work here
> before it is merged.

Type: `Feature` `Fix` `Chore` `Docs` `Research`
Lanes: `Backlog` → `Ready` → `In Progress` → `In Review` → `Pending Merge` → `Merged`
(plus `Blocked` for parked work and `Dropped` for abandoned work)

| ID | Task | Type | Status | Priority | Risk | Blocked by | Branch/Worktree | Notes |
|---|---|---|---|---|---|---|---|---|

## Rules

- **Add a row before starting work.** Work not on the board is not sanctioned work.
- **Acceptance criteria (2–5, checkable) are required before a row leaves `Backlog`.**
  Write them in Notes as `- [ ]` checkboxes with the proof to record
  (`test: path:line`, or the exact manual step).
- **Risk** is a level plus one line of reasoning.
- **Blocked by** lists board IDs, or exactly `- None.`
- **Every change happens in a worktree named after the feature:**
  `.kilo/worktrees/<feature-slug>/` on branch `feat|fix|chore|docs/<feature-slug>`.
  Record the exact worktree path and branch here.
- Move the row the moment the status changes. `In Progress` → `In Review` → `Pending Merge`.
- `Pending Merge` means green and waiting for the user to inspect and merge into `main`.
  The agent never merges, pushes, or opens a PR.
- **Frontend rows** must clear the UI gate first (component factory + user-approved gallery) and
  the QA + UI/UX critique lane (`/ui`, Playwright evidence) before they can reach
  `Pending Merge`.
- `Merged` means the user actually merged it. The orchestrator sets this on `main` after the
  merge; that board edit is the only change left uncommitted for the user.
- `Blocked` = parked for a human. Record the one-line reason and what unblocks it.
- `Dropped` = abandoned. Record why.
