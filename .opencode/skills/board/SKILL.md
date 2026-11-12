---
name: board
description: Read and update the live SQLite board — add rows, move lanes, set fields — with board.py. Markdown is a generated export.
---

# Board

The live board is `<primary-checkout>/.factory-state/factory-board.sqlite3`, local to this clone and shared across
worktrees. Scripts resolve the primary checkout from Git's absolute common-dir path and fail closed if it cannot be verified. Only the orchestrator edits rows through `board.py`; the human-only finalize command
owns its successful integration transition. `docs/BOARD.md` is a one-time legacy import source,
not a live board. `board.py export` generates Markdown in `.factory-state/` on request.

First use imports an existing local main-checkout legacy board once and keeps its original bytes
as a SQLite snapshot. If legacy runtime data remains in Git metadata while the new database is
absent, normal board commands fail closed unless the atomic migration-completion manifest confirms
the complete snapshot was installed and its expected items remain; run the explicit runtime-state
migration first. A fresh clone with no legacy runtime state starts empty. Never import a historical
Git-tracked board into a fresh clone. Back up SQLite consistently or export before moving clones.
Viewer requests stay read-only and never initialize another registered project's board.

- **Worktree branches never edit the board.** A builder reports its lane status; the orchestrator
  writes the board.
- The script is the only sanctioned way to change it. Hand-editing the table loses the column
  alignment and risks corrupting a row.
- One orchestrator at a time. Never two agents writing the board.

---

## 1. The script

```bash
python3 .opencode/skills/board/scripts/board.py --help
```

Python 3.9+, standard library only. SQLite transactions merge disjoint cell edits and reject
overlapping edits; an explicit Markdown export is a snapshot, not a second source of truth.

| Command | Does |
|---|---|
| `board.py show [ID]` | print active rows, or one active row, after normalized migration |
| `board.py plan accept` | atomically accept a JSON array from stdin and assign IDs |
| `board.py plan queue` | list queued items in queue order |
| `board.py plan history` | list completed/cancelled items in display order |
| `board.py plan promote <ID>` | promote queued work to `Ready` |
| `board.py plan complete <ID>` | retain active work as completed history |
| `board.py plan cancel <ID>` | retain queued or active work as cancelled history |
| `board.py add --id ...` | append a legacy row only before normalized migration |
| `board.py add-column --name <Col> [--after "<Col>"]` | insert a column only before normalized migration |
| `board.py set-status <ID> "<status>"` | change an active item to another active status |
| `board.py set-field <ID> --field <field> --value "<value>"` | change one permitted field |
| `board.py remove <ID>` | cancel and retain a normalized item |
| `board.py lanes` | count active rows per lane |
| `board.py export` | generate an active-only Markdown snapshot in `.factory-state/` |

The columns are:

    ID | Task | Type | Status | Priority | Risk | Blocked by | Repos | Branch/Worktree | Notes

**Repos** holds the repo ids from `.opencode/repos.json` that the row touches, comma
separated (`api`, `api,control`). It is written by `worktree.py create --repo`
and can be set by hand:

```bash
python3 .opencode/skills/board/scripts/board.py add --id BOARD-00X --task "..." \
  --type Feature --status Ready --priority P2 --risk "🟡 medium — one line" \
  --blocked-by "None." --repos "api"

python3 .opencode/skills/board/scripts/board.py set-field BOARD-00X \
  --field repos --value "api,control"
```

A table that predates the `Repos` column is migrated with the script, never by
hand:

```bash
python3 .opencode/skills/board/scripts/board.py add-column --name Repos --after "Blocked by"
```

It inserts the header cell in the right place, gives every row an empty cell in
that column, keeps every other cell's bytes, refuses when the column already
exists, and refuses when a row has a different cell count from the header.

---

## 2. Lanes

Queued plans are stored in `planned_items` with `queue_position`; they are not active work.
Promotion creates one `active_work` reference with status `Ready`. Active work uses
`Ready` → `In Progress` → `In Review` → `Pending Merge`, plus `Blocked` (parked for a human).
Completed and cancelled items remain in history and are not active.

| Lane | Meaning |
|---|---|
| `Backlog` | Queued plan, ordered by `queue_position`; not active |
| `Ready` | Promoted plan with one active-work reference |
| `In Progress` | Worktree exists, Build lane running |
| `In Review` | Build done, QA and Review lanes running |
| `Pending Merge` | Green. **Waiting for human approval to merge** |
| `Merged` | Compatibility label for completed history; human finalize owns successful integration |
| `Blocked` | Parked for a human: needs a decision, unclear scope, or duplicate |
| `Dropped` | Compatibility label for cancelled history; the reason is retained |

Types: `Feature` `Fix` `Chore` `Docs` `Research`.

---

## 3. A plan before acceptance

Every row carries:

- **User story** — required for newly accepted plans; legacy rows without one stay blank.
- **Acceptance criteria** — 2–5 checkable items, each verifiable by a test or an observable step.
  New plans cannot be accepted without them.
  A **Feature** row also carries a reuse criterion — which existing code was extended, or the
  reason there was none to extend.
- **Risk** — `🟢 low` / `🟡 medium` / `🔴 high` plus one line of reasoning.
- **Blocked by** — existing Board IDs or temporary keys in the same accepted batch.
- **Notes** — retain context verbatim; criteria are stored separately after migration.

### Planning before persistence
- Before a feature plan is persisted, present a conversation preview with each item’s user story, 2–5 checkable acceptance criteria, dependencies, priority, risk, and order.
- Persist nothing until the user explicitly accepts the whole proposal or a selected subset. Persist only accepted items, preserving their preview order.
- The planned item is canonical. Promotion creates one active-work reference to it; only promoted items appear in Active. Completion or cancellation removes that reference and retains the planned item in history.

---

## 4. The flow

```bash
# 1. read active work and the queue/history before anything
python3 .opencode/skills/board/scripts/board.py show
python3 .opencode/skills/board/scripts/board.py plan queue

# 2. after explicit user acceptance, persist the selected preview batch
python3 .opencode/skills/board/scripts/board.py plan accept <<'JSON'
[{"key":"export","task":"Add the export endpoint","type":"Feature","priority":"P2",
  "risk":"🟡 medium — one new endpoint, one new consumer",
  "user_story":"As an operator, I can export the board",
  "acceptance_criteria":["POST /api/export returns a CSV","The export is covered by a test"],
  "blocked_by":[],"repos":["control"],"notes":""}]
JSON

# 3. promote queued work, then move only among active statuses
python3 .opencode/skills/board/scripts/board.py plan promote BOARD-00X
python3 .opencode/skills/board/scripts/board.py set-status BOARD-00X "In Progress"
python3 .opencode/skills/board/scripts/board.py set-status BOARD-00X "In Review"
python3 .opencode/skills/board/scripts/board.py set-status BOARD-00X "Pending Merge"

# 4. human-only finalize coordinates merge, cleanup and Merged lane from base checkout
python3 .opencode/skills/git-worktree/scripts/worktree.py finalize --board BOARD-005
```

`board.py remove <ID>` is cancellation, not deletion. `plan complete` and `plan cancel` retain the
canonical item, criteria and terminal outcome. After normalized migration, `add-column` is refused
because the SQLite schema is fixed; use `plan accept` for every new item.

When the worktree exists, record it:

```bash
python3 .opencode/skills/board/scripts/board.py set-field BOARD-005 \
  --field branch-worktree --value ".opencode/worktrees/export-endpoint · branch feat/export-endpoint"
```

---

## 5. Findings stay in the task

A QA or UI/UX finding on the current task sends its row back to `In Progress`. Record evidence
in the local ledger and row notes; resume the same builder in the existing worktree, then repeat
QA and review. Do not create a Fix row or a second worktree for in-task corrections. A distinct,
independently approved defect may be scoped as a separate Fix task.

---

## 6. See it live

SQLite is the source of truth. The **factory board console**
renders it as a dense, keyboard-first dashboard you can open in a browser:

```bash
python3 .opencode/skills/board/scripts/board_serve.py --port 15180
```

The console is styled with Tailwind CSS v4. The stylesheet is prebuilt and committed, so the
viewer needs no Node at runtime. After changing a class, rebuild it:

```bash
npm --prefix .opencode/skills/board/ui run build   # -> .opencode/skills/board/static/board.css
```

`/gallery` renders the same `wb_` components the board uses; approve it before a screen changes.
The runtime serves the CSS and the two self-hosted Geist fonts from `.opencode/skills/board/static/`.

Before a task, apply `AGENTS.md` §A7's catalogue selection/reporting rule. UI verification/review
of the board and gallery follows §B4.2 and the QA skill: load `browser` first, use only OpenCode's
built-in browser interactions, screenshots, DOM measurements, console and network observations.
Store evidence under `artifacts/factory/qa/<date>/<task-id>/` with route, viewport, theme, steps,
expected and observed results. Transfer captures using returned server-local paths; do not assume
a shared desktop/server disk. Hold unavailable access/measurements without fallback. Gallery
approval, independent review, accessibility and unslop gates remain mandatory.

- An **app bar** carries the wordmark, the live refresh clock, Pause, Refresh now, and the
  system/light/dark theme and comfortable/compact density toggles.
- A **pipeline** strip counts the active lanes; each lane button filters the cards and is the
  primary way to read the shape of the flow.
- A **toolbar** holds search (`/`), status, type and priority filters, the result count, and
  Reset. The filter state lives in the URL, so a view can be bookmarked and shared.
- Every **card** shows its ID, task, type, priority, risk badge, `Blocked by`, and worktree. The
  parsed **Notes checklist** renders each criterion with its checked/open state and proof line,
  so acceptance criteria are readable without opening the markdown.
- A **live worktrees** table shows each worktree with its branch, path, ahead/behind counts, and
  a dirty marker; a branch can be copied from the card.
- Keyboard: `/` focuses search, `j`/`k` move between cards, `Enter` opens one, `Esc` closes or
  clears. Focus rings and accessible names are present throughout.
- The board is re-read on **every request** and the page auto-refreshes. Nothing is cached.
- Requests are **read-only and offline**: standard library only, no external assets. Startup
  alone may initialize the current control board when absent; it never changes existing bytes.
- `/api/board` and `/api/worktrees` serve the same data as JSON, unchanged.

The port is forwarded by the devcontainer as **Factory Board (15180)**.

## 7. Rules

- **The board is the source of truth.** Re-read it at the start of every session and every task.
  A row's status must match reality.
- **Never silently drop a row.** A task that cannot proceed moves to `Blocked` with a one-line
  reason and what unblocks it.
- **`Merged` means the user merged it.** Never "the agent finished".
- **`Blocked by` defines the order of work.** Settle shared contracts, schemas, and file layouts
  on the base branch before fanning out to parallel worktrees.
- **One orchestrator.** Never run two orchestrators against the same board.
