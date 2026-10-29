---
name: board
description: Read and update the live work board at docs/BOARD.md — add rows, move lanes, set fields — without hand-editing the markdown table. Use whenever work is planned, started, reviewed, or finished.
---

# Board

`docs/BOARD.md` is the single source of truth for what is going on. It lives in the **main
checkout**, and the orchestrator is its **only writer**.

- **Worktree branches never edit the board.** A builder reports its lane status; the orchestrator
  writes the board.
- The script is the only sanctioned way to change it. Hand-editing the table loses the column
  alignment and risks corrupting a row.
- One orchestrator at a time. Never two agents writing the board.

---

## 1. The script

```bash
python3 .kilo/skills/board/scripts/board.py --help
```

Python 3.9+, standard library only. It rewrites the file atomically and refuses to touch it when
the table cannot be parsed.

| Command | Does |
|---|---|
| `board.py show [ID]` | print all rows, or one row |
| `board.py add --id ... --task ... --type ... --status ... --priority ... --risk ...` | append a row |
| `board.py set-status <ID> "<status>"` | change one cell: the status |
| `board.py set-field <ID> --field <field> --value "<value>"` | change one cell |
| `board.py remove <ID>` | delete a row |
| `board.py lanes` | count rows per lane |

---

## 2. Lanes

`Backlog` → `Ready` → `In Progress` → `In Review` → `Pending Merge` → `Merged`
plus `Blocked` (parked for a human) and `Dropped` (abandoned).

| Lane | Meaning |
|---|---|
| `Backlog` | Identified, not started |
| `Ready` | Scoped, has acceptance criteria, can be picked up |
| `In Progress` | Worktree exists, Build lane running |
| `In Review` | Build done, QA and Review lanes running |
| `Pending Merge` | Green. **Waiting for human approval to merge** |
| `Merged` | The user merged it; the worktree can be cleaned up |
| `Blocked` | Parked for a human: needs a decision, unclear scope, or duplicate |
| `Dropped` | Abandoned; the reason is recorded |

Types: `Feature` `Fix` `Chore` `Docs` `Research`.

---

## 3. A row before it leaves `Backlog`

Every row carries:

- **Acceptance criteria** — 2–5 checkable items, each verifiable by a test or an observable step.
  A task with no checkable criteria is not ready to build.
  A **Feature** row also carries a reuse criterion — which existing code was extended, or the
  reason there was none to extend.
- **Risk** — `🟢 low` / `🟡 medium` / `🔴 high` plus one line of reasoning.
- **Blocked by** — board IDs it depends on, or exactly `- None.`
- **Notes** — the acceptance criteria and any context, so the next agent can pick it up cold.

---

## 4. The flow

```bash
# 1. read the board before anything
python3 .kilo/skills/board/scripts/board.py show

# 2. add the row before starting work
python3 .kilo/skills/board/scripts/board.py add \
  --id BOARD-005 --task "Add the export endpoint" --type Feature --status Ready \
  --priority P2 --risk "🟡 medium — one new endpoint, one new consumer" \
  --blocked-by "None." --branch-worktree "-" \
  --note "- [ ] POST /api/export returns a CSV
- [ ] the export is covered by a test"

# 3. move it as the work advances
python3 .kilo/skills/board/scripts/board.py set-status BOARD-005 "In Progress"
python3 .kilo/skills/board/scripts/board.py set-status BOARD-005 "In Review"
python3 .kilo/skills/board/scripts/board.py set-status BOARD-005 "Pending Merge"

# 4. after the human merges
python3 .kilo/skills/board/scripts/board.py set-status BOARD-005 "Merged"
```

When the worktree exists, record it:

```bash
python3 .kilo/skills/board/scripts/board.py set-field BOARD-005 \
  --field branch-worktree --value ".kilo/worktrees/export-endpoint · branch feat/export-endpoint"
```

---

## 5. Findings become rows

A QA or UI/UX finding is a **bug-fix unit of work**. The reviewer reports it; the orchestrator
creates the row:

- `Type: Fix`
- `Status: Ready` — or `Blocked` when the finding needs a product decision
- `Priority` from the finding severity
- `Risk` from the blast radius of the defect
- `Blocked by: BOARD-xxx` — the row that produced the finding
- `Notes` — expected, actual, repro, evidence path

A FAIL verdict sends the reviewed row back to `In Progress` with the findings restated. A PASS
lets it proceed to `Pending Merge`.

---

## 6. Rules

- **The board is the source of truth.** Re-read it at the start of every session and every task.
  A row's status must match reality.
- **Never silently drop a row.** A task that cannot proceed moves to `Blocked` with a one-line
  reason and what unblocks it.
- **`Merged` means the user merged it.** Never "the agent finished".
- **`Blocked by` defines the order of work.** Settle shared contracts, schemas, and file layouts
  on the base branch before fanning out to parallel worktrees.
- **One orchestrator.** Never run two orchestrators against the same board.
