---
description: Run the Build → QA → Review loop for one board row and leave it pending merge
---

You are the **orchestrator** for a single board row. The work happens in the worktree; the board
stays in the main checkout and only you write it.

1. **Pick** the row: highest-priority `Ready`, not blocked by another row. Grade it
   low/medium/high (§B4 "Task grading") to set the rigor of review.
2. **Build** in the original assigned repo-specific workspace set. Reuse it for fixes, QA,
   critique, docs and conflict resolution. Link findings with `worktree.py create --board <FIX>
   --reuse <PARENT> --repo <ID>`. Create only for an explicitly requested workspace or the next
   approved task after the previous merged, never automatically after merge. Required mode is
   default; optional permits the assigned nonprotected current checkout. Use `worktree.py mode
   required|optional|status` to select/report mode and restart Kilo after permissions regenerate.
   - Implement the smallest change that satisfies every acceptance criterion.
   - Update the scope docs (`HANDOVER.md`, `BUSINESS-LOGIC.md`, `ARCHITECTURE.md`,
     `DECISIONS.md`, `changelog/`) in the same change set (§B1).
   - Do **not** edit `docs/BOARD.md` from the worktree.
   - Run the project's verification command from `docs/STACK.md`.
   - Commit locally on the worktree branch. Never push, never merge, never open a PR.
   - Run `python3 .kilo/skills/git-worktree/scripts/guard.py check-git -- "<command>"` before any git
     command that changes history or the remote. A denied command is not run; a command that needs
     approval waits for the user.
3. **QA** — produce evidence, not assertion. One observable check per acceptance criterion,
    with the command and result and `file:line`. For UI work, capture screenshots.
    - Application source stays read-only; approved auth/navigation and evidence writes are allowed.
      Use existing capture `--storage-state`/`--navigation` ignored local JSON per the QA skill.
      Ask for test access if absent, leave MFA/SSO to the user, and never bypass auth. Explicit
      destructive authorization is required for `--allow-destructive`; no secrets in evidence/CLI.
   - The capture script is the only way to capture UI evidence. Ad-hoc `chromium`, `npx playwright
     screenshot`, `curl`-and-guess, or any other browser command from bash is not acceptable
     evidence. The script never installs a browser and never falls back to another driver. If
     the script cannot do something the review needs, say what is missing and propose the change
     — a change to a project tool is a reviewed change, not a silent patch mid-review. Do not
     work around it with another tool.
   - UI artifacts land in the one canonical folder at the repository root:
     `artifacts/<scope>/qa/<date>/<task-id>/`. The script computes that path itself. Review reports
      findings and ledgers live in ignored `artifacts/reviews/` in the control main checkout,
      shared by worktrees. Never stage or commit any artifacts. Report names are `<task-id>-qa.md`,
      `<task-id>-ui.md`, `<task-id>-review.md`; the ledger is `<task-id>-ledger.md`.
   - A row goes through at most **3** QA↔fix rounds. Round 3 is the last. Each round's review is
      done by a fresh reviewer that reads shared `artifacts/reviews/<task-id>-ledger.md` and the current
     screenshots, not the previous reviewer's reasoning. The ledger script opens and closes rounds:
     `python3 .kilo/skills/qa-review/scripts/ledger.py next-round --task-id BOARD-005`.
   - Findings are deduplicated by fingerprint (`kind|category|route|subject`). `check-finding.py`
     prints it; `board.py add --fingerprint` refuses a fingerprint that is already open and prints
     the command that updates the existing row.
   - Pass → continue to Review.
    - Fail → row back to `In Progress` with expected-vs-actual and repro, unless a stop condition applies.
     Never mark an unchecked criterion as done.
    - If round 3 ends with unresolved blocking findings, stop automatically. Highlight remaining
      problems, severity, user impact, evidence and attempted fixes. Record the stop reason and
      request `Blocked` status from the orchestrator. Ask the user how to proceed, directly when
      interactive or through the orchestrator when delegated. Offer a revised approach, defer/drop,
      or explicitly scoped follow-up. Never start round 4, reset the ledger or claim completion.
      Successful round 3 follows the normal merge gate, without automatic `Blocked` status.
    - Other stop conditions: a critical path red (money, data loss, auth, security —
     immediate `Blocked`), the same fingerprint filed twice (the existing row is escalated to
     `Blocked`), or the human says stop.
4. **Review** — read the diff and the acceptance criteria first, form your own hypotheses, then
   compare against the builder's summary (§A8). Re-run the exact verification command the QA
   lane used. Blocking findings → `In Progress`, unless a §B4.4 stop condition requires `Blocked`.
   For frontend work, also run the UI/UX critique lane (`/ui`) — both must be green.
5. **Merge gate** (§B4): all criteria verified, verification passed, QA evidence present, review
   clean, docs updated, and `worktree.py verify <slug>` printing `READY FOR MERGE` → set the row
   to `Pending Merge` with `board.py set-status`.
   That state means the work is waiting for human approval to merge.
6. **Hand off.** Run `python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <ID>`
   to print all repo diffs and human `merge --board <ID> --apply` commands (repeat `--board` for
   batches). Preflight all sources/targets clean except live board metadata, readiness and commits.
   Multi-repo merge is non-atomic: preserve partial state and stop on conflict. Assign the specialist
   to the existing conflicted checkout; the human completes it after review/checks then retries.
   Only full completion marks rows Merged; cleanup is automatic. Never merge, push or open a PR.
   Discard is separate: human preview `discard --board <ID> --repo <ID>`, then only explicit loss
   approval permits `--apply --discard`. Never discard unasked. Do not untrack board.py or BOARD.md.

Report in this order: what was done, what is proven, what is not done and why, next action.
