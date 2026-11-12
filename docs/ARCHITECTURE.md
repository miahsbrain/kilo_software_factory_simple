# Factory architecture

## Shape

The factory is a local, single-user OpenCode control repository. It owns the harness, policies,
documentation and SQLite task board. Product repositories live separately and are accessed only
through explicit IDs in `.opencode/repos.json`.

```text
OpenCode architect
  ├── SQLite board (task state and dependencies)
  ├── isolated Git worktrees (one task per worktree)
  ├── specialist builders → QA reviewer → independent review
  └── human-only integration gate

Read-only dashboard
  ├── SQLite board rows and lanes
  └── Git branch/worktree metadata
```

The default product shape is a monorepo under `/projects/<project-id>`, with one app per `apps/`
folder. A service may become a separate repository when it has independent ownership or release
needs. Every work surface must be registered before the factory reads its contents.

## State and boundaries

- Clone-local factory runtime state lives at `<primary-checkout>/.factory-state/`, outside Git
  metadata. The live board is `.factory-state/factory-board.sqlite3`; Markdown is a one-time
  import or generated export, never the live state. Scripts resolve the primary checkout from
  Git's absolute common-dir path and fail closed when it cannot be verified.
- QA/UI reports and evidence live under `artifacts/<scope>/qa/<YYYY-MM-DD>/<task-id>/` in the
  primary checkout. Only bounded-loop ledgers live in `.factory-state/reviews/`; update them through
  `ledger.py`. Cleanup recovery journals and backups live in `.factory-state/cleanup-wt/<repo-id>/`
  to keep repository identities separate.
- Planned work, acceptance criteria, active work and terminal history are normalized in the same
  SQLite database. `planned_items` is canonical; `active_work` contains only promoted, nonterminal
  rows, and `acceptance_criteria` stores ordered checklist items and proof separately. Nullable
  queue positions order backlog work; terminal outcomes retain completed/cancelled history. New
  items enter through an explicitly accepted JSON batch; validation and dependency-key resolution
  are pure, ID assignment and insertion occur under one SQLite write transaction, and the batch is
  all-or-nothing. Promotion creates one `Ready` active reference; completion/cancellation remove
  it without deleting the canonical item or its criteria. Queue and history are separate CLI views.
  Existing board CLI and worktree callers retain their Markdown-table interface as a compatibility
  projection. The explicit `migrate-normalized` command previews by default and requires `--apply`
  to back up and transactionally migrate the imported snapshot; it never runs at startup.
  Legacy Notes may contain multiple checklist criteria separated by `; - [ ]`; each checkbox,
  verification state and explicit proof is stored separately without rewriting Notes. Removing a
  normalized row through the compatibility CLI cancels it: active/queue references are cleared,
  while the canonical item and its history are retained. After explicit migration, `show`, `lanes`,
  and `export` expose active work only; planned queue/history use their dedicated commands. Normal
  worktree writers update normalized state through the board compatibility API; the human finalize
  writer records `Merged` as completed history inside its existing transaction.
- The explicit runtime-state migration command supports dry-run and `--apply`; all legacy database
  writers must be stopped first. It copies the database and WAL/SHM files read-only into private
  staging, checks source metadata and content before and after the copy, then backs up and verifies
  only the staged SQLite copy. It installs the complete state tree atomically without deleting
  Git-metadata sources. Existing destinations must match the complete snapshot exactly; partial,
  extra, or differing state is refused. A completion manifest gates normal writers while legacy
  state remains.
- Git is the source of branch and worktree state. The board's `Branch/Worktree` cell links a task
  to its isolated worktree.
- The dashboard is read-only. It shows board state, branches and worktrees. It does not expose
  OpenCode sessions, dispatch agents, write board rows or maintain a second run-history table.
- `/api/planned-work` is a read-only factory-control-board endpoint. It reads normalized queue and
  terminal history through the safe read-only SQLite boundary, excluding active items. It shares the
  canonical normalized row query with the CLI and holds one explicit read transaction across related
  selects; request handling does not initialize or migrate data.
- OpenCode's architect coordinates specialist agents. The approved builder limit is two total and
  one per repository. This policy is not enforced until BOARD-133 is complete.
- A `factory-dev` specialist is approved for control-repo board/worktree/guard tooling, but its
  exact agent rule and permission entry still need A9 approval (BOARD-143).
- QA and review use specialist agents; UI evidence uses OpenCode's built-in browser and the
  approved gallery/anti-slop checks. BOARD-130 remains Blocked, so the approved task-local evidence
  path is not yet integrated into the base branch.
- A task becomes Pending Merge only after acceptance evidence, verification, independent review,
  documentation and a clean committed worktree. The human alone integrates it.

## Runtime and dependencies

The board and dashboard use Python standard-library SQLite and HTTP. The dashboard runs on loopback
port 15180. The viewer has no write endpoint. Node 22 is used only to author the committed Tailwind
stylesheet; no Node runtime or external service is required to serve the dashboard.

## Deferred architecture

The code-graph engine, graph dashboard, session APIs, dashboard dispatch, distributed workers and
multi-user service are deferred. Reconsider graph memory only after safe task execution,
registration, concurrency and QA have been proven.

See [DECISIONS.md](DECISIONS.md), [FACTORY_ROADMAP.md](FACTORY_ROADMAP.md), [RISKS.md](RISKS.md),
[API_CONTRACTS.md](API_CONTRACTS.md) and [STACK.md](STACK.md).
