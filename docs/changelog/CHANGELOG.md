# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-11-12] Preserve native deny ordering and verify BOARD-151
**Type:** Fix
**Board:** BOARD-151 | **Branch:** fix/fix-shared-qa-artifact-guard-permissions
**Changed:** `.opencode/skills/git-worktree/scripts/guard.py`, `.opencode/plugins/factory-guard/guard.test.mjs`, script-generated `opencode.jsonc`, `.gitignore`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Approved ordering correction extends existing `generated_permission`: native restrictions now follow generic shell/edit rules, so blanket allow cannot override artifact/ledger denies. Existing regression checks preserve base shell/edit order, approval ask and configured role exceptions.
**Impact:** Approved further `node --test .opencode/plugins/factory-guard/guard.test.mjs` run passed 5/5, exit 0, 8146.249618ms. No shell/agent rules changed. Scratch fixtures remain repository-local, retained under root-anchored `/factory-guard-test-*/` and `/factory-hook-test-*/` ignores; no deletes or fixture commits. Independent QA/review remain pending; builder verification is not merge approval.

## [2026-11-12] Checkpoint native deny synchronization with ordering blocker
**Type:** Fix
**Board:** BOARD-151 | **Branch:** fix/fix-shared-qa-artifact-guard-permissions
**Changed:** `.opencode/policies/git-policy.json`, script-generated `opencode.jsonc`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Approved addition of six existing config artifact/ledger edit denies to `policy.native` avoids applying role-independent Python `file_effect` denials. Reused `guard.py check-policy --write`; no hand edits to generated config, shell or agent rules.
**Impact:** Final authorized test run exited 1: 4/5 passed, 4437.727463ms. Policy equality passes; role regression fails at `guard.test.mjs:184`: `frontend-dev: qa.md`, `'allow' !== 'deny'`. Native denies precede and are overridden by the generated blanket edit allow. Security blocker; no third run, workaround or cleanup. Recommend approval to order native denies after base edit rules while retaining role overrides. Repo-local scratch fixtures retained; independent QA/review pending, not merge-ready.

## [2026-11-12] Keep BOARD-151 fixtures in the task worktree and diagnose policy drift
**Type:** Fix
**Board:** BOARD-151 | **Branch:** fix/fix-shared-qa-artifact-guard-permissions
**Changed:** `.opencode/plugins/factory-guard/guard.test.mjs`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Correct forbidden outside-repository fixture paths, not repair external access. Reuse repo-local scratch placement from `test_handoff.py`; set Python subprocess cwd explicitly. No new tooling, dependencies or deletes.
**Impact:** No tests rerun. Read-only comparison found 142 config rules vs 136 generated: config-only edit denies for `artifacts/**`, `**/artifacts/**`, `/**/artifacts/**`, `.factory-state/reviews/*-ledger.md`, `**/.factory-state/reviews/*-ledger.md`, `/**/.factory-state/reviews/*-ledger.md` at zero-based indices 64–69; all other rules match in order. Policy/config unchanged. Recommend approval to add the six denies to canonical policy, retaining native role overrides. Verification and independent review remain outstanding.

## [2026-11-12] Checkpoint shared QA artifact guard exception
**Type:** Fix
**Board:** BOARD-151 | **Branch:** fix/fix-shared-qa-artifact-guard-permissions
**Changed:** `.opencode/skills/git-worktree/scripts/guard.py`, `.opencode/plugins/factory-guard/guard.test.mjs`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Existing `cmd_check_file` rejected canonical primary evidence writes; extend it and the existing disposable adapter fixtures rather than duplicate primary resolution or role authority. No new files or dependencies.
**Impact:** Unverified narrow location exception; native role permissions and shell policy unchanged. One documented test command exited 1, 0/5 passed: fixture `mkdtemp` failed with `EACCES` under `/tmp/opencode`, and the existing generated-policy equality assertion failed. No live data mutation or retry; blocked pending orchestrator decision and independent review.

## [2026-11-12] Record BOARD-150 QA and completed human cleanup
**Type:** Docs
**Board:** BOARD-150 | **Branch:** fix/fix-planning-cli-database-resolution
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Replace pending review/cleanup status with current evidence; earlier entries remain historical.
**Impact:** QA round 1 PASS (`artifacts/factory/qa/2026-11-12/BOARD-150/qa.md`); builder 7 tests in 2.621s, reviewer 7 in 2.626s; architect review found no blocker. Corrected live CLI queue/history retained all 20 original migrated records (13 queued, 2 active, 5 history); BOARD-150 adds one active only. Human removed the accidental primary `docs/BOARD.md` (absent at 22:31); no database, backup or evidence was deleted. Human inspection/finalize is next, then BOARD-147 dashboard work after merge. Documentation only; no further tests run.

## [2026-11-12] Resolve plan CLI commands to the canonical SQLite database
**Type:** Fix
**Board:** BOARD-150 | **Branch:** fix/fix-planning-cli-database-resolution
**Changed:** `.opencode/skills/board/scripts/board.py`, `.opencode/skills/board/scripts/test_board_normalized.py`, `docs/STACK.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, `docs/changelog/CHANGELOG.md`
**Why:** Initialization returns the legacy Markdown path; plan handlers require the existing live SQLite database. Reuse `live_database` at dispatch rather than add another resolver.
**Impact:** All plan subcommands target canonical state; lifecycle semantics and read-only fixtures remain unchanged. `python3 .opencode/skills/board/scripts/test_board_normalized.py PlannedCliDatabaseTests PlannedLifecycleTests` passed 7 tests in 2.621s. No live data changed; human cleanup of the accidental empty primary `docs/BOARD.md` remains blocked by primary-checkout protection.

## [2026-11-12] Record BOARD-146 round-four review
**Type:** Docs
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Record the independent QA pass, architect review and verification totals before human integration.
**Impact:** Documentation only. No live migration has run; migration dry-run and separately approved apply remain after human inspection/finalize.

## [2026-11-12] Reject multiline repository IDs in planned items
**Type:** Fix
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/board.py`, `.opencode/skills/board/scripts/test_board_normalized.py`, `docs/STACK.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Prevent repository IDs from splitting compatibility rows and reject malformed generated projections before persistence.
**Impact:** Focused command `python3 .opencode/skills/board/scripts/test_board_normalized.py PlannedProjectionValidationTests` passed 2 tests in 0.096s. No live data was touched.

## [2026-11-12] Keep planned-work payloads on one snapshot
**Type:** Fix
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/board_serve.py`, `.opencode/skills/board/scripts/test_board_serve.py`, `docs/ARCHITECTURE.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Prevent related normalized reads from combining different committed lifecycle states.
**Impact:** The read-only adapter now holds an explicit SQLite read transaction. The focused API class passed 7 tests in 0.529s.

## [2026-11-12] Add read-only planned-work API
**Type:** Feature
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/board.py`, `.opencode/skills/board/scripts/board_serve.py`, `.opencode/skills/board/scripts/test_board_serve.py`, `docs/API_CONTRACTS.md`, `docs/STACK.md`, `docs/ARCHITECTURE.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Serve canonical queue/history and structured active criteria through safe read-only SQLite access.
**Impact:** Focused command `python3 .opencode/skills/board/scripts/test_board_serve.py PlannedWorkApiTests` passed 5 tests in 0.302s. No live board/migration or dependency changes.

## [2026-11-12] Record BOARD-146 lifecycle fix handoff
**Type:** Docs
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Record the committed Notes correction and the next independent-review step.
**Impact:** Documentation only.

## [2026-11-12] Keep empty planned Notes canonical
**Type:** Fix
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/board.py`, `.opencode/skills/board/scripts/test_board_normalized.py`, `docs/BUSINESS-LOGIC.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Store omitted planned Notes as an empty string while rendering `-` only in the Markdown compatibility view.
**Impact:** Focused retry `python3 .opencode/skills/board/scripts/test_board_normalized.py PlannedLifecycleTests` passed (5 tests, 0.382s); it also verifies unrelated field edits preserve the canonical empty value.

## [2026-11-12] Add normalized board planning lifecycle
**Type:** Feature
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/board.py`, `.opencode/skills/board/scripts/test_board_normalized.py`, `.opencode/skills/board/SKILL.md`, `.opencode/skills/git-worktree/scripts/worktree.py`, `docs/ARCHITECTURE.md`, `docs/API_CONTRACTS.md`, `docs/BUSINESS-LOGIC.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/STACK.md`
**Why:** Add explicit JSON-batch acceptance and transactional queue/active/history lifecycle while retaining the existing active-board CLI and human-finalize gate.
**Impact:** Lifecycle behavior added; HTTP remains contract-only. Verification `python3 .opencode/skills/board/scripts/test_board_normalized.py PlannedLifecycleTests` ran 5 tests and failed at test line 294 because missing notes stored `'-'` instead of expected `''`; no retry was made.

## [2026-11-12] Align BOARD-146 docs after rebase
**Type:** Docs
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`
**Why:** Preserve BOARD-149 artifact policy and retain BOARD-146 decisions under unique ADR numbers after rebasing onto `opencode`.
**Impact:** Documentation only; no board state or application behavior changed. User-reported board suite result was not rerun.

## [2026-11-12] Record BOARD-149 final review handoff
**Type:** Docs
**Board:** BOARD-149 | **Branch:** chore/move-qa-reports-to-task-artifacts
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`
**Why:** Record that the docs-only follow-up passed architect review and user inspection is next.
**Impact:** Documentation only; task behavior and status are unchanged.

## [2026-11-12] Update BOARD-149 review handoff
**Type:** Docs
**Board:** BOARD-149 | **Branch:** chore/move-qa-reports-to-task-artifacts
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`
**Why:** Record the round-2 QA result and remaining review/human integration steps.
**Impact:** Documentation only; task behavior and status are unchanged.

## [2026-11-12] Clarify QA artifact permission boundary
**Type:** Docs
**Board:** BOARD-149 | **Branch:** chore/move-qa-reports-to-task-artifacts
**Changed:** `AGENTS.md`
**Why:** Align the factory rule with the approved native file-tool permission boundary.
**Impact:** These rules constrain file tools only; shell remains trusted-agent authority, not blocked by this map.

## [2026-11-12] Move QA reports into shared task artifacts
**Type:** Chore
**Board:** BOARD-149 | **Branch:** chore/move-qa-reports-to-task-artifacts
**Changed:** QA/UI instructions, native edit/write/patch role permissions, project templates and scopes, UI-UX guidance, handover, project state and decisions; copied BOARD-146 QA report to its approved artifact path.
**Why:** Keep reports/evidence with task artifacts while reserving `.factory-state/reviews/` for bounded-loop ledgers.
**Impact:** New report paths and role-specific file-tool permissions; shell remains trusted-agent authority. Ledger location, 10-round cap and stop conditions remain unchanged. Historical reports remain untouched.
## [2026-11-12] Preserve checklist details and cancelled history
**Type:** Fix
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/board.py`, `.opencode/skills/board/scripts/test_board_normalized.py`, board architecture/decision/business-logic/handover/stack/project-state docs.
**Why:** Extract multiple semicolon-separated Notes checkboxes independently and retain normalized items when removed through the compatibility CLI.
**Impact:** Each criterion keeps its own verification/proof; remove records cancellation without deleting canonical history. Verification was not run because the approved suite attempts are exhausted.

## [2026-11-12] Correct normalized migration fixture count
**Type:** Fix
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/test_board_normalized.py`, `docs/PROJECT_STATE.md`, `docs/HANDOVER.md`
**Why:** Match the apply-result assertion to the fixture's 22 rows after three status-mapping cases were added.
**Impact:** Test expectation only; not rerun because the prescribed verification attempts are exhausted.

## [2026-11-12] Normalize planned and active board storage
**Type:** Feature
**Board:** BOARD-146 | **Branch:** feat/separate-planned-work-from-active-board
**Changed:** `.opencode/skills/board/scripts/board.py`, normalized migration tests, board architecture/decision/stack/handover/business-logic/project-state documentation.
**Why:** Separate planned queue, active work, criteria and terminal history while retaining existing board CLI behavior.
**Impact:** Explicit `migrate-normalized` dry-run and `--apply` migration added. Applying creates a consistent backup through a separate read-only connection while holding the writer lock, verifies snapshot content/revision, then migrates transactionally. No live database was migrated; no planning lifecycle commands or endpoint added.

## [2026-11-12] Correct ledger invalid-ID test mock
**Type:** Fix
**Board:** BOARD-145 | **Branch:** chore/raise-qa-review-loop-limit-to-ten
**Changed:** `.opencode/skills/qa-review/scripts/test_ledger.py`
**Why:** Mock the runtime-state lookup and ledger file operations actually used by the ledger module.
**Impact:** Test-only; production behavior is unchanged.

## [2026-11-12] Move runtime state outside Git metadata
**Type:** Feature
**Board:** BOARD-148 | **Branch:** chore/move-clone-local-state-out-of-git-metadata
**Changed:** runtime-state resolver/migration CLI, board/worktree/QA state consumers, regression fixtures, rules, and factory docs.
**Why:** Keep clone-local mutable state outside `.git` while sharing it across linked worktrees.
**Impact:** Runtime paths use `<primary-checkout>/.factory-state/`. The verified snapshot was installed atomically after stopping legacy DB writers; SQLite integrity and source stability were checked. The original `.git/` state remains untouched; cleanup was not approved or performed. Default writers refuse unverified destinations.
**Verification:** `state.py migrate` dry-run previewed five state items; `state.py migrate --apply` reported `migration verified and installed atomically; source remains untouched`. Runtime-state suite: 13 tests passed; board suite: 35 passed; handoff suite: 34 passed (user-run after the final fixture correction).

## [2026-11-12] Raise QA review loop cap to ten
**Type:** Chore
**Board:** BOARD-145 | **Branch:** chore/raise-qa-review-loop-limit-to-ten
**Changed:** QA ledger, boundary tests, loop policy, reviewer instructions, command shortcuts, decisions, handover and project state; corrected session status and QA list indentation after rebase.
**Why:** Apply the approved ten-round future cap while retaining immediate stop conditions.
**Impact:** New ledgers permit 10 rounds and refuse 11. BOARD-130 historical state and artifacts remain unchanged.
**Verification:** Ledger suite passed 5 tests before the documentation-only correction; `git diff --check` verifies the documentation diff.

## [2026-11-12] Plan factory implementation backlog
**Type:** Docs
**Board:** BOARD-131 | **Branch:** docs/plan-factory-implementation-backlog
**Changed:** `docs/FACTORY_ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/RISKS.md`, factory docs index, project structure, API contract, decisions, handover, project state, README.
**Why:** Turn the approved factory direction into small, dependency-ordered SQLite tasks and a readable roadmap.
**Impact:** Documentation and backlog only. The dashboard remains read-only; no runtime or API behavior changed.
**Verification:** `git diff --check` passed; live board rows reviewed with `board.py show` and generated export. Docs-only review passed; no application tests run.

## [2026-11-12] Record BOARD-131 handoff state
**Type:** Docs
**Board:** BOARD-131 | **Branch:** docs/plan-factory-implementation-backlog
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log.
**Why:** Record the local plan commit and the remaining human review gate.
**Impact:** None; no runtime or backlog behavior changed.
**Verification:** `git diff --check` passed; clean-worktree handoff check pending.

## [2026-11-12] Verify registered-repository read boundary
**Type:** Docs
**Board:** BOARD-126 | **Branch:** feat/expose-registered-repos-and-safe-candidates
**Changed:** `docs/PROJECT_STATE.md`, `docs/HANDOVER.md`, this log.
**Why:** Record current-state suite and independent review after the API/security corrections.
**Impact:** None; no runtime change. The earlier failed attempts remain recorded below.
**Verification:** Board suite 32 tests OK on `ec15b3d`; independent review PASS.

## [2026-11-12] Clarify active-WAL read verification
**Type:** Test
**Board:** BOARD-126 | **Branch:** feat/expose-registered-repos-and-safe-candidates
**Changed:** `test_board_serve.py`, `docs/API_CONTRACTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log.
**Why:** SQLite may change existing `-shm` metadata on a read-only active-WAL lookup.
**Impact:** The regression still requires current row, unchanged DB/WAL bytes and sidecar set, and clean Git status; only existing transient `-shm` bytes are exempt. Missing-board no-write assertions remain. No server change. Catalogue: python-pro, secure-code-guardian.
**Verification:** Focused four-test second attempt exited 0: 4 tests in 0.088s. Earlier broad suite remains unverified; parent review pending.

## [2026-11-12] Anchor candidate discovery to no-follow directory handles
**Type:** Fix
**Board:** BOARD-126 | **Branch:** feat/expose-registered-repos-and-safe-candidates
**Changed:** `board_serve.py`, `test_board_serve.py`, `docs/API_CONTRACTS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log.
**Why:** A directory could be replaced with a symlink between listing and path-based marker inspection.
**Impact:** Directory-descriptor-based scanning skips swapped symlinks and closes descriptors on failure; candidate response remains names-only with safe 503. Added active-WAL read regression. Catalogue: python-pro, secure-code-guardian.
**Verification:** Focused four-test run exited 1: three scan tests passed, active-WAL file-byte assertion failed after current-data read. WAL semantics need a decision; earlier broad suite remains unverified.

## [2026-11-12] Prevent HTTP reads from initializing registered boards
**Type:** Fix
**Board:** BOARD-126 | **Branch:** feat/expose-registered-repos-and-safe-candidates
**Changed:** `board_serve.py`, `test_board_serve.py`, `docs/API_CONTRACTS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log.
**Why:** The existing board reader can create SQLite when a registered independent repo lacks its board.
**Impact:** Read-only secondary SQLite lookup; a missing board remains visible with `Board not initialized`. Only the board CLI can initialize it. No migration or new dependency. Catalogue: python-pro, api-designer, secure-code-guardian.
**Verification:** Focused scratch check first failed on read-only SQLite WAL sidecars; corrected and second run passed 2 tests in 0.087s. Prior broad suite remains unverified; parent review pending.

## [2026-11-12] Expose registered repositories and safe candidate names
**Type:** Feature
**Board:** BOARD-126 | **Branch:** feat/expose-registered-repos-and-safe-candidates
**Changed:** `board_serve.py`, `test_board_serve.py`, root/template `AGENTS.md`, `docs/API_CONTRACTS.md`, `docs/PROJECT_STRUCTURE.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log.
**Why:** The dashboard previously showed only a control/project pair and could not safely show prospective repo names.
**Impact:** Registered repos appear in existing read-only APIs; a separate metadata-only candidate API scans `/projects` up to two levels. No registration or candidate content access; no migration or new dependency. Catalogue: python-pro, api-designer, secure-code-guardian.
**Verification:** Documented suite failed twice on old unregistered-project fixture expectations; corrected without a third run under the two-attempt cap. Parent independent verification/review pending.

## [2026-11-12] Hold approval lock and publish finalize recovery atomically
**Type:** Fix
**Board:** BOARD-125 | **Branch:** fix/repair-finalize-after-worktree-removal
**Changed:** `worktree.py`, `test_handoff.py`, git-worktree skill, `docs/STACK.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, this log.
**Why:** An incomplete direct journal write blocked retry; board approval could change between confirmation and merge.
**Impact:** No-overwrite synced journal and a SQLite writer lock from approval recheck through integration and board update; other writers may wait/time out. Failure retains recovery for replay; no live integration by agents.
**Verification:** Focused scratch-repository handoff suite, then independent parent review.

## [2026-11-12] Repair finalize after self-removal
**Type:** Fix
**Board:** BOARD-125 | **Branch:** fix/repair-finalize-after-worktree-removal
**Changed:** `worktree.py`, `test_handoff.py`, git-worktree skill, `docs/STACK.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, this log.
**Why:** SQLite row update imported a script that finalize had just deleted with its worktree.
**Impact:** Loaded board adapter keeps live control discovery; validated, durable recovery supports replay without re-merging; human prompt shows target and requires exact `yes` on real TTY. No bypass or live integration by agents.
**Verification:** Focused scratch-repo handoff tests; parent independent review required. Catalogue: python-pro, cli-developer, debugging-wizard, secure-code-guardian.

## [2026-11-12] Correct interactive finalize confirmation
**Type:** Fix
**Board:** BOARD-124 | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `worktree.py` confirmation, `test_handoff.py`, git-worktree skill, HANDOVER and this log.
**Why:** The human's stdin was a TTY, but opening `/dev/tty` raised `io.UnsupportedOperation` and refused finalize.
**Impact:** Prompt via TTY stderr and read one line from TTY stdin; fail closed on non-TTY, EOF, mismatch or stream errors. Exact four-value challenge and post-confirmation base recheck stay intact. No bypass flag or agent-run integration. Catalogue: python-pro, cli-developer.
**Verification:** `python3 -m unittest discover -s .opencode/skills/git-worktree/scripts -p 'test_handoff.py'` passed: 24 tests in 12.083s. Parent independent review pending.

## [2026-11-12] Correct bootstrap finalize instructions
**Type:** Docs
**Board:** BOARD-124 | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `.opencode/skills/git-worktree/SKILL.md`, `docs/HANDOVER.md` and this log.
**Why:** The ready handoff prints an absolute bootstrap-script finalize command; older instructions incorrectly required manual merge and cleanup.
**Impact:** Preserve pre-merge import and byte-exact backup, then direct the human to review and run the printed command from the clean base checkout in a real TTY. No runtime change.
**Verification:** File review and `git diff --check` only. Catalogue: code-documenter.

## [2026-11-12] Clarify app work-surface finalize path
**Type:** Docs
**Board:** BOARD-124 | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `.opencode/skills/git-worktree/SKILL.md`, `AGENTS.md`, `templates/project/AGENTS.md` and this log.
**Why:** Relative control-script examples fail when copied into an app work surface without the harness.
**Impact:** App handoff guidance uses the printed absolute control-script path and `--repo <id>`; relative examples remain valid for the control checkout only. No runtime change.
**Verification:** File review and `git diff --check` only. Catalogue: code-documenter.

## [2026-11-12] Guard bootstrap import and local review paths
**Type:** Fix
**Board:** BOARD-124 | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `board.py`, `worktree.py`, `ledger.py`, adjacent regression tests, git-worktree skill, HANDOVER, STACK and this log.
**Why:** An uninitialized database could lose tracked legacy rows on merge; app handoff pointed to a nonexistent relative script; ledger IDs allowed path traversal.
**Impact:** Human pre-merge check creates/verifies local import and byte-exact backup before legacy deletion; handoff uses absolute control script; invalid ledger IDs refuse before I/O. Fresh clones remain empty. Reuses board importer/export writer and handoff command; new adjacent ledger tests cover input safety. Catalogue: python-pro, cli-developer, secure-code-guardian/input-validation.
**Verification:** Board suite 24 OK (rerun after export-path refinement); handoff suite 24 OK; ledger suite 2 OK. `git diff --check` passed. Temporary repositories/directories only; parent independent review required.

## [2026-11-12] Align bootstrap lifecycle and review guidance
**Type:** Docs
**Board:** BOARD-124 | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `AGENTS.md`, `templates/project/AGENTS.md`, `.opencode/skills/git-worktree/SKILL.md`, `.opencode/commands/ui.md`.
**Why:** Remove stale second-worktree, automatic Fix-row, raw teardown, main-target and review-artifact commit instructions; identify the one-time human-managed bootstrap integration while the base checkout still has old tooling.
**Impact:** Guidance only; no tooling behavior change. Normal tasks use human-only finalize; this bootstrap requires human manual merge and cleanup after approval.
**Verification:** File review and `git diff --check` only.

## [2026-11-12] Complete local-board and human-gate migration
**Type:** Fix
**Board:** BOARD-124 | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `worktree.py`, `test_handoff.py`, `ledger.py`, root/template rules, agent/skill/command guidance, `docs/BOARD.md` index, structure/stack/decisions/handover.
**Why:** Prevent unattended integration and conflicted main checkout; remove tracked historical board state and automatic Fix-worktree fanout.
**Impact:** Local SQLite board and reviewer records stay outside Git; Markdown is generated export. Human typed-TTY gate is policy deterrence, not same-identity security. Existing board bytes and import snapshot preserved; fresh clone starts empty. In-task findings reuse the task worktree.
**Verification:** Lifecycle suite in isolated temporary repositories; independent parent review still required.

## [2026-11-12] Gate env provisioning and add human-only finalization
**Type:** Feature
**Board:** BOARD-124 | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `worktree.py`, `env.py`, lifecycle tests, HANDOVER and this log.
**Why:** Reuse existing board/Git/env lifecycle adapters; fail closed on unsafe env sources and destinations and replace raw merge guidance with a single human operation. New `cmd_finalize` is needed for ordered preflight, merge, recovery and teardown.
**Impact:** Partial failed creations remain owned and Blocked. Finalize preflights conflicts and records branch tip before integration; never runs automatically. Pending Merge certifies review evidence that cannot be independently parsed by the CLI. Skills: python-pro, cli-developer, secure-code-guardian.
**Verification:** Two allowed suite runs: first 19 tests/2 stale-fixture failures; second 19 tests OK (9.198s) after fixing scratch SQLite mutation. Subsequent small guidance/legacy-cleanup tightening is unverified and needs independent review before the row advances.

## [2026-11-12] Move the live board core to SQLite
**Type:** Feature
**Board:** bootstrap slice | **Branch:** feat/sqlite-board-bootstrap
**Changed:** `board.py`, `board_serve.py`, focused board tests, `.gitignore`, STACK, PROJECT_STRUCTURE, HANDOVER, PROJECT_STATE and this log.
**Why:** Keep board state local to a clone and shared across its worktrees without dirtying tracked Markdown. Reused the existing board parser, command handlers, `read_table`/`write_atomic` lifecycle adapter and read-only viewer; added only SQLite storage, three-way cell merge and export. No new module or external dependency. Catalogue: python-pro (standard library), sql-pro (database design), cli-developer (argparse).
**Impact:** First default read imports the old main-board bytes once, without deleting or modifying them. SQLite holds authoritative state thereafter; `board.py export` generates a Markdown file in the Git common directory. Concurrent disjoint changes merge; overlapping changes refuse. Existing tracked board remains until a separate safe untracking slice; no project repo or integration checkout edits. Reversible with preserved import bytes and export.

## [2026-11-11] Record independent handoff-gate review PASS
**Type:** Docs
**Board:** BOARD-123 | **Branch:** fix/gate-merge-handoffs-on-finished-clean-worktrees
**Changed:** HANDOVER, PROJECT_STATE and this log only.
**Why:** Independent QA/review report and ledger committed in `27c2e94` record PASS; parent reports the factory row is Pending Merge, awaiting human merge.
**Impact:** Status now reflects passed review and pending human action. Parent retains final live handoff check; no merge guidance emitted here. Historical unrelated HANDOVER conflict markers preserved; no source/rules/tests or board changes.
**Verification:** File review only for this docs update; no tests rerun. Existing authorized focused result remains exit 0, 13 tests in 3.847s. Independent acceptance-criteria evidence and coverage limits: `docs/reviews/BOARD-123-qa.md:3–30`.

## [2026-11-11] Verify corrected handoff status gate
**Type:** Fix
**Board:** BOARD-123 | **Branch:** fix/gate-merge-handoffs-on-finished-clean-worktrees
**Changed:** HANDOVER, PROJECT_STATE and this log record authorized second-run evidence; no further implementation changes.
**Why:** Architect reviewed the existing `STATUS_INDEX` correction and authorized one focused rerun, exact force-add of ignored new `test_handoff.py`, and narrow tracked-file staging after the earlier ignored-path staging error (exit 1). No broad force-add or repeat of that staging command.
**Impact:** Handoff gates verified against isolated scratch repositories; parent review and live Pending Merge remain required before merge guidance. No real board/project changes, installs, UI/browser/build work or unrelated historical conflict-marker cleanup.
**Verification:** `python3 -m unittest discover -s .opencode/skills/git-worktree/scripts -p 'test_handoff.py'` exited 0: 13 tests in 3.847s, OK. Covers staged/unstaged/untracked dirt, nonready/missing status, missing branch/base/worktree/row, no commits ahead, Git failures/empty count, clean Pending Merge ordering, read-only behavior and already-merged nonmerge guidance. Full lifecycle suite not run. Prior failed-run record below remains historical.

## [2026-11-11] Gate merge handoffs on finished clean worktrees
**Type:** Fix
**Board:** BOARD-123 | **Branch:** fix/gate-merge-handoffs-on-finished-clean-worktrees
**Changed:** Existing worktree `cmd_handoff`, lifecycle `handoff()` test; root/template AGENTS §B5/§B11, git-worktree skill, handover/closeout/run/board commands, STACK, DECISIONS (ADR-082), HANDOVER, PROJECT_STATE and this log. New adjacent `test_handoff.py` isolates handoff regressions from the unrelated full env/teardown suite while reusing its scratch fixture builder.
**Why:** Premature handoffs offered merge and teardown for unfinished work. Reuse board/live-row/repo/base/Git helpers and STATUS_INDEX; add checked status, branch identity, commit count and ancestry inside existing effectful command, no parallel readiness framework. Skills applied: python-pro (standard library/testing), cli-developer (Python CLI/UX), test-master (unit testing), code-documenter (user guides), git-worktree procedure. Python 3.9+/stdlib/unittest conventions prevail.
**Impact:** Only finished verified/reviewed committed clean Pending Merge work may receive merge guidance; manual commands obey the same gate. Dirty/nonready/missing/Git-error output refuses (exit 1), retains review commands, omits merge/teardown. Clean already-merged path preserves review/cleanup with no merge (exit 0). Factory/future template only; separate existing project deferred. Reversible local harness change; no history rewrite, board/security edits, install, build, UI/server work, merge, push or cleanup.
**Verification:** Single `python3 -m unittest discover -s .opencode/skills/git-worktree/scripts -p 'test_handoff.py'` exited 1: 13 tests in 3.993s, nine failures. All failures identify status as missing: `field_index` handles editable fields, not Status. Corrected to existing `STATUS_INDEX` after file review; no rerun under one-command budget. Parent must reverify and review; checkpoint is not merge-ready. Initial multi-file policy patch had a template-context mismatch and applied nothing; corrected patch added template B5 step 8 where absent. Existing unrelated HANDOVER conflict-marker history preserved, not resolved by this task.

## [2026-11-11] Verify local-board migration and untrack runtime state
**Type:** Feature
**Board:** BOARD-122 | **Branch:** feat/keep-live-board-local-and-untracked
**Changed:** Existing `test_board_serve.py`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log; remove only the task index entry for `docs/BOARD.md`, retaining its disk bytes. Template starter unchanged and tracked. No new files or production-code changes in this resumption.
**Why:** Architect approved correcting two fixtures rather than changing valid production behavior: assert the established missing-board error entry while retaining no-recreation assertions; recreate the scratch docs directory before restoring the backup after Git deletion. Reuse existing tests and fixtures; no abstraction/dependency. Previously selected python-pro, cli-developer, test-master, code-documenter references and git-worktree procedure remain applicable.
**Impact:** Runtime factory board is ignored and absent from the task index. Guard check-git returned 3, needs approval; the user's existing exact-command authorization covered `git rm --cached -- docs/BOARD.md`, run only in the task worktree. Before/after task-file SHA-256 matches: `c2c5da6f78fc5e8ba6c2ad4cb16f150235dee4ee03937cd0d8bb2fdc22cee91e`. Cached name/status is `D docs/BOARD.md`; ls-files lists only the template starter and check-ignore lists the runtime board. No main-board/backup access, project edits, history rewrite, merge, push, UI/server changes or installs. Parent review still required; human refresh-backup/merge/restore sequence retained in HANDOVER.
**Verification:** Second and final authorized attempt: `python3 -m unittest discover -s .opencode/skills/board/scripts -p 'test_board*.py'` exited 0, 24 tests in 0.222s, OK. Covers main/linked/nested ownership with missing boards, CLI/viewer startup, existing/malformed byte preservation, concurrent exclusive complete publication, symlink refusal, read-only requests, ignores and scratch Git backup/merge/restore. Real data never used as test fixtures; real main board and backup untouched. No merge readiness claim before parent review.

## [2026-11-11] Checkpoint local-board bootstrap and migration rules
**Type:** Feature
**Board:** BOARD-122 | **Branch:** feat/keep-live-board-local-and-untracked
**Changed:** Both `.gitignore` files, board CLI/viewer and existing adjacent tests, worktree control-root lookup; root/template AGENTS, board/worktree skills, architect agent, board commands, structure/template handover, STACK, DECISIONS (ADR-081), HANDOVER, PROJECT_STATE and this log. No new files; no BOARD.md content or index change.
**Why:** Keep live board state local, separate from task commits. Reuse COLUMNS/parser and the existing Git main-checkout resolver; add only shared missing-board bootstrap because ordinary parser reads and viewer requests must not write. Catalogue python-pro (standard library), cli-developer (Python CLI), test-master (unit testing), code-documenter (user guides), and git-worktree procedure applied; existing Python 3.9+/unittest conventions prevail.
**Impact:** Startup exclusively publishes a complete missing default board, preserves existing/malformed bytes, refuses symlink paths, and never initializes explicit paths or another project's board. Exact user-approved permanent wording applied after one authorized narrower retry excluded every BOARD.md target. Template starter bytes unchanged. Runtime board remains tracked until verification passes and guarded index-only removal is completed. No history rewrite, main-board/backup access, project changes, dependency/UI/server changes. High-risk local-data migration remains held; backup and restore required before tools restart after eventual merge.
**Verification:** Single `python3 -m unittest discover -s .opencode/skills/board/scripts -p 'test_board*.py'` exited 1: 24 tests in 0.235s, one failure/one error. Request-read-only fixture expects an empty list rather than existing missing-board error payload; scratch merge removes empty docs directory, so restore needs mkdir first. No correction/rerun under the one-command budget, no real untracking, not merge-ready. Initial follow-up docs patch had a context typo and applied nothing; corrected patch records this hold.

## [2026-11-11] Checkpoint main preview and screenshot hold
**Type:** Docs
**Board:** BOARD-121 | **Branch:** feat/apply-approved-workbench-to-main-dashboard
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/STACK.md`, this log; new `docs/reviews/BOARD-121-qa.md` stores this task's attributed parent observations and hold, not an independent verdict.
**Why:** Parent inspected `fd89d5b` and started main preview 15183; preserve observed initial scope/DOM state and exact screenshot blocker for resumption.
**Impact:** Parent observed Project default 14 tasks/result 14 of 14/three project worktrees; hidden Harness 21 tasks/eight control worktrees, proper isolation. At 1000×700 CSS no horizontal overflow, 60s refresh, 17px/600 heading and no fixture notice. Built-in screenshot after tabs.focus returned browser.operation_failed: “Screenshot needs a visible tab. Call browser.tabs.focus and keep its desktop window visible.” No retry/fallback or screenshot; independent visual/unslop, keyboard/full responsive QA remain held. Visible desktop window needed; not merge-ready. Live 15180 unchanged. Reversible docs-only checkpoint; no source, board, rules or artifacts workaround.
**Verification:** Verification limited to file review because this was a low-risk visual/static change. No browser calls, tests or builds in this checkpoint. Prior implementation proof retained: documented Python regression command exited 0, 15 tests in 0.048s.

## [2026-11-11] Apply approved workbench to the main dashboard
**Type:** Feature
**Board:** BOARD-121 | **Branch:** feat/apply-approved-workbench-to-main-dashboard
**Changed:** `board_serve.py`, adjacent `test_board_serve.py`; `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/UI-UX.md`, `docs/DECISIONS.md`, `docs/PROJECT_STRUCTURE.md`, this log. No new files.
**Why:** User approved the latest hierarchy gallery and requested main dashboard implementation. Reuse `wb_scope_tabs`, `wb_scope_content`, `wb_toolbar`, lane/card/meter/rail and existing JS; extract only `wb_workbench_header` because main and gallery now share that composition. Extend existing scope presenter for path-based explicit-board association instead of a second repository model. Correct stale control-only repository-map documentation.
**Impact:** Real repository-scoped main tabs/counts/tasks/worktrees, Project default with remembered fallback, approved typography/card boundaries and integrated rail. Preserve actual refresh timestamp, live/stale/Pause/manual/60s behavior, URL filters, criteria, storage and keyboard selection. JSON/endpoints and offline read-only standard-library runtime unchanged; fixtures remain gallery-only. Reversible presentation change; blast radius is dashboard users. No CSS, asset, dependency, server, board, rule or project changes.
**Verification:** `python3 .opencode/skills/board/scripts/test_board_serve.py` exited 0, 15 tests in 0.048s; temporary fixtures/mocked Git, no live server. Cases cover scoping, duplicate IDs, explicit paths, escaping, empty/error fallback, fixture exclusion, shared classes and refresh contracts. No browser execution or build. Parent fresh 15183 built-in-browser-only QA/critique/unslop pending; live 15180 untouched, not merge-ready. Skills: catalogue python-pro (standard-library), javascript-pro (browser APIs), test-master (unit testing), native unslop/signs and built-in browser guidance; surrounding Python 3.9/unittest/JS conventions retained over catalogue defaults.

## [2026-11-11] Strengthen gallery section and card hierarchy
**Type:** Fix
**Board:** BOARD-118 | **Branch:** feat/redesign-board-console-component-gallery
**Changed:** `.opencode/skills/board/ui/src/app.css`, generated `static/board.css`; `docs/UI-UX.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log. No new files.
**Why:** User found section headings and individual task boundaries hard to distinguish. Extend existing workbench-scoped selectors instead of forking presenters or duplicating layout/state.
**Impact:** 17px/600 section headings, quiet 13px/500 lane labels, 15px/600 task titles above 12px metadata; 1px theme-relative card edges, 8px corners, 12px gaps and 24px group separation. Comparable worktree surfaces; no shadows, gradients or heavy outer panels. CSS-only, reversible; live `/`, Python/JS behavior, rules, dependencies, servers and board unchanged.
**Verification:** Required stylesheet authoring exited 0 (Tailwind 4.3.5, 59ms). Verification limited to file review because this was a low-risk visual/static change. No tests or browser calls; prior screenshots/critique are historical, not proof for changed CSS. Parent built-in light/dark inspection and user approval pending; not merge-ready. Catalogue index reviewed: no relevant CSS-only specialist; native unslop spacing/type/layout passes applied.

## [2026-11-11] Checkpoint corrected gallery preview and independent critique
**Type:** Docs
**Board:** BOARD-118 | **Branch:** feat/redesign-board-console-component-gallery
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/UI-UX.md`, this log; checkpoint existing new `docs/reviews/BOARD-118-ui.md` and `BOARD-118-ledger.md`. Extend critic report with attributed parent preview steps instead of creating a duplicate preview report. New review/ledger files preserve independent round-1 evidence/state.
**Why:** Replace stale preview-refresh instructions with observed corrected c77a72a preview and bounded review coverage.
**Impact:** Parent light/system-dark 1104×877 CSS captures, 20px heading/no desktop overflow, scoped tabs, actual tab/reload/theme behavior and current-document diagnostics recorded. Independent screenshot critique/unslop HOLD, no blocking visible findings; narrow matrix/keyboard/focus/contrast and remaining behavior/user approval open. Built-in catalogue lacks resize. Canonical artifacts notes.md patch guard-refused, no retry/bypass. Policy BOARD-120 commit 800cb3b remains separate Pending Merge. Live 15180 unchanged; not merge-ready.
**Verification:** Verification limited to file review because this was a low-risk visual/static change. No source edits, browser calls, tests or builds in this checkpoint; previous test/build results retained as historical evidence.

## [2026-11-11] Rework gallery into a compact repository workbench
**Type:** Fix
**Board:** BOARD-118 | **Branch:** feat/redesign-board-console-component-gallery
**Changed:** `board_serve.py`, adjacent `test_board_serve.py`, `ui/src/app.css`, generated `static/board.css`; `docs/UI-UX.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log. No new files.
**Why:** User rejected old chunky components with tabs. Extend existing board presenter with optional populated-only lanes; reuse wb_ task, meter, toolbar and rail renderers and existing JS state/handlers. Scope new appearance to workbench, preserve live defaults.
**Impact:** Tight 20px header, content-width lane navigation, continuous task surface with title above quiet metadata, borderless status markers and adjacent repository rail at ordinary desktop width; empty examples below populated tasks. Gallery-only, reversible; no live rollout, rule, dependency, board or server changes.
**Evidence:** CSS authoring command exited 0 (Tailwind 4.3.5, 59ms). `python3 .opencode/skills/board/scripts/test_board_serve.py` exited 0: 12 tests in 0.031s. Source nine-pass craft record in UI-UX §6.3. Built-in tabs.list returned browser.disconnected, no exit code; no retry/fallback. Rendered QA/unslop and user gallery approval pending. Parent must refresh preview Python process for new markup; not merge-ready.

## [2026-11-11] Checkpoint parent gallery preview and browser error
**Type:** Docs
**Board:** BOARD-118 | **Branch:** feat/redesign-board-console-component-gallery
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/UI-UX.md`, this log.
**Why:** Preserve parent preview observations and stop reason without claiming completed QA or approval.
**Impact:** Parent reviewed diff and started http://127.0.0.1:15182/gallery from BOARD-118; live 15180 and prior 15181 unchanged. Built-in tab `5007dd99-7e7a-47c0-b5d6-3c060c359dd7`, snapshot generation 2 showed Project default, Project 2 / Harness 1 tabs, Project 2 in flight / 1 blocked / 2 tasks / 1 worktree, labelled fixture empty/error states. Harness click ref `e46` failed `[browser.operation_failed] browser.click failed. UnknownVizError` (no exit code); following tabs.list confirmed same gallery generation 2; no retry. Parent observations only, not independent QA. Blocked on browser error and gallery approval; user reviews directly. Interactions/themes/responsive/canonical evidence and independent unslop remain incomplete. Not merge-ready; no live screen rollout.
**Verification:** Docs-only checkpoint, no further checks/source edits/installs. Existing 11-test pass and user-supplied install/build evidence preserved unchanged. Verification limited to file review because this was a low-risk visual/static change.

## [2026-11-11] Complete repository workbench gallery for preview
**Type:** Feature
**Board:** BOARD-118 | **Branch:** feat/redesign-board-console-component-gallery
**Changed:** `.opencode/skills/board/scripts/board_serve.py`, adjacent `test_board_serve.py`, `ui/src/app.css`, generated `static/board.css`; `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/UI-UX.md`, this log. No new files.
**Why:** Resume after user-provisioned locked UI dependencies. Reuse shared wb_ presenters and dashboard handlers; remove unused count constants, align fixture Notes with review tasks, protect gallery keyboard focus from idle refresh, and allow compact rows to wrap safely at the mobile floor. Existing tests extended instead of adding a test tool or dependency.
**Impact:** Gallery-only tab/content composition and scoped styling now have generated assets. User-generated CSS was inspected/preserved before regeneration; live `/` markup/layout remains unchanged. No installs by this builder, no package/lockfile changes, server/port changes, real project or board edits. Reversible; ready for browser preview, not gallery-approved or merge-ready.
**User-supplied evidence:** `npm ci` added 56 packages, audited 63 in 18s, zero vulnerabilities; `npm run build` Tailwind 4.3.5 completed in 61ms. Not represented as builder-run commands.
**Builder evidence:** `npm --prefix .opencode/skills/board/ui run build` exited 0, Tailwind 4.3.5, 62ms (required CSS authoring, not an application production build). One verification command: `python3 .opencode/skills/board/scripts/test_board_serve.py` exited 0, 11 tests passed in 0.033s. Five new tests at lines 212–317 cover rendering/default fallback/isolation/semantics/escaping/handler contracts and gallery CSS; six inherited refresh/data tests stay green. Browser keyboard/storage/timer execution, responsive/contrast/theme inspection, canonical captures, independent review and unslop remain open; no browser attempt or installation.

## [2026-11-11] Record approved gallery dependency install timeout
**Type:** Docs
**Board:** BOARD-118 | **Branch:** feat/redesign-board-console-component-gallery
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/UI-UX.md`, this log.
**Why:** User explicitly approved installing existing locked UI dependencies to unblock gallery asset authoring; record the environmental stop without implying completion.
**Impact:** `npm --prefix .opencode/skills/board/ui ci` produced no output and exceeded 120000ms shell timeout; no exit code returned, completion unknown. Stopped without retry/workaround, build, tests, browser work or source changes. Gallery remains incomplete, not preview-ready or merge-ready. Parent requests a decision on a longer install attempt. No new dependencies or lockfile changes requested.
**Verification:** No verification command run; installation timed out before source review/verification resumed. No browser/canonical/unslop pass claimed.

## [2026-11-11] Checkpoint repository workbench gallery source
**Type:** Feature
**Board:** BOARD-118 | **Branch:** feat/redesign-board-console-component-gallery
**Changed:** `board_serve.py`, `ui/src/app.css` under `.opencode/skills/board/`; `docs/UI-UX.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, ADR-078 and this log. No new files.
**Why:** Preview approved Project/Harness tabs before screen rollout. Reuse existing wb_ cards/lanes/panels/meter/rail, row adapter, count helpers and dashboard JS rather than duplicate gallery handlers. New pure scope presenters provide missing tablist/default/content composition; fixture adapter reuses existing fixtures, deliberately sharing task IDs across scopes. Optional base rendering preserves default worktree row output.
**Impact:** Partial gallery-only source; live board markup unchanged, new layout styles scoped. Shared JS adds remembered scope, tab keyboard handling and selected-scope result totals while retaining no-tab behavior. No API changes, installs, server changes, board edits or project reads. Reversible. NOT merge-ready: generated stylesheet remains unchanged.
**Verification:** Asset authoring `npm --prefix .opencode/skills/board/ui run build` exited 127, `sh: 1: tailwindcss: not found`. Stopped per delegated instructions; regression extension/run and browser/canonical/unslop review incomplete. Parent must obtain approval to provision pinned existing dependencies before resuming.

## [2026-11-11] Include registered project worktrees in console data
**Type:** Fix
**Board:** BOARD-119 | **Branch:** fix/include-project-repository-worktrees-in-console
**Changed:** `.opencode/skills/board/scripts/board_serve.py`, adjacent `test_board_serve.py`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md` (ADR-077), this log. No new files.
**Why:** Existing `worktree_state()` listed only the control repository. Extend it with existing `load_repos`, `resolve_repo`, `is_git_repo`, `list_worktrees`, `default_base` and `git_out`, without duplicating map/Git parsing. New test fixture method supplies repository-scoped mocked Git output so existing helpers can be exercised without live repositories.
**Impact:** Every worktree request reloads control/project registry entries, omits absent/uninitialized project, and adds stable `repo` plus `base` metadata without removing existing fields or changing the JSON array. Main markers, dirty state and counts stay repository-specific, including identical branch names. Existing malformed-map exception handling remains. Read-only/offline standard-library runtime; no real board/project edits, UI changes, installs, restarts or builds. Reversible data-only change; approved tabs/default/selection await gallery and later implementation.
**Verification:** `python3 .opencode/skills/board/scripts/test_board_serve.py` → exit 0, six tests passed. Temporary fixtures/mocked Git/server prove registry refresh, registered nonconventional path, main/base/count isolation, dirty state, missing/uninitialized project, fallback values, additive endpoint compatibility and invalid maps. No browser QA; BOARD-117's existing QA blockers remain.

## [2026-11-11] Checkpoint partial parent browser observations
**Type:** Docs
**Board:** BOARD-117 | **Branch:** fix/refresh-project-board-discovery-every-minute
**Changed:** `docs/reviews/BOARD-117-qa.md` (preserved disconnected reviewer addendum; separate parent addendum), `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log.
**Why:** Record user-approved parent interactive evidence without representing it as an independent reviewer pass or complete QA.
**Impact:** Parent saw harness/project panels 18/14 (32 total), configured 60s, Pause state and actual manual reload while paused (changed timeOrigin); Pause resets after reload. Search input/URL observed, filtering not proven with unreliable `.card` selector; `/` left BODY active, shortcut not proven. Later Refresh now click returned `[browser.operation_failed] browser.click failed. UnknownVizError` (no exit code); tabs.list stayed at generation 4, loading false, same URL. No retry; filter retention, elapsed scheduling, keyboard, themes, responsiveness and visual/unslop/gallery gates remain unchecked. No product defect proven. Canonical capture still lacks Playwright; no installs. Main15180 unchanged, preview15181 only; BOARD-118 queued, not implemented. User decides whether to retry after desktop error resolution. Wip, not merge-ready.
**Verification:** Documentation only, no browser/test/build/source changes. Verification limited to file review because this was a low-risk visual/static change. Previous independent regression remains four tests, exit 0.

## [2026-11-11] Checkpoint blocked BOARD-117 QA
**Type:** Docs
**Board:** BOARD-117 | **Branch:** fix/refresh-project-board-discovery-every-minute
**Changed:** Reviewer report `docs/reviews/BOARD-117-qa.md`, current session notes in `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, this log. No source or permanent-rule edits.
**Why:** Preserve independent QA evidence and the environment blocker in a clearly labelled wip local checkpoint, not a merge-ready handoff.
**Impact:** Parent code review found no blocker; independent regression rerun passed four tests (exit 0). Browser interactions, 60-second elapsed scheduling, visual/unslop and gallery review remain unverified. Main server 15180 unchanged; preview 15181 launched from the worktree. No restarts or dependency installation. User must approve provisioning Playwright or provide its installed location before QA resumes. BOARD-118 approved redesign gallery remains queued behind BOARD-117, not implemented.
**Capture:** `node .opencode/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:15181 --route / --scope factory --task-id BOARD-117 --project . --scheme both --date 2026-11-11` → exit 2: Playwright not found in the project or global npm install (exact error: reviewer report lines 33–35). No canonical evidence produced; no application defect demonstrated.
**Verification:** Existing reviewer evidence recorded only; no additional test/build/capture commands. Verification limited to file review because this was a low-risk visual/static change.

## [2026-11-11] Refresh board discovery on every request
**Type:** Fix
**Board:** BOARD-117 | **Branch:** fix/refresh-project-board-discovery-every-minute
**Changed:** `.opencode/skills/board/scripts/board_serve.py`, new adjacent `test_board_serve.py`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/STACK.md`, `docs/DECISIONS.md` (ADR-076), this log.
**Why:** `main()` captured discovered paths once, hiding projects created after server initialization. Existing `discover_boards`, payload callbacks, parser and renderer are reused; HTML now uses the same board-payload path as JSON. New test file is needed because board/scripts had no regression tests; standard-library unittest adds no dependency or custom tooling.
**Impact:** Rediscover filesystem boards per request, including ignored project paths; keep tasks separated and explicit `--file` fixed. Set default/JavaScript fallback to 60 seconds. Existing controls, filters/state, payload shapes and read-only/offline runtime remain; no redesign, live project edits or server restart. Reversible code-only behavior change; parent review and browser QA/critique remain open.
**Verification:** `python3 .opencode/skills/board/scripts/test_board_serve.py` → exit 0, four tests passed. Temporary fixtures and mocked request handling prove HTML/JSON appearance/removal, isolation, fixed file/fresh reads and refresh defaults/override. Manual controls checked in source only; no browser interaction/timer evidence. Initial patch refusal occurred with factory-root session context; authorized worktree-relative retry succeeded after session move, without guard changes.
## [2026-11-11] Require catalogue skills and built-in browser UI reviews
**Type:** Docs
**Board:** BOARD-120 | **Branch:** docs/require-catalog-skills-and-browser-ui-reviews
**Changed:** root/template `AGENTS.md` §A7/§B4.2 and related references; all seven agent definitions; catalogue index; QA, unslop and board workflow skills; `/ui`, `/run`, `/unslop`, `/components`, `/board-view`; root/template UI-UX and STACK docs; README, HANDOVER, PROJECT_STATE, DECISIONS (ADR-079), this log. Extended existing documents; no new file or tool.
**Why:** Approved exact blocks require catalogue selection/application/reporting for every task and built-in-browser-only UI verification/review, replacing mandatory scripted capture rather than supplementing it.
**Impact:** Canonical artifact paths and gallery, independent review, accessibility, unslop, bounded ledger/fingerprint and finding-validation gates remain. Missing browser access/measurements hold criteria without fallback; transfer guidance distinguishes desktop file IDs from server-local screenshot/files.get paths. Read-only scope files' old capture directions are explicitly superseded by canonical §B4.2. Historical ADRs/logs/evidence and test/capture source remain unchanged; no guard/security policy, dependency, board, project-copy, merge or push changes.
**Verification:** File review completed. First inline `python3` consistency command exited 1 (`AssertionError: .opencode/skills/board/SKILL.md`): its overbroad `script is the only` pattern matched the unrelated board-editing rule. Architect authorized one corrected browser-specific check; it exited 0 with six root/template exact-block checks, seven agent checks, 23 active documents free of old positive UI capture directives, preserved nonbrowser script ownership and bounded finding gates, 27 Markdown-only files and clean whitespace. Board-editing rule unchanged. No build, runtime, browser or model-behavior tests. Applied catalogue `code-documenter` (user-guides reference), `prompt-engineer` (system-prompts reference), and native OpenCode/browser guidance; reused existing documents. Initial shell `rg` search exited 127 (executable unavailable); architect authorized the existing dedicated grep tool, with no installation or retry. Local documentation commits await architect review and the human merge gate.


## [2026-11-11] Use OpenCode browser for interactive UI reviews
**Type:** Docs
**Board:** BOARD-116 | **Branch:** docs/use-opencode-browser-for-interactive-ui-reviews
**Changed:** root/template `AGENTS.md` §B4.2; `.opencode/agents/qa-reviewer.md`, `ui-critic.md`; `.opencode/skills/qa-review/SKILL.md`; `.opencode/commands/ui.md`; root/template `docs/UI-UX.md`; `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md` (ADR-075), this log. Extended existing instructions; no new tools or files.
**Why:** Approved policy uses the built-in browser for interactive checks while keeping canonical QA capture script-only.
**Impact:** QA and unslop gates remain; built-in screenshots are inspection-only. Guidance covers skill loading, Code Mode signature discovery, explicit tab IDs, fresh refs, untrusted page/log content and desktop attachment. Unavailable browser is reported without retries on disconnection or silent MCP fallback; configured MCP retained. Parent reviewed all 12 file diffs: PASS; reviewed docs change prepared for human review/local commit through the authorized existing Kilo bootstrap guard. BOARD-114 remains blocked and runtime unverified; no migration, source/config, plugin or permission changes or approval to merge the migration.
**Verification:** Verification limited to file review because this was a low-risk visual/static change. Zero verification commands; no browser/runtime checks, builds or tests.

## [2026-11-11] Require committed worktree handoff checkpoints
**Type:** Docs
**Board:** BOARD-115 | **Branch:** docs/require-committed-worktree-handoff-checkpoints
**Changed:** `AGENTS.md` and `templates/project/AGENTS.md` §B5/§B11; `.opencode/commands/closeout.md`, `.opencode/commands/handover.md`, `.opencode/skills/git-worktree/SKILL.md` §6/§8; `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md` (ADR-074), this log. Extended existing instructions; no new files or tools.
**Why:** Approved handoff policy requires local task commits and a reported SHA/diff, including clearly labelled `wip` checkpoints for blocked or unfinished work.
**Impact:** Checkpoints do not imply merge readiness; verification, review, human-merge and integration-branch protections remain. Docs-only parent review passed; local task commit prepared for human review. BOARD-114 remains blocked and not merge-ready; no migration or security-policy changes or approval to merge the migration.
**Verification:** Verification limited to file review because this was a low-risk visual/static change.

## [2026-11-11] OpenCode V2 port, chunk 1
**Type:** Chore
**Board:** BOARD-114 | **Branch:** feat/port-factory-harness-to-opencode-v2
**Changed:** tracked `.kilo/` harness moved to `.opencode/` with plural agents/commands; `opencode.jsonc`; existing Python/JS path references, native permission generator, factory base selector, templates and active docs. Added architect primary because no existing primary orchestrator definition covered that role; retained six specialists and upstream licences. App base semantics unchanged.
**Why:** Approved OpenCode-only integration port on `opencode`; `main` retains Kilo. Reused lifecycle, env, scope, board and QA mechanics rather than introducing replacement tools.
**Impact:** Chunk 1 only, not merge-ready. Bootstrap worktree stays unmoved and ignored; steady-state guards accept only `.opencode/worktrees/`. Security plugin/search-path enforcement, native runtime validation and devcontainer migration remain later work. No dependencies, commit, merge or push.
**Verification:** `python3 .opencode/skills/git-worktree/scripts/test_env.py` → exit 0, `all checks passed`; the only verification command. Runtime package ignores are root-anchored so moved board UI manifests remain trackable.

## [2026-11-11] The /plan and /unslop commands
**Type:** Chore
**Board:** BOARD-113 | **Branch:** chore/add-plan-and-unslop-commands
**Changed:** `.kilo/command/plan.md`, `.kilo/command/unslop.md`, `docs/UI-UX.md` §2.1, `docs/changelog/CHANGELOG.md`
**Why:** The plan and unslop skills sit in `.kilo/skills/`, but the skill loader does not expose them, so neither was discoverable as a command. Both procedures were already the rules; they were only reachable by asking.
**Impact:** `/plan` packages the plan skill's five phases into a product-planning shortcut that points at the decision gate; `/unslop` packages the unslop procedure — direction, sign audit, nine passes, checklist — and writes the audit to `docs/reviews/<task-id>-unslop.md`. Neither command adds a rule: both name the by-path read and defer to `AGENTS.md`. The command directory is part of the harness slice, so a project copy carries both.

## [2026-11-11] The board screen becomes a dense dashboard
**Type:** Feature
**Board:** BOARD-112 | **Branch:** feat/rebuild-factory-pages-as-a-split
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `.kilo/skills/board/ui/src/app.css`, `.kilo/skills/board/static/board.css`, `docs/UI-UX.md` §6.2, `docs/reviews/BOARD-112-*.md`, `docs/changelog/CHANGELOG.md`
**Why:** The board was still the single-column console while `/gallery` already carried the approved dashboard shell. The user asked for an elegant, dense, useful dashboard, so the real board moved onto the same components.
**Impact:** `GET /` now renders a 240px lane/filter sidebar, a main column with a KPI strip, flow meter and lane panel, and a 320px sticky worktrees rail. All filters, search, keyboard, URL state, folds, pause/refresh, parsed Notes and branch copy are preserved. The old inline CSS and its renderers are removed; the Tailwind stylesheet is the only style system. Footer pluralisation and the copy-button tap target were fixed from the review.

## [2026-11-11] The factory page language moves to Tailwind
**Type:** Feature
**Board:** BOARD-112 | **Branch:** feat/rebuild-factory-pages-as-a-split
**Changed:** `.kilo/skills/board/ui/package.json`, `.kilo/skills/board/ui/package-lock.json`, `.kilo/skills/board/ui/src/app.css`, `.kilo/skills/board/static/board.css`, `.kilo/skills/board/static/fonts/*`, `.kilo/skills/board/scripts/board_serve.py`, `.kilo/skills/board/SKILL.md`, `docs/DECISIONS.md` (ADR-072), `docs/STACK.md`, `docs/UI-UX.md` §6.2, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-11-factory-tailwind.md`
**Why:** The board screen read as a generic Bootstrap-style stack, and the single-file hand-written CSS made a consistent component language slow to evolve. The user chose Tailwind v4 with a self-hosted Geist pair and a Swiss-industrial direction.
**Impact:** The board UI is now built from Tailwind v4 at author time into one committed stylesheet; the runtime stays Python-standard-library and offline. `GET /gallery` is rebuilt in the new language; the board screen moves onto the same components in the next chunk. Self-hosted Geist Sans/Mono (SIL OFL) replace system fonts, so the page is noticeably more distinctive and the repo grows by about 140 KB of woff2. A class change now requires `npm --prefix .kilo/skills/board/ui run build`.

## [2026-11-11] The factory page language and component gallery
**Type:** Feature
**Board:** BOARD-112 | **Branch:** feat/rebuild-factory-pages-as-a-split
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/UI-UX.md` §6.2, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-11-factory-workbench.md`
**Why:** The split-workbench direction needed a settled token set and a reusable component factory before the board screen could be rebuilt. The gallery is the human approval artefact for that language.
**Impact:** Light and dark colour tokens move to paper/graphite with one signal-orange accent, and a `wb-` component set is shared by `/gallery` and, in the next chunk, the board. `GET /` keeps its structure, filters, keyboard and URL state, and gains one quiet footer link to `/gallery`. Routing, dependencies and the read-only, server-rendered, offline behaviour are unchanged.

## [2026-11-11] The unslop pass is mandatory on every UI change
**Type:** Docs
**Board:** BOARD-111 | **Branch:** docs/make-the-unslop-pass-mandatory
**Changed:** `AGENTS.md` (§B4.2, §B4.3), `docs/UI-UX.md` (§2.1), `.kilo/agent/ui-critic.md`, `.kilo/agent/frontend-dev.md`, `.kilo/skills/qa-review/SKILL.md`, `docs/changelog/CHANGELOG.md`
**Why:** The BOARD-109 review read the unslop signs list but never ran the unslop procedure, and the loader does not expose the `unslop` skill, so nothing forced an agent to open it. A real audit of the merged console then found uppercase tracked labels, negative tracking on small text, redundant 650/700 weights and five equal stat cards — signs the QA and UI pass had let through.
**Impact:** Every UI change now runs the full unslop procedure — five-line direction, full `references/signs.md` audit, nine passes, checklist — in the same review round as the QA capture, recorded in the UI report. A UI row with no recorded unslop audit cannot leave `In Review`. The skill is opened by path because the loader does not expose it. Precedence is unchanged: where the skill and `AGENTS.md` disagree, `AGENTS.md` wins, and the conflict is reported.

## [2026-11-11] The board console passes the unslop audit
**Type:** Fix
**Board:** BOARD-110 | **Branch:** fix/fix-the-unslop-signs-in-the-board-console
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/UI-UX.md` §6.1, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-11-unslop-board-console.md`
**Why:** The merged console (BOARD-109) tripped four sign groups in `.kilo/skills/unslop/references/signs.md`: five equal stat cards for the lane counts, uppercase tracked labels, negative tracking on small text, and weights of 650 and 700. The palette, type scale, layout and controls were already right, so this is a polish pass only.
**Impact:** The five lane counts are one framed flow instrument of five hairline-separated stops; only the stop with the highest non-zero count carries the accent, and on mobile the instrument scrolls rather than stacking. Lane names and table headers are sentence case with normal tracking, small-text tracking is zero, and every weight is 400, 500 or 600. Counts, click-to-filter, aria-pressed sync and the all-clear headline are unchanged; the viewer stays read-only, server-rendered and offline.

## [2026-11-10] The live board becomes a factory console
**Type:** Feature
**Board:** BOARD-109 | **Branch:** feat/elevate-the-live-board-ui-into-a-factory-console
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `.kilo/skills/board/SKILL.md`, `docs/UI-UX.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-factory-board-console.md`
**Why:** The viewer was a vertical accordion that showed cards but not the shape of the flow, and its lane and notes content was slow to scan. The board is the orchestrator's main surface, so it needs a dense, keyboard-first console with filters, parsed acceptance criteria and the worktree state in the same view.
**Impact:** `GET /` now renders again after a `TypeError` in `render_pipeline()` that broke the whole page while `/health` and the JSON endpoints stayed up. The page keeps its read-only, server-rendered, offline behaviour, and `/api/board` and `/api/worktrees` are unchanged. The visual language is recorded in `docs/UI-UX.md` §6.1.

## [2026-11-10] The teardown command sets the board lane
**Type:** Fix
**Board:** BOARD-108 | **Branch:** fix/cleanup-and-discard-set-the-board
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-cleanup-and-discard-set-the-lane.md`
**Why:** `worktree.py cleanup --board BOARD-107 --apply` removed the worktree, deleted the branch and cleared the row's `Branch/Worktree` cell, but left the row in `Pending Merge`. The lane is the source of truth for what is in flight, so a row whose branch is merged and whose worktree is gone must read `Merged`. A discard left the same confusion in `In Progress`.
**Impact:** The teardown command owns the lane for the row it tears down (ADR-071). `cleanup --board <ID> --apply` puts the row in `Merged` and clears the cell; `discard --board <ID> --apply` puts the row back in `Ready` and clears it; the slug form of `cleanup` cannot know the row and touches nothing on the board. `clear_row_worktree` takes the lane as an argument and writes the lane cell and the worktree cell in the same atomic write, so they never drift. A refused cleanup or discard changes nothing on the board. The board write stays in the control repo's main checkout. `AGENTS.md` §B4 rule 12 and §B3 say the script is the board's writer for a teardown the human runs, so the orchestrator does not set the lane by hand afterwards.

## [2026-11-10] The specialist skills, ported as a read-on-demand catalogue
**Type:** Feature
**Board:** BOARD-107 | **Branch:** feat/port-the-specialist-skill-catalog
**Changed:** `.kilo/catalog/` (67 skill folders + `README.md`, 438 upstream markdown files), `AGENTS.md`, `.kilo/agent/frontend-dev.md`, `.kilo/agent/backend-dev.md`, `.kilo/agent/mobile-dev.md`, `.kilo/agent/qa-reviewer.md`, `.kilo/agent/docs-writer.md`, `.kilo/skills/git-worktree/scripts/guard.py`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STRUCTURE.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-specialist-skill-catalog.md`
**Why:** The builders need specialist depth — a React, a FastAPI, a Postgres, a Playwright expert — without 67 skills crowding the system prompt. The upstream catalogue (MIT, © 2025 Jeffallan, https://github.com/Jeffallan/claude-skills) is kept as files the agent reads when the task is in that domain.
**Impact:** The catalogue lives at `.kilo/catalog/<skill>/`, outside the auto-discovered skills folder: the loader only scans directories named `skill`/`skills`, so `.kilo/catalog/` is invisible to it and none of the 67 skills enters the system prompt. `kilo debug skill` still lists exactly the six repository skills — `board`, `git-worktree`, `qa-review`, `plan`, `unslop`, `kilo-config`. Every upstream file is carried over byte for byte with its MIT frontmatter; each `SKILL.md` gains a three-line header that maps the Claude Code tool names onto this harness, and 20 `AskUserQuestion` mentions plus 13 subagent mentions in the body become `question tool` and `Task tool agent`. The index at `.kilo/catalog/README.md` is read first, then the one matching `SKILL.md`. `AGENTS.md` §A7 gains a Specialist skills section that states the precedence rule once — this repository's rules win — and each builder agent file names its own specialists. `guard.py sync` now carries `catalog` in its slice, so a project receives the catalogue with the rest of the harness.

## [2026-11-10] The plan skill, merged from two upstream skills
**Type:** Feature
**Board:** BOARD-106 | **Branch:** feat/port-a-merged-plan-skill
**Changed:** `.kilo/skills/plan/` (SKILL.md, references/ ×12), `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STRUCTURE.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-plan-skill.md`
**Why:** A new project or a large feature needs a planning procedure that writes into the documents this repository already has. The upstream `feature-forge` and `architecture-designer` skills carry the question banks, the specification template, the EARS syntax, the ADR template and the NFR checklist, and nothing of their own was kept.
**Impact:** One merged skill at `.kilo/skills/plan/`, with all twelve upstream references carried over intact under their MIT credit lines. Each of the five phases names the document it writes into: `DOMAIN.md`, `docs/BUSINESS-LOGIC.md`, `docs/DECISIONS.md`, `docs/RISKS.md`, `docs/STACK.md`, `ROADMAP.md` and `docs/BOARD.md`. The upstream `AskUserQuestions` tool becomes the `question` tool, the upstream `Task` subagents become this harness's `Task` tool, and the upstream "write a spec document" step becomes "write into the mapped document". The precedence rule is stated once, in the skill, and referenced from `AGENTS.md` §A2, §A4 and §A6. Attribution: MIT, © 2025 Jeffallan for the two upstream skills; MIT, © Jesse Vincent for the two superpowers research documents.

## [2026-11-10] The unslop skill, adopted and merged into the QA lane
**Type:** Feature
**Board:** BOARD-105 | **Branch:** feat/add-the-unslop-skill-and-merge
**Changed:** `.kilo/skills/unslop/` (SKILL.md, references/, scripts/snapshot.mjs, examples/), `.kilo/skills/qa-review/SKILL.md`, `.kilo/agent/ui-critic.md`, `AGENTS.md`, `docs/UI-UX.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STRUCTURE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-unslop-skill-and-qa-checker.md`
**Why:** The 15 anti-slop rules catch the loud tells but not the quiet ones — a stray `mt-[13px]`, a mixed number format, an icon nudged off its column. The upstream skill carries a full sign-by-sign checklist, and it belongs in the lanes that judge a screen.
**Impact:** The unslop skill (Damir Sokolovsky, CC BY 4.0) is adopted as a standalone skill at `.kilo/skills/unslop/`, and its signs list is merged into the QA lane: `AGENTS.md` §B4.3 states the precedence rule once, the qa-review skill and the ui-critic agent each add the unslop pass, and `docs/UI-UX.md` §2.1 points at the list. The story video and every image-generation instruction are removed, so a visual is built in code; `scripts/snapshot.mjs` resolves Playwright and chromium the way the QA script does and exits 2 when no browser is found. The credit line survives in every copied file.

## [2026-11-10] The teardown is named by the board row
**Type:** Feature
**Board:** BOARD-104 | **Branch:** feat/hand-off-names-the-teardown
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** The hand-off block named the cleanup by slug and listed the worktree removal and the branch deletion as loose lines, so the human had to read the path back out of the block to run the teardown.
**Impact:** `worktree.py cleanup` takes `--board <ID>` as an alternative to the slug: it resolves the row's `Branch/Worktree` cell, runs the same cleanup, and clears that cell when the worktree is gone. Giving a slug and `--board` together, or neither, is a usage error. The hand-off block now ends with a teardown section that names `cleanup --board <ID> --apply` and, below it, the manual `git worktree remove` and `git branch -d` pair; the old cleanup lines are gone from the block. `AGENTS.md` §B5 says the block ends with that command. The slug form of `cleanup` and every other command keep their behaviour.

## [2026-11-10] The hand-off block, printed by the script
**Type:** Feature
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** Every work session had to hand the human the merge command, and usually forgot the diff command, so the human could not review the work before merging it.
**Impact:** `worktree.py handoff --board <ID>` prints the hand-off block for a row's worktree: the path, the branch, the base, the diff command, the log command, the merge command and the cleanup command. It prints commands and paths only and never changes anything. A branch already merged into the base gets a `git show --stat` line instead of a merge command that would fail. `AGENTS.md` §B5 now requires every session report for work in a worktree to end with that block, diff command first.

## [2026-11-10] Forced discard, confirmed in two steps
**Type:** Feature
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** `discard` refused a dirty worktree or a branch with unmerged commits, so the only way to destroy that work was by hand, and a hand `git worktree remove --force` left nothing behind to recover from.
**Impact:** `discard --force` alone prints the destruction plan — the path, the branch, the unmerged and dirty counts and exactly what is lost — and refuses without writing a file or deleting anything. `discard --force --yes` acts, and before it destroys anything it writes the uncommitted changes as a patch and the lost commit shas into the recovery files under the repository's `cleanup-wt/` folder, printing both paths. `--force` only relaxes the refusal: `--apply` still governs acting on the normal path, and `--yes` without `--force` is a usage error. The policy, the permission map and the board are unchanged.

## [2026-11-10] Corrective round: distinct create refusals, section order, symlink-safe env copy
**Type:** Fix
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/env.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** The review found that `create` used one refusal message for two situations, so a row whose slug directory was taken by another row was told to `resume` or `discard` a worktree it did not have — a circle. The two new SKILL.md sections were also numbered 2b and 2c but placed before the existing 2a, and the env copy followed a symlink planted at the destination.
**Impact:** `create` now prints a separate message when the slug directory belongs to another row: it names the owning row when the board records one and offers only a new `--slug` or `discard` for that owning row. The SKILL.md sections now read 2a Env files, 2b Reuse a worktree, 2c Repos. The env copy is written with `O_NOFOLLOW`, so a symlink at the destination is replaced by the copy instead of being written through. No change to the policy, the permission map or the board.

## [2026-11-10] Provision env files into worktrees and reuse an existing worktree
**Type:** Feature
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/env.py`, `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`
**Why:** A new worktree had no local env files, so the application could not start there, and the agent could not read or copy them because the policy denies reading them. Separately, `worktree.py create` did not notice a worktree that already existed for the same board row, so agents piled up duplicates.
**Impact:** `create` copies `.env` and `.env.local` from the repository's main checkout into the new worktree with mode `0600` and lists them in the repository's `.git/info/exclude`; the contents are never printed and the read policy is unchanged. `create` now refuses when the row already has a live worktree and prints the resume / discard / new-slug options. New `resume` and `discard` commands reuse or remove that worktree, `cleanup` removes the env copies, and `list` gained a `state` column. No behaviour change to the existing commands beyond the new refusal and the env provisioning.

## [2026-11-04] Board heading gets the page gutter
**Type:** Fix
**Board:** BOARD-102 | **Branch:** feat/compact-accordion-redesign-of-the-live
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/changelog/CHANGELOG.md`
**Why:** The board section had no CSS rule, so its heading and count line ran flush to the viewport edge while the lane stack and the header had a 24px gutter.
**Impact:** The board section now carries the same horizontal gutter as the header and the lane stack, and the lane stack's own margins were made relative so its cards stay aligned with the heading above them. Content, behaviour, the JSON endpoints and the escaping are unchanged.

## [2026-11-04] Board viewer fixes from QA round 1
**Type:** Fix
**Board:** BOARD-102 | **Branch:** feat/compact-accordion-redesign-of-the-live
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/changelog/CHANGELOG.md`
**Why:** The first QA pass found text clipped at narrow widths, a favicon request to the network, and lanes that looked populated while holding no cards.
**Impact:** Long values now wrap instead of clipping, the favicon is inline so the page makes no extra request, a lane with no cards stays collapsed, the board path is shown as a path, and a 480px breakpoint tightens the header, filter and panels. Content, behaviour, the JSON endpoints and the escaping are unchanged.

## [2026-11-04] Compact accordion board viewer
**Type:** Feature
**Board:** BOARD-102 | **Branch:** feat/compact-accordion-redesign-of-the-live
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`
**Why:** The viewer was a horizontal kanban with every lane always open, so the growing Merged lane forced an endless scroll and hid the work that was in flight.
**Impact:** The dashboard now renders the lanes as a vertical accordion of collapsible sections, cards as compact rows that expand to their detail, the Merged lane as the last 10 rows with a "Show all" control, and fold state kept in the browser. Read-only behaviour, the board file and the JSON endpoints are unchanged.

## [2026-11-02] Make worktree-only changes deterministic
**Type:** Fix
**Board:** BOARD-001 | **Branch:** chore/enforce-worktree-only-changes-and-serve
**Changed:** `.kilo/policies/git-policy.json`, `kilo.jsonc`, `.kilo/skills/git-worktree/scripts/guard.py`, `.kilo/skills/git-worktree/SKILL.md`, `.kilo/skills/board/scripts/board_serve.py`, `docs/changelog/CHANGELOG.md`
**Why:** The worktree rule was prose the model had to obey. Edits in the main checkout were allowed, `git commit` was allow-listed, no hook enforced the rule, and the board server showed one board.
**Impact:** The `edit` permission map now denies every path by default and allows only `**/.kilo/worktrees/**`; `docs/BOARD.md` is denied to file tools. A new `in_worktree` policy check denies `git commit` in the main checkout, and `guard.py install-hooks` writes a fail-closed pre-commit hook into the control repo and every mapped repository. `board_serve.py` discovers and renders both the harness board and the project board, and `/api/board` returns both. Verified: main-checkout commit denied, worktree commit allowed, `check-policy` in sync, both boards listed over HTTP.

## [2026-11-02] Close the last two gaps in the worktree rule
**Type:** Fix
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `.kilo/skills/git-worktree/scripts/{guard.py,worktree.py}`, `.kilo/policies/git-policy.json`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/changelog/CHANGELOG.md`
**Why:** Two things were documented but not true. A commit straight onto `dev` in a microservice was allowed, because only `main`, `master` and `base` were protected, and the microservices base on `dev`. And `worktree.py create` wrote the pointer into the new worktree but not into the repository root, so a brand-new repository had no pointer until a separate `sync` ran.
**Impact:** `protected_branches` in `.kilo/policies/git-policy.json` now names `dev` as well, and the repository's own default branch from `origin/HEAD` is always added. `guard.py check-git` refuses a commit on the base branch in every repository. `worktree.py create` writes the pointer into the repository root and into the new worktree, so a new repository is complete the moment its first worktree is created. Verified on a throwaway repository: the pointer appeared in both places, was excluded from git, a commit on `dev` was blocked and a commit on the worktree branch was allowed.

## [2026-11-02] Give a work surface a pointer instead of a copy of the rules
**Type:** Chore
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `.kilo/skills/git-worktree/scripts/{scope.py,guard.py,worktree.py}`, `.kilo/skills/board/scripts/board.py`, `.kilo/skills/git-worktree/SKILL.md`, `.kilo/scopes/service.md`, `AGENTS.md`, `docs/{DECISIONS,HANDOVER,PROJECT_STRUCTURE}.md`, `docs/changelog/CHANGELOG.md`
**Why:** The harness was copied into every work surface, so a factory change had to be re-applied in every application repository and the factory could not grow without touching them all. The board was also unreachable from inside a work surface, because the harness looked for `apps/<repo>/docs/BOARD.md`.
**Impact:** The harness stays in the control repo. A work surface receives one generated file, `AGENTS.md`, that names the project, the canonical scope rules and the unit's documentation; it is listed in the repository's `.git/info/exclude`, so it is never committed. `guard.py sync --all` refreshes every pointer in one command. The harness now finds the control repo by walking up, so the board, the repo map and the guard rails work from inside any work surface. ADR-058, ADR-059 and ADR-060 record the decisions. No application behaviour changes.

## [2026-11-02] Split the factory from the project
**Type:** Chore
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `AGENTS.md` (§A1 "The factory and the project", §A2 boot sequence), `README.md`, `.gitignore` (ignores `/project/`), `.kilo/repos.json` (the control repo only), `docs/{BOARD,DECISIONS,ENVIRONMENT,HANDOVER,PROJECT_STATE,PROJECT_STRUCTURE,README,STACK}.md` (rewritten for the factory), `docs/changelog/CHANGELOG.md`, `templates/project/**` (new: the blank project skeleton)
**Why:** The factory and the product shared one repository, so 79 project handover files, the platform architecture and the product's risk register were committed to the software factory, and the factory's board carried product rows.
**Impact:** The factory holds the harness only — rules, agents, commands, skills, policies, scope rules and the blank project skeleton. The Inhouz Cloud AI platform is its own git repository in `project/`, with its own board, documentation set, domain rules and 75 application repositories. `guard.py check-repos` exits 0 in both. The decision log is split: ADR-001 to ADR-099 are the factory's, the project's own decisions start at ADR-100. A project copies the harness in and owns the copy, so a factory change does not reach a project automatically. No behaviour changes.

## [2026-10-30] Deny every tool read access to git config, credential and .env files
**Type:** Security
**Board:** - | **Branch:** main (uncommitted)
**Changed:** `.kilo/policies/git-policy.json` (expanded `hidden_paths`, added `allow` list and edit denials), `.kilo/skills/git-worktree/scripts/guard.py` (expands `hidden_paths` into `read`/`grep`/`glob`/`list` deny rules and honours the allow list; `check-policy` compares every generated tool key), `kilo.jsonc` (generated), `.devcontainer/kilo-redact.sh` (new protected-file guard in the `$BASH_ENV` startup file), `.devcontainer/test-kilo-redact.sh` (10 guard checks), `.devcontainer/devcontainer.json` (`KILO_CONFIG` points at the root `kilo.jsonc`, so no subfolder copy is needed), `.kilo/skills/git-worktree/SKILL.md` (§3), `docs/DECISIONS.md` (ADR-052), `docs/HANDOVER.md`
**Why:** A git config or credential file can hold a token in a URL, a credential helper or an extra HTTP header, and a `.env` file holds application secrets. The agent never needs to read any of them, but only the `read` tool was blocked before, and a nested app repository did not load the root config.
**Impact:** `read`, `grep`, `glob` and `list` deny `.env`, `.env.*` (except `.env.example`), `.git/config`, `*.git/config`, submodule configs, `.git-credentials`, `~/.gitconfig`, the XDG git config and credential stores, `.npmrc`, `*.pem`, `*.key`, `*.p12` and `id_rsa*`. `edit` denies the same secret files. The `$BASH_ENV` guard refuses any `bash -c` command whose text names a protected file, in every subfolder and every repository; `.env.example` and `process.env` stay allowed. `KILO_CONFIG` points at the root config so nested repositories inherit it without a copy. No application behaviour changes. A Kilo restart is needed for the new permission block; the shell guard is active as soon as the file is installed. Shell commands that merely mention `.env` (for example a commit message) are also refused by the guard.

## [2026-10-30] Redact credentials from every shell command's output
**Type:** Security
**Board:** BOARD-002 | **Branch:** chore/redact-credentials-from-every-shell-command
**Changed:** `AGENTS.md` (§B11 — a credential never reaches a transcript through a URL), `.devcontainer/kilo-redact.sh` (new), `.devcontainer/test-kilo-redact.sh` (new), `.devcontainer/devcontainer.json` (`remoteEnv.BASH_ENV`, install step in `postCreateCommand`), `docs/{ENVIRONMENT,STACK,RISKS,DECISIONS,PROJECT_STATE}.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-redact-credentials-from-shell-output.md`
**Why:** The machine's global git config carried a `url.https://<token>@github.com/.insteadOf` rewrite, so `git remote -v` printed the credential in plaintext and it reached an agent transcript. The rewrite is removed — the token now lives in `/home/node/.git-credentials` (mode `600`) behind git's credential helper — and a `sed` filter installed as the container's `$BASH_ENV` startup file now scrubs both output streams of every shell command.
**Impact:** No URL carries a credential, so no routine git command can disclose one. `$BASH_ENV` is used because Kilo Code runs shell tools as `/bin/bash -c` and Debian's `~/.bashrc` returns immediately for a non-interactive shell. Output with no credential is byte-identical, including binary output; the exit code, the stdout/stderr split and the output order are preserved. The filter needs a container rebuild or window reopen to activate. The token itself was printed once and must be rotated at GitHub.

## [2026-10-30] Multi-repo support in the board and the git tools
**Type:** Feature
**Board:** BOARD-003, BOARD-004 | **Branch:** feat/multi-repo-support-in-the-board, docs/multi-repo-rules-agent-and-documentation
**Changed:** `.kilo/repos.json` (new), `.kilo/scopes/{web,mobile,api}.md` (new), `.kilo/skills/board/scripts/board.py` (`Repos` column, `add-column`, `add --repos`, `set-field --field repos`, strict row parsing), `.kilo/skills/board/scripts/board_serve.py` (column list), `.kilo/skills/git-worktree/scripts/worktree.py` (`create --repo`, board-driven `cleanup`/`verify`, repo-wide `list`), `.kilo/skills/git-worktree/scripts/guard.py` (`sync`, `check-repos`, policy root follows the shell, sync writes into the shell's tree), `.kilo/policies/git-policy.json` (`.kilo/scopes/*.md` asks), `kilo.jsonc` (generated), `.kilo/skills/{board,git-worktree}/SKILL.md`, `AGENTS.md` (§A1 multi-repo, §A7 script table, §B1, §B3 `Repos` column, §B4 repo-aware worktrees, the control-repo subsection), `.kilo/agent/docs-writer.md` (repository-aware units), `README.md` (multi-repo section), `apps/{web,mobile,api}/AGENTS.md` (synced copies), `docs/{PROJECT_STRUCTURE,HANDOVER,DECISIONS,README}.md`, `docs/handover/{README,web,mobile,api}.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-multi-repo-support-in-the-board.md`
**Why:** An application that keeps its own git repository under `apps/` could not be worked in: nothing could name the repo a row belonged to, nothing could give that repo the same guard rails, and the rules and the documentation still described a single repository.
**Impact:** The board gains a `Repos` column, migrated by `board.py add-column` instead of a hand edit. `worktree.py create --repo <id>` creates the worktree in that repo and keeps the board in the control repo. `guard.py sync --repo <id>` copies the `.kilo/` slice, the scope rules and the permission map into the target repo; `guard.py check-repos` proves the map and the `apps/` layout agree. `guard.py check-policy` now reads and writes the policy and config of the tree the shell is in, so a builder in a worktree no longer rewrites the main checkout; `guard.py sync` does the same and no longer fails when the target is the control repo itself. `AGENTS.md` and the `docs-writer` agent describe the control repo, the work surfaces and the repo map, and the scope rules are canonical in `.kilo/scopes/<id>.md` with `apps/<id>/AGENTS.md` as their synced copies.

## [2026-10-30] A documentation agent owns the application memory map
**Type:** Feature
**Board:** BOARD-002 | **Branch:** feat/add-a-documentation-agent-that-writes
**Changed:** `.kilo/agent/docs-writer.md` (new), `.kilo/command/handover.md` (rewritten, now routed to `docs-writer`), `docs/handover/{README,web,mobile,api}.md` (new), `AGENTS.md` (§A7 agent table, §A10 doc table, §B1 doc table, §B2), `docs/{README,PROJECT_STRUCTURE,HANDOVER,DECISIONS}.md`, `README.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-docs-writer-and-application-memory-map.md`
**Why:** The handover was one file written from memory of a system, and a reader could not tell which parts of the code were pure and which touched the outside world.
**Impact:** `/handover` now runs the `docs-writer` agent, which reads the whole codebase on its first run in a session and writes one memory map per application under `docs/handover/` plus a global index. Every module is marked pure, reactive or effectful, and every claim carries a `file:line`. `docs/HANDOVER.md` stays as the factory's own handover. No behaviour change to the build, QA or merge lanes.

## [2026-10-30] One guard-rail policy, two enforcement layers
**Type:** Feature
**Board:** BOARD-001 | **Branch:** feat/add-a-permission-file-and-git
**Changed:** `.kilo/policies/git-policy.json` (new), `.kilo/skills/git-worktree/scripts/guard.py` (`check-git`, `check-policy`, `policy`), `kilo.jsonc` (generated `permission` map), `.kilo/skills/git-worktree/SKILL.md` (§3), `AGENTS.md` (§A7 table, §B9, §B11), `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `.kilo/command/{run,closeout}.md`, `docs/{PROJECT_STRUCTURE,HANDOVER,DECISIONS,PROJECT_STATE}.md`, `README.md`, `docs/changelog/CHANGELOG.md`
**Why:** The guard rails were prose in `AGENTS.md` and nothing stopped an agent from running `git push`, committing on `main`, or switching branches inside a worktree.
**Impact:** One policy file is the source of truth for the guard rails. The generated `permission` map in `kilo.jsonc` now denies the irreversible git commands (`git push`, `git reset --hard`, `git clean`, `git checkout --`, `git branch -D`, a raw `git worktree remove`, `git filter-branch`, `git filter-repo`, `git reflog expire`, `git gc`, `git update-ref -d`) and asks before the rest that changes history or the remote. `guard.py check-git` adds the three context checks a keyword list cannot make: no commit on `main`/`master`/`base`, no branch switch inside a worktree, and no raw `git worktree remove`. Edits to the rules files ask first; the real `.env` and key files are denied. `guard.py check-policy` proves the two layers still match.

## [2026-10-29] Starter: front page, no test residue, empty board
**Type:** Chore
**Board:** BOARD-013 | **Branch:** chore/starter-repo-prep
**Changed:** `README.md` (new), `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, removed `artifacts/factory/qa/2026-10-29/BOARD-012/notes.md`, emptied `docs/BOARD.md`
**Why:** The repo is going public as a starter to plug into any project, so it needs a front page, no test residue, and a board that starts empty.
**Impact:** No behaviour change. A fresh clone has an empty board; the first row is added with `board.py add`. The handover and project state describe the starter, not a running project.

## [2026-10-29] One driver for the capture path, failures reported not routed around
**Type:** Chore
**Board:** BOARD-012 | **Branch:** chore/remove-cdp-and-report-failures
**Changed:** `.kilo/skills/qa-review/scripts/browser-review.mjs`, `AGENTS.md`, `.kilo/skills/qa-review/SKILL.md`, `.kilo/command/{ui,run}.md`, `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `docs/{UI-UX,STACK,HANDOVER,DECISIONS}.md`, `docs/changelog/CHANGELOG.md`
**Why:** The capture script advertised a CDP fallback it never had, and the incident behind the "ask before building a tool" rule was described with a protocol name instead of what actually happened.
**Impact:** The capture path drives Playwright only. `--chromium <path>` is a plain binary path handed to Playwright's launch, the resolution order is flag → env var → downloaded → system, and a missing chromium exits 2 with the searched list instead of being installed or replaced. A new rule makes an agent report a failed command, capture, or test instead of routing around it.

## [2026-10-29] One canonical artifacts folder, ask before building a tool
**Type:** Chore
**Board:** BOARD-010 | **Branch:** chore/one-artifacts-folder-and-ask-before
**Changed:** `.kilo/skills/qa-review/scripts/browser-review.mjs`, `.gitignore`, `AGENTS.md`, `docs/{UI-UX,HANDOVER,DECISIONS,PROJECT_STRUCTURE}.md`, `docs/changelog/CHANGELOG.md`, `.kilo/skills/qa-review/SKILL.md`, `.kilo/command/{ui,run}.md`, `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `apps/{web,mobile}/AGENTS.md`
**Why:** UI evidence was scattered across app folders, `docs/`, and `/tmp`, and an agent built a browser driver instead of asking, while Playwright was already installed globally.
**Impact:** All UI evidence lands under `artifacts/<scope>/qa/<date>/<task-id>/` in the main checkout; the capture script computes the path itself and writes `notes.md`. Review reports and ledgers stay in `docs/reviews/` — documents, not artifacts. A new rule makes an agent check for existing tooling and ask before building any.

## [2026-10-29] Live board viewer, bounded UI loop, gated UI tooling
**Type:** Feature
**Board:** BOARD-008, BOARD-009 | **Branch:** feat/live-board-viewer-html-dashboard-with
**Changed:** `.kilo/skills/board/scripts/board_serve.py` (new), `.kilo/skills/qa-review/scripts/{browser-review.mjs,check-finding.py,ledger.py}`, `.kilo/skills/board/scripts/board.py`, `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/{board,qa-review}/SKILL.md`, `.kilo/command/{board-view,run,ui}.md`, `.kilo/agent/{qa-reviewer,ui-critic}.md`, `kilo.jsonc` (Playwright MCP), `.devcontainer/devcontainer.json` (port 15180), `AGENTS.md`, `docs/{STACK,DECISIONS}.md`
**Why:** The markdown board is hard to scan, the UI critique → fix loop could run forever, and Playwright was installed but unreachable — so the agent built a browser driver by hand and looped proving it worked.
**Impact:** A read-only dashboard on port 15180 shows the lanes and the live worktrees. The QA loop is capped at 3 rounds with fingerprint dedupe and a ledger. The Playwright MCP is configured and the capture script resolves the global Playwright, so no hand-rolled browser client remains.
## [2026-11-11] OpenCode security adapter awaiting fixture access
**Type:** Feature
**Board:** BOARD-114 | **Branch:** feat/port-factory-harness-to-opencode-v2
**Changed:** `.opencode/plugins/factory-guard/`, canonical policy, guard file/search checks, config sync, STACK and session state
**Why:** Native search permissions do not enforce target paths; copied control repos need the complete runtime configuration
**Impact:** Incomplete security migration. Node tests exited 1 on temporary fixture directory EACCES; no workaround attempted. Container and native runtime verification remain pending.
