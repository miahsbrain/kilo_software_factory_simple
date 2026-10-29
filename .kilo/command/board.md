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

- Create the worktree with the script, named after the feature:
  `python3 .kilo/skills/git-worktree/scripts/worktree.py create <slug> --type <type> --base <base>`
- Add the row with the script and record the worktree path and branch:
  `python3 .kilo/skills/board/scripts/board.py add --id BOARD-00X --task "..." --type Feature \
      --status Ready --priority P2 --risk "🟡 medium — one line" --blocked-by "None." \
      --branch-worktree ".kilo/worktrees/<slug> · branch <type>/<slug>"`
- Set it to `In Progress` with
  `python3 .kilo/skills/board/scripts/board.py set-status <ID> "In Progress"`.
- Delegate the work to a builder agent working inside that worktree. The builder does **not**
  edit this board — it updates the scope docs and reports back.
- For frontend work, the builder builds the component factory and gallery first and waits for
  the user's approval of the visual language (`/components`). No screens before that.
- On the builder's report: set `In Review`, then `Pending Merge` when the merge gate (§B4) is
  green — including the QA and UI/UX review lanes for frontend work (`/ui`). `Pending Merge`
  means the work is waiting for human approval to merge.
- Print the review and merge commands for the user. Never merge, push, or open a PR yourself.
- After the user merges, set `Merged` and clean up the worktree.
