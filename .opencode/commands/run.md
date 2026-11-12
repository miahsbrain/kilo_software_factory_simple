---
description: Run the Build → QA → Review loop for one board row and leave it pending merge
---

You are the **orchestrator** for a single SQLite board row. Work happens in the task worktree;
only you update board rows through `board.py`.

Before the task, read `.opencode/catalog/README.md`, apply all relevant skills and required
references under `AGENTS.md` §A7, and report skills used or that none matched.

1. **Pick** the row: highest-priority `Ready`, not blocked by another row. Grade it
   low/medium/high (§B4 "Task grading") to set the rigor of review.
2. **Build** in the worktree named after the feature. Create it from the board row if it does not
   exist: `python3 .opencode/skills/git-worktree/scripts/worktree.py create --board <ID>`
   (the branch type and slug are derived from the row).
   - Implement the smallest change that satisfies every acceptance criterion.
   - Update the scope docs (`HANDOVER.md`, `BUSINESS-LOGIC.md`, `ARCHITECTURE.md`,
     `DECISIONS.md`, `changelog/`) in the same change set (§B1).
    - Do **not** edit the SQLite board from a builder worktree.
   - Run the project's verification command from `docs/STACK.md`.
   - Commit locally on the worktree branch. Never push, never merge, never open a PR.
   - Run `python3 .opencode/skills/git-worktree/scripts/guard.py check-git -- "<command>"` before any git
     command that changes history or the remote. A denied command is not run; a command that needs
     approval waits for the user.
3. **QA** — produce evidence, not assertion. One observable check per acceptance criterion,
   with the command and result and `file:line`. For UI work, capture screenshots.
   - Load `browser` first and use only OpenCode's built-in browser for UI verification/review
     (§B4.2, QA skill). Use interactions, screenshots, DOM measurements, console and network
     observations. No Playwright, browser MCP alternatives or `browser-review.mjs`. Hold an
     unavailable browser/measurement criterion and report the limitation without fallback.
   - UI artifacts land in the one canonical folder at the repository root:
     `artifacts/<scope>/qa/<date>/<task-id>/`. Record route, viewport, theme, steps, expected and
     observed results; transfer browser captures using server-local paths, not desktop paths.
      Review reports and ledger stay under `<git-common-dir>/reviews/`, outside task worktrees.
   - A row goes through at most **3** QA↔fix rounds. Round 3 is the last. Each round's review is
      done by a fresh reviewer that reads `<git-common-dir>/reviews/<task-id>-ledger.md` and current
     screenshots, not the previous reviewer's reasoning. The ledger script opens and closes rounds:
     `python3 .opencode/skills/qa-review/scripts/ledger.py next-round --task-id BOARD-005`.
    - Findings are deduplicated by fingerprint (`kind|category|route|subject`). Record them in
      the ledger and original row notes. Reuse the same builder and worktree; never open an
      automatic Fix row for an in-task finding. A distinct defect needs independent approval.
   - Pass → continue to Review.
   - Fail → row back to `In Progress` with the expected-vs-actual and the failing repro.
     Never mark an unchecked criterion as done.
   - Stop conditions: round cap reached, a critical path red (money, data loss, auth, security —
     immediate `Blocked`), the same fingerprint filed twice (the existing row is escalated to
      `Blocked`), or the human says stop.
4. **Review** — read the diff and the acceptance criteria first, form your own hypotheses, then
   compare against the builder's summary (§A8). Re-run the exact verification command the QA
   lane used. Any blocking finding → row back to `In Progress` with the finding restated.
   For frontend work, also run the independent UI/UX critique lane (`/ui`) — both must be green,
   the unslop audit recorded, and gallery approval and accessibility gates satisfied.
5. **Merge gate** (§B4): all criteria verified, verification passed, QA evidence present, review
   clean, docs updated, and `worktree.py verify <slug>` printing `READY FOR MERGE` → set the row
   to `Pending Merge` with `board.py set-status`.
   That state means the work is waiting for human approval to merge.
6. **Hand off.** Report the worktree path, the branch, the commits, and the review commands.
   Recheck the live worktree and board under §B11's merge-guidance gate. Print the block from
   `python3 .opencode/skills/git-worktree/scripts/worktree.py handoff --board <ID>`.
   Only finished, verified, reviewed, committed, clean `Pending Merge` work gets merge guidance.
   Otherwise provide only review/diff commands and blockers, never manually added merge or teardown.
    Never merge, invoke `finalize`, push, or open a PR yourself.

Report in this order: what was done, what is proven, what is not done and why, next action.
