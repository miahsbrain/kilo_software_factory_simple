---
description: Run the Build → QA → Review loop for one board row and leave it pending merge
---

You are the **orchestrator** for a single board row. The work happens in the worktree; the board
stays in the main checkout and only you write it.

1. **Pick** the row: highest-priority `Ready`, not blocked by another row. Grade it
   low/medium/high (§B4 "Task grading") to set the rigor of review.
2. **Build** in the worktree named after the feature. Create it with the script if it does not
   exist: `python3 .kilo/skills/git-worktree/scripts/worktree.py create <slug> --type <type>
   --base <base>`.
   - Implement the smallest change that satisfies every acceptance criterion.
   - Update the scope docs (`HANDOVER.md`, `BUSINESS-LOGIC.md`, `ARCHITECTURE.md`,
     `DECISIONS.md`, `changelog/`) in the same change set (§B1).
   - Do **not** edit `docs/BOARD.md` from the worktree.
   - Run the project's verification command from `docs/STACK.md`.
   - Commit locally on the worktree branch. Never push, never merge, never open a PR.
3. **QA** — produce evidence, not assertion. One observable check per acceptance criterion,
   with the command and result and `file:line`. For UI work, capture screenshots.
   - Pass → continue to Review.
   - Fail → row back to `In Progress` with the expected-vs-actual and the failing repro.
     Never mark an unchecked criterion as done.
4. **Review** — read the diff and the acceptance criteria first, form your own hypotheses, then
   compare against the builder's summary (§A8). Re-run the exact verification command the QA
   lane used. Any blocking finding → row back to `In Progress` with the finding restated.
   For frontend work, also run the UI/UX critique lane (`/ui`) — both must be green.
5. **Merge gate** (§B4): all criteria verified, verification passed, QA evidence present, review
   clean, docs updated, and `worktree.py verify <slug>` printing `READY FOR MERGE` → set the row
   to `Pending Merge` with `board.py set-status`.
   That state means the work is waiting for human approval to merge.
6. **Hand off.** Report the worktree path, the branch, the commits, and the review commands.
   Print the merge command for the user:

       git merge --no-ff <type>/<feature-slug> -m "merge: <feature-slug>"

   Never merge, push, or open a PR yourself.

Report in this order: what was done, what is proven, what is not done and why, next action.
