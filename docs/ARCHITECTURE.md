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

`worktree.py clean-slate --repo <id>` delegates a read-only, closed inventory to
`project_reset.py`. It requires a local standalone control map and verified primary checkout;
shared-board app scopes are refused. It reads normalized SQLite through the existing immutable
reader only when there are no sidecars, never initializing or migrating state. Linked worktrees,
active references and unknown evidence ownership block execution. Runtime recovery/migration
copies remain disclosed and retained. The project-only document allowlist and portable
`git-worktree/templates/project-v1/manifest.json` define replacement hashes. Factory documents
are preserved. Human-only `--apply` requires the selected primary checkout and exact repository ID
plus canonical path on stdin/stderr TTYs. This is the same local deterrence boundary as purge,
not an OS security boundary against code with the same identity.

Reset authority stays in `project_reset.py`, separate from purge's target vocabulary. It reuses
purge's safe paths, stamps, private copy and durable publication, the runtime resolver/snapshot
adapter, and the canonical SQLite writer transaction (`BEGIN IMMEDIATE`). Mandatory
`.factory-state/clean-slates/<operation-id>/manifest.json` records exact filesystem and logical DB
pre/postimages before reset effects. Optional private backup attempts finish and verify first.
Per-node deletion avoids ambiguous partially deleted trees; replacements publish staged new inodes.
Each unpublished document preparation records its unique `replacement-<step-index>-<uuid>` attempt
before exclusive creation. A pending interrupted write is retained, never overwritten or deleted;
confirmed resume prepares a fresh exclusive attempt. After a running postimage is durable, resume
requires that exact stage or already-published inode; modified stages and targets still refuse.
Canonical emptying commits last, preserving schemas and ID high-water while replacing stale
projection prose with the canonical empty view. Crash recovery requires explicit
`--resume <operation-id>` plus fresh named confirmation, verifies saved ownership/pre/postimages
even when the board is empty, and refuses drift/recreated targets. Historical copies and incomplete
backup attempts remain; there is no automatic rollback. No dependency, new lock framework, guard
bypass or change to purge behavior is introduced. Independent destructive-flow QA is still pending.

Task purge is a narrow human-only exception to cancellation retention. `worktree.py purge`
delegates inventory and recovery to `task_purge.py`, sharing board projections, the primary
checkout resolver, repository mapping, protected-branch policy and durable journal publication.
Preview uses the same read-only SQLite boundary as the viewer, never initializes/migrates state,
and lists exact resources. Apply requires the primary control checkout, a terminal and an exact
task-ID confirmation. Dependent tasks, foreign repositories, symlinks and changed targets refuse.
Existing cancelled tasks need explicit orphan ownership evidence; unclaimed worktrees refuse
rather than infer ownership from names. Ordinary cancellation/discard/finalization are unchanged.

`.factory-state/purges/<ID>/manifest.json` records phases under an exclusive POSIX lock and a
SQLite immediate transaction. Filesystem/Git steps precede canonical deletion; failures retain
the task and durable metadata for inspected retry. A crash after SQLite commit is recognized on
retry. Changed or partially removed trees refuse rather than delete content whose identity can
no longer be proven. Optional private content backups are separate from mandatory operational
metadata. Backup preparation records `copying` before copying into a fresh private UUID directory;
only fsynced, content-verified copies transition to `complete`. Retry preserves abandoned attempts,
verifies the completed copy against stored content digests, and never silently disables backup.
Nested `.git` markers of any type refuse; only the expected verified root worktree file is allowed.
Historical/shared backups, legacy copies and exports are retained and disclosed.
Git objects/history are not rewritten or erased; deleting the selected branch can remove its
reflog, and purge does not guarantee permanent retention of unreachable objects.
`plan_id_sequence` retains a monotonic allocation high-water
mark independently of task rows. No new dependency, clean-slate or slash shortcut is included.

- Clone-local factory runtime state lives at `<primary-checkout>/.factory-state/`, outside Git
  metadata. The live board is `.factory-state/factory-board.sqlite3`; Markdown is a one-time
  import or generated export, never the live state. Scripts resolve the primary checkout from
  Git's absolute common-dir path and fail closed when it cannot be verified.
- QA/UI reports and evidence live under `artifacts/<scope>/qa/<YYYY-MM-DD>/<task-id>/` in the
  primary checkout. Only bounded-loop ledgers live in `.factory-state/reviews/`; update them through
  `ledger.py`. Cleanup recovery journals and backups live in `.factory-state/cleanup-wt/<repo-id>/`
  to keep repository identities separate.
- The native-file guard's QA edit exception uses the existing runtime-state primary-checkout
  resolver, not a path substring or worktree-list authority. Only canonical non-symlink outputs
  under `artifacts/{web,api,mobile,factory}/qa/YYYY-MM-DD/<task>/` qualify; traversal, hidden
  components and nested/foreign repositories do not. This removes only the worktree-location
  gate: file policy and OpenCode role-specific permissions still apply. Shell policy is unchanged.
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
- QA and review use specialist agents; UI evidence uses the existing Playwright capture script
  and configured MCP for interaction, alongside the
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
