---
description: Show the live board, pick the next task, and move it through the worktree lanes
---

You are the **orchestrator**. This command runs in the main checkout and is the only writer of
`docs/BOARD.md`.

Read `docs/BOARD.md` and report:

1. **Snapshot** — every row: ID, task, type, status, risk, worktree, next action.
2. **Counts per lane** — Backlog, Ready, In Progress, In Review, Pending Merge, Blocked, Merged.
3. **Next task** — the highest-priority `Ready` row that is not blocked by another row, with its
   acceptance criteria and risk.

Then, if asked to start it:

- Create the Agent Manager worktree named after the feature
  (`.kilo/worktrees/<feature-slug>/`, branch `feat|fix|chore|docs/<feature-slug>`).
- Record the worktree path and branch in the board row and set it to `In Progress`.
- Delegate the work to a builder session in that worktree. The builder does **not** edit this
  board — it updates the scope docs and reports back.
- For frontend work, the builder builds the component factory and gallery first and waits for
  the user's approval of the visual language (`/components`). No screens before that.
- On the builder's report: set `In Review`, then `Pending Merge` when the merge gate (§B4) is
  green — including the QA and UI/UX review lanes for frontend work (`/ui`) — then ask the user
  to inspect and merge. Never merge into `main` yourself.
- After the user merges, set `Merged` and clean up the worktree.
