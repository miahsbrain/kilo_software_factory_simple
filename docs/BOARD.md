# BOARD — software factory

**This board carries factory work only.** Product work is tracked on the project's own board,
in that project's repository. See `AGENTS.md` §A1.

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

| ID | Task | Type | Status | Priority | Risk | Blocked by | Repos | Branch/Worktree | Notes |
|---|---|---|---|---|---|---|---|---|---|
| BOARD-101 | Add the no-production-build rule to the factory rules and the frontend builder rules | Docs | Pending Merge | P2 | 🟢 low — rules text only; no runtime code changes. | None. | control | .kilo/worktrees/add-the-no-production-build-rule · branch docs/add-the-no-production-build-rule | - [x] AGENTS.md gains a No production builds section · - [x] .kilo/agent/frontend-dev.md carries the same rule for the builder · Built: commit 85c75fc on docs/add-the-no-production-build-rule, worktree .kilo/worktrees/add-the-no-production-build-rule. Merge with: git merge --no-ff docs/add-the-no-production-build-rule -m "merge: add-the-no-production-build-rule" |
| BOARD-102 | Compact accordion redesign of the live board dashboard | Feature | Pending Merge | P2 | 🟡 medium — read-only viewer only; board data and scripts untouched. | None. | control | .kilo/worktrees/compact-accordion-redesign-of-the-live · branch feat/compact-accordion-redesign-of-the-live | - [x] Lanes render as a vertical accordion, one column; no horizontal scrolling · proof: artifacts/factory/qa/2026-11-04/BOARD-102/round2 (horizontal_overflow_check_passed true at 320/390/834/1440/1920) · - [x] Backlog, Merged, Dropped collapsed by default; active lanes open; a lane with no cards stays folded · proof: board_serve.py lane_open_by_default · - [x] Cards are compact rows (ID, task, type, priority, risk); click expands blocked-by, worktree, fingerprint, notes · proof: docs/reviews/BOARD-102-qa.md · - [x] Merged lane shows the 10 most recent rows, with a show-all control · proof: Show all 11 in the capture, .card.extra display none to block on click · - [x] Open/closed lanes and expanded cards persist in localStorage · proof: state written on click and applied after a reload · - [x] Filter still hides non-matching cards · proof: filter path unchanged, capture loads with an empty filter · - [x] Board file, board.py and worktree scripts unchanged (read-only guarantee holds) · proof: git diff main --stat touches only board_serve.py and docs · Built: commits 0c410ac, 4f79977, 8bcf3b3, 12f0eee on feat/compact-accordion-redesign-of-the-live, worktree .kilo/worktrees/compact-accordion-redesign-of-the-live. Merge with: git merge --no-ff feat/compact-accordion-redesign-of-the-live -m 'merge: compact-accordion-redesign-of-the-live' |

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
