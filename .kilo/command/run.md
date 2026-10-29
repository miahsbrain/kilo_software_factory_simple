---
description: Run the Build → QA → Review loop for one board row and leave it pending merge
---

You are the **orchestrator** for a single board row. The work happens in the worktree; the board
stays in the main checkout and only you write it.

1. **Pick** the row: highest-priority `Ready`, not blocked by another row. Grade it
   low/medium/high (§B4 "Task grading") to set the rigor of review.
2. **Build** in the worktree named after the feature. Create it from the board row if it does not
   exist: `python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <ID> --base main`
   (the branch type and slug are derived from the row).
   - Implement the smallest change that satisfies every acceptance criterion.
   - Update the scope docs (`HANDOVER.md`, `BUSINESS-LOGIC.md`, `ARCHITECTURE.md`,
     `DECISIONS.md`, `changelog/`) in the same change set (§B1).
   - Do **not** edit `docs/BOARD.md` from the worktree.
   - Run the project's verification command from `docs/STACK.md`.
   - Commit locally on the worktree branch. Never push, never merge, never open a PR.
3. **QA** — produce evidence, not assertion. One observable check per acceptance criterion,
   with the command and result and `file:line`. For UI work, capture screenshots.
   - The capture script is the only way to capture UI evidence. Ad-hoc `chromium`, `npx playwright
     screenshot`, `curl`-and-guess, or any other browser command from bash is not acceptable
     evidence. If the script cannot do something the review needs, extend the script — do not
     work around it with another tool.
   - A row goes through at most **3** QA↔fix rounds. Round 3 is the last. Each round's review is
     done by a fresh reviewer that reads `docs/reviews/<task-id>-ledger.md` and the current
     screenshots, not the previous reviewer's reasoning. The ledger script opens and closes rounds:
     `python3 .kilo/skills/qa-review/scripts/ledger.py next-round --task-id BOARD-005`.
   - Findings are deduplicated by fingerprint (`kind|category|route|subject`). `check-finding.py`
     prints it; `board.py add --fingerprint` refuses a fingerprint that is already open and prints
     the command that updates the existing row.
   - Pass → continue to Review.
   - Fail → row back to `In Progress` with the expected-vs-actual and the failing repro.
     Never mark an unchecked criterion as done.
   - Stop conditions: round cap reached, a critical path red (money, data loss, auth, security —
     immediate `Blocked`), the same fingerprint filed twice (the existing row is escalated to
     `Blocked`), or the human says stop.
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
