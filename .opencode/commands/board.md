---
description: Show the live board, pick the next task, and move it through the worktree lanes
---

You are the **orchestrator**. Update the Git-common-dir SQLite board through `board.py` only.

`docs/BOARD.md` is a legacy one-time import source, not the live board. Markdown exports are
generated snapshots; the human-only finalize command owns its integration transition.

Run `python3 .opencode/skills/board/scripts/board.py show` to initialize SQLite, then report:

1. **Snapshot** — every row: ID, task, type, status, risk, worktree, next action.
2. **Counts per lane** — Backlog, Ready, In Progress, In Review, Pending Merge, Blocked, Merged.
3. **Next task** — the highest-priority `Ready` row that is not blocked by another row, with its
   acceptance criteria and risk.

Then, if asked to start it:

- Add the row with the script:
  `python3 .opencode/skills/board/scripts/board.py add --id BOARD-00X --task "..." --type Feature \
      --status Ready --priority P2 --risk "🟡 medium — one line" --blocked-by "None."`
- Create the worktree from the row — the name and branch type are derived from it:
  `python3 .opencode/skills/git-worktree/scripts/worktree.py create --board BOARD-00X --base main`
  The script writes the row's `Branch/Worktree` cell and moves it to `In Progress`.
- Delegate the work to a builder agent working inside that worktree. The builder does **not**
  edit this board — it updates the scope docs and reports back.
- For frontend work, the builder builds the component factory and gallery first and waits for
  the user's approval of the visual language (`/components`). No screens before that.
- On the builder's report: set `In Review`, then `Pending Merge` when the merge gate (§B4) is
  green — including the QA and UI/UX review lanes for frontend work (`/ui`). `Pending Merge`
  means the work is waiting for human approval to merge.
- Recheck the live worktree and board (§B11); print the `worktree.py handoff --board <ID>` block.
  Only finished, verified, reviewed, committed, clean `Pending Merge` work gets merge guidance.
  Otherwise provide only review/diff and blockers, with no manually added merge or teardown.
  Never merge, push, or open a PR yourself.
- A review finding returns to the original builder in the same worktree. Do not create an
  automatic Fix row. The human invokes `worktree.py finalize` with a real terminal and typed
  board/base/branch/tip; agents never invoke it or independently merge/clean up.
