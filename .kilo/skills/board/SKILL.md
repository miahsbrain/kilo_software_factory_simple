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

For the read-only viewer, run `python3 .kilo/skills/board/scripts/board_serve.py --port 15180` as a tracked background process and report readiness and URL.
