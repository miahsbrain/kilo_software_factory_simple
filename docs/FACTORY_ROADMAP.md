# Factory implementation roadmap

**Updated:** 2026-11-12 · **Planning row:** BOARD-131
**State source:** the clone-local SQLite board is authoritative. This file is the readable plan and acceptance-criteria index; check `board.py show` for live status.

## Goal and approved scope

Build a reliable local OpenCode factory that can run a small number of independent tasks safely, gives a human a clear view of board state and worktrees, and leaves reviewable code and handovers.

- The dashboard is a read-only monitor of board rows, branches and worktrees. It does not show OpenCode sessions, dispatch agents, or mutate tasks.
- SQLite board rows and Git worktree metadata remain the only task/run state. Do not add a separate run-history table.
- Run at most two builders at once and no more than one builder per repository.
- Projects live in sibling repositories under `/projects/<project-id>`. A project is a monorepo by default; split an app into its own repository only for independent ownership or release. Register every repository explicitly.
- Keep the existing Python-standard-library dashboard, SQLite board, worktree scripts, reviewer agents, built-in browser QA and unslop gates. Do not add a framework or dependency without a new decision.
- Defer the code-graph engine until the core workflow is working. Do not add graph-engine tasks to this delivery.

## What already exists

| Capability | Current evidence | Plan treatment |
|---|---|---|
| Clone-local SQLite board, board CLI and task lanes | `docs/PROJECT_STRUCTURE.md:75-76`; `.opencode/skills/board/scripts/board.py` | Keep as the task source of truth. |
| Read-only dashboard with board lanes/cards and live worktrees/branches | `docs/UI-UX.md:384-418`; `README.md:172-176`; `.opencode/skills/board/scripts/board_serve.py:1629` | Preserve. Do not rebuild or add session controls. |
| Read-only board/worktree tests | `.opencode/skills/board/scripts/test_board_serve.py:92,420,736,792,817` | Extend only when a later task finds a coverage gap. |
| Worktree create/resume/discard/handoff/finalize gates | `.opencode/skills/git-worktree/scripts/worktree.py`; `docs/STACK.md:60-71` | Reuse and extend; human still owns integration. |
| Specialist agents, QA/UI review, anti-slop rules, handover skeleton | `.opencode/agents/`; `.opencode/catalog/README.md`; `templates/project/docs/handover/README.md` | Keep. No duplicate skill or dashboard implementation. |

## Current blockers and ordering

- BOARD-130 remains **Blocked** after its three QA rounds. The user chose to leave the dated historical note in `docs/PROJECT_STATE.md:78` unchanged. Do not reopen the review loop or create another Fix row for the same findings.
- The task-local artifact policy was approved, but BOARD-130 is not integrated. The base checkout still contains old review-artifact instructions. Any task that needs browser or reviewer artifacts in the task worktree waits on BOARD-130 unless the user changes that stop decision.
- BOARD-143 is the prerequisite for control-tool code work. Its exact permanent-rule and permission edits still need A9 approval. The remaining rows stay Backlog until dependencies and decision gates are settled.
- The dashboard already meets the read-only monitor request. No UI feature or OpenCode V2 session API task is planned.

## Backlog

Board statuses below are the planning snapshot for 2026-11-12. Live status and ownership belong to SQLite, not this table.

### Safe Git and concurrency

#### BOARD-143 — Add a scoped factory-dev specialist

**Status:** Backlog · **Type:** Chore · **Priority:** P1 · **Owner:** architect

**Start with:** `.opencode/agents/architect.md`, `opencode.jsonc` and a proposed new `.opencode/agents/factory-dev.md`.

- [ ] Present the exact new agent definition and permission entry for A9 approval before editing either permanent rule/config file.
- [ ] Scope the role to factory control tooling: board, worktree and guard scripts plus their tests; no product app code or board-row editing.
- [ ] Keep existing deny-by-default and Git/worktree safeguards intact.
- [ ] Verify OpenCode recognizes the role and the architect can invoke it within its scope; run the documented permission-policy consistency check.

#### BOARD-132 — Add guarded one-pass worktree commit command

**Status:** Backlog · **Type:** Chore · **Priority:** P1 · **Blocked by:** BOARD-143 · **Owner:** factory-dev

**Start with:** `.opencode/skills/git-worktree/scripts/worktree.py`, `guard.py`, lifecycle tests and `SKILL.md`.

- [ ] Accept a board ID and explicit commit message only for the row's live task worktree and recorded branch; refuse protected or mismatched branches.
- [ ] Stage and commit through separate guarded Git process invocations. Never join `git add` and `git commit` into one shell command.
- [ ] Test successful commit and refusal paths in a disposable repository; verify a refusal leaves the worktree and board unchanged.
- [ ] Document the one-pass command and its failure behavior. Keep the human merge/finalize gate unchanged.

#### BOARD-133 — Enforce builder concurrency limits

**Status:** Backlog · **Type:** Chore · **Priority:** P1 · **Blocked by:** BOARD-132 · **Owner:** factory-dev

**Start with:** `worktree.py`, board transaction helpers and lifecycle tests.

- [ ] Admit at most two rows in `In Progress` across the factory.
- [ ] Admit at most one `In Progress` builder for each repository ID; `In Review` no longer occupies a builder slot.
- [ ] Make simultaneous admission race-safe and refuse before leaving a partial worktree or board update.
- [ ] Cover limits, release on lane transition, and failure cleanup with temporary repository/SQLite tests.

#### BOARD-140 — Rehearse concurrent worktree admission

**Status:** Backlog · **Type:** Research · **Priority:** P1 · **Blocked by:** BOARD-133 · **Owner:** architect + QA reviewer

**Start with:** the concurrency tests and the documented worktree workflow.

- [ ] Run two independent admissions in parallel and confirm both records point to the right repository, branch and worktree.
- [ ] Confirm a same-repository third admission and a third global builder are refused without partial state.
- [ ] Record the exact command/results and any remaining manual coordination; use only disposable repositories.

### Project registration and starter quality

#### BOARD-134 — Align project layout rules with the approved repo model

**Status:** Backlog · **Type:** Docs · **Priority:** P1 · **Owner:** architect + docs-writer

**Start with:** `AGENTS.md`, `templates/project/AGENTS.md`, `docs/PROJECT_STRUCTURE.md`, `.opencode/repos.json` and `README.md`.

- [ ] Show exact proposed edits to permanent rule files and wait for the A9 approval before changing them.
- [ ] State that projects live at `/projects/<project-id>` and are registered explicitly through `.opencode/repos.json`.
- [ ] State that a project monorepo is the default; separate app repositories are for independent ownership or release.
- [ ] Preserve the rule that unregistered candidate discovery grants no repository-content access.

#### BOARD-135 — Write the project onboarding guide

**Status:** Backlog · **Type:** Docs · **Priority:** P1 · **Blocked by:** BOARD-134 · **Owner:** docs-writer

**Start with:** `README.md`, `docs/PROJECT_STRUCTURE.md`, `templates/project/README.md` and `guard.py` usage.

- [ ] Document copying the project skeleton into its own repository and registering the repo ID.
- [ ] Document the existing `guard.py check-repos` and `guard.py sync` steps; do not invent a bootstrap tool.
- [ ] Explain when to keep apps in the monorepo and when a service repository is justified.
- [ ] Verify every path and command against the current template and scripts.

#### BOARD-136 — Align project starter board documentation with SQLite

**Status:** Backlog · **Type:** Docs · **Priority:** P1 · **Owner:** docs-writer

**Start with:** `templates/project/docs/HANDOVER.md`, `PROJECT_STRUCTURE.md` and `README.md`.

- [ ] Say the live board is clone-local SQLite in the Git common directory.
- [ ] Describe `docs/BOARD.md` as a legacy import/starter only, not live runtime state.
- [ ] Keep project-template documentation consistent with the factory's read-only dashboard and board CLI.
- [ ] Preserve product-specific placeholders and make no runtime-code changes.

#### BOARD-137 — Smoke-test project registration and template sync

**Status:** Backlog · **Type:** Chore · **Priority:** P1 · **Blocked by:** BOARD-134, BOARD-135, BOARD-136 · **Owner:** factory-dev

**Start with:** existing `guard.py` and its repo-map/sync tests; use a temporary Git repository.

- [ ] Copy the project template into a disposable repository and register it by ID.
- [ ] Verify `check-repos` and the generated scope pointer match the registered path.
- [ ] Verify an unregistered candidate remains metadata-only and is not read as a board or work surface.
- [ ] Reuse existing tests and add only uncovered regressions.

### Memory, recovery and full workflow proof

#### BOARD-138 — Create a factory board-console memory map

**Status:** Backlog · **Type:** Docs · **Priority:** P2 · **Owner:** docs-writer

**Start with:** `.opencode/agents/docs-writer.md`, `docs/HANDOVER.md` and `board_serve.py` plus its tests.

- [ ] Add `docs/handover/README.md` and one `board-console.md` unit map.
- [ ] Cite every code claim with `file:line`; cover entry points, pure/effectful boundaries, data, routes, tests and known gaps.
- [ ] Link the map from `docs/HANDOVER.md` and `docs/PROJECT_STRUCTURE.md`.
- [ ] Have an independent reader locate the route, data source and test from the map without broad source reading.

#### BOARD-139 — Rehearse board backup and restore

**Status:** Backlog · **Type:** Research · **Priority:** P2 · **Owner:** factory-dev

**Start with:** `board.py`, `docs/STACK.md` and SQLite's existing Python standard-library support.

- [ ] Back up and restore a temporary WAL database without touching the live board.
- [ ] Confirm restored rows match and the generated Markdown export is not treated as the live board.
- [ ] Write a short recovery procedure and state which artifacts are clone-local.
- [ ] Do not add a new dependency or recovery command without a separate decision.

#### BOARD-141 — Rehearse two-repository builder concurrency

**Status:** Backlog · **Type:** Research · **Priority:** P1 · **Blocked by:** BOARD-130, BOARD-133, BOARD-137 · **Owner:** architect + specialist builders

**Start with:** the repo map, `worktree.py`, `/run` and the registered-repo tests.

- [ ] Use two independently registered repository IDs and two non-overlapping Ready tasks; if two suitable repos are not registered, stop and ask rather than reading candidates.
- [ ] Run at most two builders in parallel, one per repository; keep dashboard read-only and do not add a dispatcher/session view.
- [ ] Confirm board rows, branches and worktrees remain correctly isolated.
- [ ] Record the remaining manual coordination and stop before human-only finalize.

#### BOARD-142 — Run one end-to-end factory task rehearsal

**Status:** Backlog · **Type:** Research · **Priority:** P1 · **Blocked by:** BOARD-130, BOARD-132, BOARD-133, BOARD-137, BOARD-141 · **Owner:** architect + QA reviewer + UI critic when UI is involved

**Start with:** `.opencode/commands/run.md`, board/worktree scripts and the approved task-local evidence path.

- [ ] Take one scoped task from Ready through build, QA, independent review and Pending Merge.
- [ ] Confirm every lane has evidence and the task's docs, branch and SQLite row agree.
- [ ] Confirm no dashboard session, dispatch or run-history feature is required.
- [ ] Stop at Pending Merge; do not merge, push or invoke finalize.

#### BOARD-144 — Reconcile the factory handover inventory

**Status:** Backlog · **Type:** Docs · **Priority:** P1 · **Blocked by:** BOARD-130 · **Owner:** docs-writer

**Start with:** `docs/HANDOVER.md`, `AGENTS.md`, `docs/API_CONTRACTS.md`, `docs/STACK.md` and `docs/PROJECT_STRUCTURE.md`.

- [ ] Remove the literal merge-conflict markers in the Testing section without changing historical session records.
- [ ] Reconcile the live inventory with SQLite board state, read-only dashboard routes, current worktree commands and approved QA evidence policy.
- [ ] Keep the artifact-path policy aligned with the result of BOARD-130; do not reopen its QA loop or copy its findings into a Fix row.
- [ ] Verify cited paths and commands against source/docs and confirm no conflict markers remain.

## Deferred and explicitly out of scope

- Code-graph engine and graph dashboard: revisit only after the task/worktree, onboarding, concurrency and QA workflow is proven.
- OpenCode session API integration, dashboard dispatch and a separate run-history table.
- Distributed workers, cloud services, multi-user auth and scale targets not requested for this local factory.
- Rebuilding the existing board/worktree dashboard or replacing its approved component gallery.

## Research basis

- [unslop](https://github.com/heydamir/unslop): visual audit language and sign-by-sign review.
- [kilo_software_factory_simple](https://github.com/miahsbrain/kilo_software_factory_simple): lightweight factory workflow patterns.
- [super-board](https://github.com/EricTechPro/super-board): lane and quality-gate ideas; adapt to this local SQLite board, not its remote workflow.
- [Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills): read-on-demand specialist skill catalogue, already present in this factory.
- [billion-context](https://github.com/ranxianglei/billion-context): context compression is already integrated; upstream performance claims were not independently validated.
- [Graphify](https://github.com/Graphify-Labs/graphify): local code-graph option, deferred by the user.
- [OpenCode V2 API docs](https://opencode.ai/docs/api/): experimental session APIs were researched but are not part of the read-only dashboard scope.
