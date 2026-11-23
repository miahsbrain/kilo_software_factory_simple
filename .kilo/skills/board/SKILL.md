---
name: board
description: Read and update the live work board at docs/BOARD.md — add rows, move lanes, set fields — without hand-editing the markdown table. Use whenever work is planned, started, reviewed, or finished.
---

# Board

The live `docs/BOARD.md` is local to the main checkout. One coordinator writes it through `.kilo/skills/board/scripts/board.py`; builders report status. Keep the script tracked and the template board blank for initialization.

```bash
python3 .kilo/skills/board/scripts/board.py show
python3 .kilo/skills/board/scripts/board.py add --id BOARD-005 --task "Describe the task" --type Feature --status Ready --priority P2 --risk "medium - affected flow" --blocked-by "None." --repos control --note "Acceptance criteria and relevant context"
python3 .kilo/skills/board/scripts/board.py set-status BOARD-005 "In Progress"
python3 .kilo/skills/board/scripts/board.py set-field BOARD-005 --field notes --value "Current evidence and blockers"
python3 .kilo/skills/board/scripts/board.py note BOARD-005 --value "Additional evidence"
```

Check existing rows before adding work. Record checkable acceptance criteria, risk, dependencies, mapped repo IDs, and assigned workspace. Lanes are `Backlog`, `Ready`, `In Progress`, `In Review`, `Pending Merge`, `Merged`, `Blocked`, and `Dropped`. Keep status truthful: finished implementation is not a merge. Lifecycle commands record merge/cleanup/discard outcomes; do not fabricate them.

Consolidate review findings once. Use `check-finding.py` from the QA skill for actionable Fix rows and its fingerprint to avoid duplicates. Fixes reuse the original workspace. Record a blocker and what resolves it rather than silently dropping work.

Board gallery and review guidance is subject to `worktree.py reviews status`. Follow `/components` and `/ui` for the independent gates. Link the manual QA/UI checklist for skipped scopes even without a blocker; policy skips and checklist delivery do not change a lane or prove a pass.

## Manual Review

Read `board.py show <ID>` before requesting review. Record a pending manual decision in `Blocked by` as `review:<scope>`, using a lowercase kebab-case identifier for the specific deliverable and revision, e.g. `review:checkout-flow-v2`. Separate independent blockers with semicolons; keep all existing reasons. Never infer approval from a passing test, screenshot, silence or an agent's report.

Only after the user explicitly approves that scope, the coordinator records the decision once:

```bash
python3 .kilo/skills/board/scripts/board.py approve-review BOARD-005 --scope checkout-flow-v2 --evidence "User accepted checkout flow v2 in review message 42"
```

`show` exposes the Notes entry `[user-approved:checkout-flow-v2]` and its evidence. Append notes instead of replacing approval history. Honor that decision for the same scope and revision; do not ask again or re-block solely for missing automated review of that decision. Material changes need a new scope. The command clears only the exact `review:<scope>` entry. A `Blocked` row returns to `In Review` only if that was its last reason; unknown or legacy free text is never guessed away. A duplicate fingerprint is refused without changing the original row. Escalate a genuine new blocker explicitly with its reason.

Before recording a decision, compare the revision the user saw with the current deliverable. Replace a superseded gate with a fresh revision-specific scope; never relabel an old decision as approval of the new revision. A repeat for an already recorded scope leaves the row and first evidence unchanged. A new decision must match a pending review gate if any are listed. Legacy rows without a structured gate can still record evidence, so the coordinator must verify the revision even there.

This records a review outcome, not a QA pass, commit, merge, or permission to start new work. Independently verify outstanding criteria and lifecycle prerequisites.

For the read-only viewer, run `python3 .kilo/skills/board/scripts/board_serve.py --port 15180` as a tracked background process and report readiness and URL.
