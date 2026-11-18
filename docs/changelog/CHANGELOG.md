# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-11-18] Clarify frontend design direction and composition
**Type:** Docs
**Board:** BOARD-120 | **Branch:** docs/clarify-frontend-design-direction-and-composition
**Changed:** `.kilo/agent/frontend-dev.md`, `.kilo/scopes/web.md`, `AGENTS.md`, `templates/project/AGENTS.md`, `docs/UI-UX.md`, `templates/project/docs/UI-UX.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`.
**Why:** Apply five explicitly approved permanent-rule clarifications in existing sections: builder role, substantive design brief, gallery scope, approved redesign scope, and chrome/content colors.
**Impact:** Factory/template guidance only, reversible by a later approved rule change. Future frontend assignments are affected if the guidance is wrong; existing project copies and application behavior are unchanged. Approval, gallery-before-screens, reuse, accessibility, auth/API preservation, no-production-build and mandatory QA/critique/unslop gates remain. No new files/tools or competing workflow; optional plan/unslop commands already defer to these rules and remain unchanged.
**Verification:** `git diff --check` passed (exit 0); orchestrator scoped diff review found no blocking inconsistency. Documentation-only: no build, tests, UI implementation or screenshots. Rule consistency does not prove visual results. User authorized committing the reviewed change and preparing human merge; Pending Merge follows commit and clean-tree verification.

## [2026-11-18] Ignore generated Playwright output in factory and template
**Type:** Chore
**Board:** BOARD-119 | **Branch:** chore/ignore-generated-playwright-output-in-factory
**Changed:** `.gitignore`, `.kilo/.gitignore`, `templates/project/.gitignore`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, `docs/changelog/CHANGELOG.md`.
**Why:** Reuse the three maintained ignore files to exclude five generated Playwright directory names at any depth.
**Impact:** Factory/template only; existing rules remain and no files are untracked. No new files or tools. User authorized commit and human-merge preparation; diff review passed with the static `.kilo` verification limitation recorded.
**Verification:** One command invocation: `git check-ignore --no-index --verbose --non-matching` with 42 synthetic probes, then `git diff --check` and scoped diff review (exit 0). Factory-root/template generated-directory and source probes passed at direct/nested levels. Existing `.git/info/exclude:52` (`.kilo/`) masks all `.kilo` probes, including source/config; that context is unverified, not a pass. No local-exclude change or workaround.

## [2026-11-18] Prepare reviewed bootstrap and handoff changes for merge
**Type:** Chore
**Board:** BOARD-117, BOARD-118 | **Branch:** chore/fix-project-bootstrap-and-template-drift
**Changed:** Handover and project state record explicit commit authorization and human merge handoff.
**Why:** Both shared rows passed focused verification and review; the user requested a commit and merge preparation.
**Impact:** Commit the intended change set, verify a clean worktree, and set both live rows Pending Merge. The agent does not merge or push. Earlier uncommitted notes below describe intermediate task history.

## [2026-11-18] Replace absolute handoff output with control-root-relative commands
**Type:** Fix
**Board:** BOARD-117 (shared BOARD-118 workspace) | **Branch:** chore/fix-project-bootstrap-and-template-drift (uncommitted)
**Changed:** Existing `cmd_lifecycle()` handoff formatting and handoff regression, worktree skill examples, handover, state, decisions and this log.
**Why:** Approved ADR-077 supersedes ADR-075: humans run commands from the control root; each clone remains independent of machine paths.
**Impact:** Review/lifecycle commands and workspace displays use `os.path.relpath` from the resolved control root, with shell quoting for command arguments and no `cd` prefix. Preserve actual executing script selection, discovery, all board/repo/target arguments, bootstrap architecture, policy and BOARD-118 assertion fixes. Reused existing function/test; no new helper or tool.
**Verification:** From `.kilo/skills/git-worktree/scripts`, ran `TMPDIR=/projects/kilo_inhouz_ai/.kilo/worktrees/fix-project-bootstrap-and-template-drift/.tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_lifecycle.LifecycleTests.test_mode_is_local_persistent_and_regenerates_permissions test_lifecycle.LifecycleTests.test_create_refreshes_required_base_map_in_optional_mode test_lifecycle.LifecycleTests.test_handoff_lists_all_repo_diffs_and_batch_commands`. All 3 tests passed in 2.007s, exit 0. Handoff checks exact relative output for both repos and primary/worktree scripts, root with spaces/apostrophes, batch selections, execution of review/preview commands from root, and byte-for-byte immutability; apply text only. No full suite, production build, real merge, commit, board edit or main/existing-project edit.

## [2026-11-18] Align stale required-mode assertions with approved ask policy
**Type:** Fix
**Board:** BOARD-118 (shared BOARD-117 workspace) | **Branch:** chore/fix-project-bootstrap-and-template-drift (uncommitted)
**Changed:** Two existing assertions in `test_lifecycle.py`, handover, state and this log.
**Why:** Required-mode regeneration and the copied base config now use the approved workspace-default `ask` action, not `deny`.
**Impact:** Test expectations only; protected-file/secret assertions, production lifecycle behavior and approved policy remain unchanged. Reused existing tests; no new helper, workspace, commit, board edit or real merge.
**Verification:** From `.kilo/skills/git-worktree/scripts`, ran `TMPDIR=/projects/kilo_inhouz_ai/.kilo/worktrees/fix-project-bootstrap-and-template-drift/.tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_lifecycle.LifecycleTests.test_mode_is_local_persistent_and_regenerates_permissions test_lifecycle.LifecycleTests.test_create_refreshes_required_base_map_in_optional_mode test_lifecycle.LifecycleTests.test_handoff_lists_all_repo_diffs_and_batch_commands`. All 3 tests passed in 1.715s, exit 0. Full suite and production builds were not run.

## [2026-11-18] Correct handoff regression fixture ordering
**Type:** Fix
**Board:** BOARD-117 | **Branch:** chore/fix-project-bootstrap-and-template-drift (uncommitted)
**Changed:** Added handoff setup in `test_lifecycle.py`, handover, state and this log.
**Why:** `add_row()` rewrites the fixture board from `self.rows`, erasing workspace entries previously added by CLI calls. Existing reuse coverage adds the fix row before creating workspaces.
**Impact:** Moved BOARD-002 creation before workspace creation; production lifecycle semantics and approved policy are unchanged. No new helper, commit, board/main-checkout edit or real merge.
**Verification:** `TMPDIR=/projects/kilo_inhouz_ai/.kilo/worktrees/fix-project-bootstrap-and-template-drift/.tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -k handoff -v` passed: 1 test in 0.871s, exit 0. Covers preview from outside control root, spaces/apostrophes, repeated board/repo and target arguments, exact printed apply structure and byte-for-byte preview immutability. Apply was not executed; full suite was outside the focused scope.

## [2026-11-18] Align the approved workspace-default policy fallback
**Type:** Fix
**Board:** BOARD-117 | **Branch:** chore/fix-project-bootstrap-and-template-drift (uncommitted)
**Changed:** First workspace-default edit rule in `.kilo/policies/git-policy.json`, decisions, handover, state and this log.
**Why:** Apply the explicitly approved `deny` to `ask` fallback correction already reflected in generated config.
**Impact:** Required mode asks for approval outside linked worktrees; optional fallback and protected-file/secret rules retain their existing behavior. `kilo.jsonc`, main checkout, board and existing projects remain unchanged.
**Verification:** One combined command: `TMPDIR=/projects/kilo_inhouz_ai/.kilo/worktrees/fix-project-bootstrap-and-template-drift/.tmp PYTHONDONTWRITEBYTECODE=1 python3 .kilo/skills/git-worktree/scripts/guard.py check-policy && TMPDIR=/projects/kilo_inhouz_ai/.kilo/worktrees/fix-project-bootstrap-and-template-drift/.tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -k handoff -v`. Policy output: `policy in sync`. Test: 1 failure in 0.409s, combined exit 1, fixture reuse at `test_lifecycle.py:725`: `worktree.py error: board BOARD-001 has required repos without workspace entries`. Handoff assertions not reached; stopped without fixture changes, retries, commits or real merges.

## [2026-11-18] Anchor generated handoff commands to the control repository
**Type:** Fix
**Board:** BOARD-117 | **Branch:** chore/fix-project-bootstrap-and-template-drift (uncommitted)
**Changed:** `worktree.py`, existing `test_lifecycle.py` handoff test, worktree skill examples, handover, state, decisions and this log.
**Why:** Pasting an absolute lifecycle script command from outside the control root sought the wrong board.
**Impact:** Printed merge preview/apply commands use safely quoted `cd <resolved control root> && python3 <script> ...`; discovery and selection arguments remain unchanged. No new tool, commit, policy/config, board or existing-project edits; no real merge.
**Verification:** `TMPDIR=/projects/kilo_inhouz_ai/.kilo/worktrees/fix-project-bootstrap-and-template-drift/.tmp PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -k handoff -v` failed (1 test, exit 1) during fixture creation: `permission initialization failed: inherited permission map disagrees with saved mode`. Handoff assertions were not reached; no workaround or second command attempted.

## [2026-11-18] Complete project bootstrap and align template ignores
**Type:** Fix
**Board:** BOARD-117 | **Branch:** assigned BOARD-117 worktree (uncommitted)
**Changed:** Factory/template READMEs, `.gitignore` files and tracking rules, board/worktree skill guidance, handover, state, decisions and this log.
**Why:** Skeleton-only setup omitted the harness and staging; template QA ignores and tracked-live-board wording contradicted approved local state.
**Impact:** Initial setup copies the existing complete sync slice/config before the first commit while retaining project rules and repo map. Live boards and all evidence stay ignored; the blank template board stays trackable. No tool, policy/config, existing project, index or board changes; no commit.
**Verification:** After approved correction to append `/docs/BOARD.md` only to the bootstrap destination, one invocation passed, exit 0, in `.tmp/board-117.jsHiWB`: `diff -qr` for six slices; `cmp` for copied ignore/config and retained rules/map; eight project ignore checks; tracked template-board/board.py checks; template-board not ignored; factory live board ignored; empty index listings; `git diff --check`. Earlier permission and child-ignore failures resolved. No handoff edits or commits.

## [2026-11-18] Keep board state truthful after partial discard
**Type:** Fix
**Board:** BOARD-116 | **Branch:** chore/synchronize-factory-worktree-lifecycle-and-policy
**Changed:** `worktree.py` and lifecycle regression tests.
**Why:** Clear removed worktree entries even when branch deletion fails.
**Impact:** Partial discards report the leftover branch while marking affected rows `Dropped`.

## [2026-11-18] Keep cleanup previews side-effect free
**Type:** Fix
**Board:** BOARD-116 | **Branch:** chore/synchronize-factory-worktree-lifecycle-and-policy
**Changed:** `worktree.py`, lifecycle regression tests, `README.md`, `docs/HANDOVER.md`, and tracked review reports.
**Why:** Delay recovery TSV creation until an apply operation passes preflight, document generated app-scope pointers, and remove obsolete tracked review reports.
**Impact:** Cleanup dry-runs and refusals no longer write recovery files; discard remains human-only and without backups.

## [2026-11-18] Complete documentation audit correction
**Type:** Docs
**Board:** BOARD-116 | **Branch:** chore/synchronize-factory-worktree-lifecycle-and-policy
**Changed:** `README.md`, `docs/PROJECT_STRUCTURE.md`, `docs/HANDOVER.md`, `docs/UI-UX.md`, historical lifecycle changelog, and this log.
**Why:** Remove stale inventory counts and duplicate sections, make ignored review artifacts authoritative, and label superseded historical discard and teardown claims.
**Impact:** Documentation only; the approved lifecycle contract and application code are unchanged.

## [2026-11-18] Correct active lifecycle documentation paths
**Type:** Docs
**Board:** BOARD-116 | **Branch:** chore/synchronize-factory-worktree-lifecycle-and-policy
**Changed:** Review-path guidance, lifecycle decisions, handover test inventory, and this changelog.
**Why:** Remove stale active references to `docs/reviews/`, clarify superseded ADR claims, and identify the current script-level test modules.
**Impact:** Documentation only; lifecycle behavior is unchanged.

## [2026-11-18] Align env status with recursive provisioning
**Type:** Fix
**Board:** BOARD-116 | **Branch:** chore/synchronize-factory-worktree-lifecycle-and-policy
**Changed:** `worktree.py`, `env.py`, lifecycle tests, handover and architecture docs
**Why:** Status previously reported only two top-level names while provisioning accepted recursive eligible `.env*` files.
**Impact:** Status now reports the same eligible source set without exposing values or changing provisioning exclusions.

## [2026-11-18] Correct lifecycle documentation contradictions
**Type:** Fix
**Board:** BOARD-116 | **Branch:** chore/synchronize-factory-worktree-lifecycle-and-policy
**Changed:** Lifecycle ADRs, handover inventory, skill guidance, historical supersession note, lifecycle self-test cleanup, and factory architecture/risk docs.
**Why:** Align the written lifecycle contract with recursive local-file provisioning, human-only no-backup discard, CLI-owned teardown, and `Merged`/`Dropped` lane transitions.
**Impact:** Current guidance no longer offers raw Git teardown or stale recovery behavior; historical rationale remains preserved and explicitly marked superseded.

## [2026-11-18] Align worktree lifecycle with human discard policy
**Type:** Chore
**Board:** BOARD-116 | **Branch:** chore/synchronize-factory-worktree-lifecycle-and-policy
**Changed:** Lifecycle and env scripts/tests, generated policy/config, and lifecycle guidance.
**Why:** Keep provisioning non-overwriting and recursive, and make permanent discard an explicit human-only action with no recovery copies.
**Impact:** New worktrees receive safe local-file copies; resume and cleanup preserve unprovenanced files. Discard drops the final board row and is denied through Kilo agent permissions.

## [2026-11-17] Close BOARD-114 provisioning and permission cleanup
**Type:** Fix
**Board:** BOARD-114 | **Branch:** feat/provision-local-env-and-secure-qa
**Changed:** `.kilo/policies/git-policy.json`, generated `kilo.jsonc`, factory handover and project state.
**Why:** Complete the approved local QA provisioning/auth work and remove the earlier duplicate review-artifact allow-rule pair while retaining the effective pair after worktree rules.
**Impact:** Review evidence remains writable and later secret and live-board denials remain effective. Policy and generated map are in sync. Lifecycle suite passed 36 tests; pending human merge.

## [2026-11-16] Provision local QA inputs into new worktrees
**Type:** Fix
**Board:** BOARD-114 | **Branch:** feat/provision-local-env-and-secure-qa
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, lifecycle tests, browser-review tests, focused skills, factory handover and project state.
**Why:** New worktrees need approved local environment and navigation inputs while keeping secret values out of agent-readable policy, command output and captured evidence.
**Impact:** New worktrees copy ignored/untracked regular `.env*` files except `.env.example`, preserve permissions, skip existing targets, and copy ignored control `.kilo/local/qa-navigation.json` without overwriting. The existing browser runner continues env-only login and masks known credentials during screenshot capture. No dependencies or policy changes.
**Handoff:** Focused provisioning tests passed 3/3 and Node QA passed 20/20. Full lifecycle suite retains two unchanged permission-order assertion failures at `.kilo/skills/git-worktree/scripts/test_lifecycle.py:732`. An unrelated unstaged user `kilo.jsonc` change is preserved; the merge gate is not clear pending human review/decision.

## [2026-11-16] Resolve review-artifact permission hold
**Type:** Fix
**Board:** BOARD-113 | **Branch:** chore/store-reviews-as-ignored-artifacts
**Changed:** Approved user policy wording/order, regenerated task config, handover and project state.
**Why:** The latest reload enabled normal shared report writes. User explicitly approved moving only the two review allowances back to tested placement while preserving their values/reasons and SSH denial edits.
**Impact:** No weakened source, board or secret protection. No ledger reset, new worktree, artifact staging, agent merge or main-config edit. Earlier hold remains historical, not current status.
**Verification:** Builder focused permission test: 1 passed in 0.065s, exit 0. Independent final delta: 1 passed in 0.053s, exit 0; maps in sync, no blocking findings. Normal `apply_patch` report creation and update both succeeded at shared ignored `artifacts/reviews/BOARD-113-review.md`. Earlier independent 6-test ledger and byte-preserving migration evidence is unchanged.

## [2026-11-16] Permit shared review evidence writes
**Type:** Fix
**Board:** BOARD-113 | **Branch:** chore/store-reviews-as-ignored-artifacts
**Changed:** Canonical git policy, generated task `kilo.jsonc`, existing `test_lifecycle.py` permission tests, ADR-071 and handover note.
**Why:** Approved narrow exception for relative/absolute `artifacts/reviews/` evidence writes; reuse existing generator and pattern matcher, no new tools or dependencies.
**Impact:** Required-mode main source remains denied; optional assigned-checkout behavior unchanged. Later secret/live-board protections still win. Added approved `**/id_rsa*` deny beside existing `id_rsa*` to preserve SSH-key protection at nested paths. Main config, guard/lifecycle source, artifacts and existing staging untouched. Active reviewer sessions require reload.
**Verification:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -k review_artifact -v` second/final attempt: 1 test passed in 0.063s, exit 0, both modes and generated maps in sync. First attempt failed four nested SSH-key subtests; the approved nested denial resolves them without weakening the test. Only task config regenerated through existing `guard.py check-policy --write`; no real mode changes, artifact writes, staging or commits.
**Independent review:** No blocking findings; the same focused regression passed 1 test in 0.070s, exit 0. After the user confirmed task-config reload, one authorized reviewer `apply_patch` retry still failed with project `edit` pattern `*`, action `deny`. No alternate write was attempted. BOARD-113 remains Blocked pending effective runtime permission; preserve a clean local checkpoint, not a merge-ready claim.

## [2026-11-16] Store reviews as ignored shared artifacts
**Type:** Chore
**Board:** BOARD-113 | **Branch:** chore/store-reviews-as-ignored-artifacts
**Changed:** `ledger.py`, new adjacent `test_ledger.py`, root/template rules, QA/UI agents, run/ui commands, web/mobile scopes, QA skill, template UI/structure docs, `.gitignore` comment, governance and this log. Removed four tracked `docs/reviews/` originals after preservation.
**Why:** Approved ADR-069/070: evidence is local and shared across worktrees; unresolved round-three blockers need a contextual human decision, not an automatic extension. The existing ledger/control-root implementation is extended, not duplicated. A new stdlib test file is needed because no ledger suite existed.
**Impact:** Default ledger directory is control main-checkout `artifacts/reviews/`; explicit absolute/relative `--ledger-dir` overrides remain. Read/root failures refuse clearly. The cap stays three, with no writes on fourth-round refusal and no inference of blockers on success. No artifacts may be staged/committed; dated screenshots unchanged. No lifecycle/auth/policy/config changes or new dependencies.
**Migration:** `docs/reviews/BOARD-102-ledger.md`, `BOARD-102-qa.md`, `BOARD-103-ledger.md`, `BOARD-103-review.md` each copied to `/projects/kilo_inhouz_ai/artifacts/reviews/<same-name>`. Existing main and feature versions were byte-identical; `cp -n -p` plus `cmp` preserved bytes without overwrites. Main originals untouched; feature deletions retain Git history. Historical internal references are intentionally unchanged; old report basenames resolve in the new directory. BOARD-103 remains capped with its original stop reason.
**Verification:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/qa-review/scripts -p test_ledger.py -v`, builder 6 tests in 0.129s; independent reviewer 6 tests in 0.107s; both exit 0. Reviewer confirmed ignored/untracked artifacts and all four migrated files against main originals and Git blobs, byte-for-byte. Nested separate-app discovery was source-reviewed, not fixture-tested.
**Checkpoint:** Intended source/docs staged, including explicit new-test inclusion despite shared `.git/info/exclude` rule `.kilo/`. No ignored artifacts staged. Local checkpoint commit is authorized; runtime report-write hold prevents Pending Merge. Permission correction is recorded above.

## [2026-11-16] Align board template after permission reload
**Type:** Docs
**Board:** BOARD-103 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `templates/project/docs/BOARD.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/reviews/BOARD-103-review.md`, this log.
**Why:** The latest authorized retry succeeded after human permission changes and reload. Remove stale mandatory per-row worktree/manual merge instructions from the project template.
**Impact:** Template uses the approved shared workspace, optional mode, clean human merge/cleanup and explicit discard rules. Source code and existing 33 lifecycle/19 auth test proof are unchanged. No actual merge, discard or mode change. User approved restoring temporary live-board permission edits; both policies and the feature config were restored. Main generated-config restoration was tool-denied and remains human cleanup.
**Evidence:** Template file review against approved rules; final documentation whitespace check and clean local commit required for handoff. Parent ledger remains capped and unchanged.

## [2026-11-16] Preserve verified fix after confirmed-reload template denial
**Type:** Docs
**Board:** BOARD-103, BOARD-107 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/reviews/BOARD-103-review.md`, this log; live board evidence recorded separately.
**Why:** Code checkpoint `f0b9c95` resolves the ordered-map defect with 33 independently passing tests. The user confirmed a task-worktree reload, but one authorized template retry still hit project `**/docs/BOARD.md: deny`.
**Impact:** Template unchanged; parent remains Blocked pending effective edit permission. No bypass, repeated retry, actual merge, discard or mode change. Preserve the verified fix and clean checkpoints.

## [2026-11-16] Independently verify ordered-map follow-up
**Type:** Docs
**Board:** BOARD-107, BOARD-103 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/reviews/BOARD-103-review.md`, this log; live board evidence recorded separately.
**Why:** Distinguish the authorized focused follow-up from the capped parent rounds and supersede earlier zero-test discovery with real independent proof.
**Impact:** Rule-order defect resolved; template edit remains blocked until Kilo loads the task-worktree permission exception. No merge, discard or mode change; parent ledger preserved.
**Evidence:** Independent absolute-path lifecycle discovery ran 33 tests in 14.190s, `OK`, exit 0. Independent current-source review found no blocking issue; orchestrator inspected the baseline diff. Auth source is unchanged from its independent 19-test pass.

## [2026-11-16] Validate inherited permission rule order through existing guard logic
**Type:** Fix
**Board:** BOARD-107 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `.kilo/skills/git-worktree/scripts/{guard,worktree,test_lifecycle}.py`, `docs/HANDOVER.md`, this log.
**Why:** Dictionary equality ignored nested rule order. Extract the existing guard ordered-items comparison into pure `permission_maps_match(current, expected)` and reuse it in `cmd_check_policy()` and `cmd_create()`; the existing generator remains the only rule source.
**Impact:** Reordered inherited maps fail closed without rewriting inherited/base config. Partial checkout/branch and journal error survive with unchanged board. Correctly ordered inherited maps still succeed. This is a newly user-authorized small follow-up, not a fourth parent review round; capped ledger and board statuses remain untouched. No real mode/map/lifecycle actions, commits, template/rules/policy/config edits, dependencies or new tooling.
**Verification:** One run in `/projects/kilo_inhouz_ai/.kilo/worktrees/configurable-shared-workspace-lifecycle-and-authenticated`: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -v`. Discovered and passed **33 tests** (31 existing plus 2 new methods) in 14.361s, exit **0**; discovery count is nonzero. New methods cover six reordered nested edit/bash/read cases and two ordered-map success cases across optional/required mode transitions, using inherited apps without local config. All mutations used disposable standard-temp repositories; existing injected cleanup/unfinished-merge failures were expected passing cases. No broader verification or parent-review pass claimed.

## [2026-11-16] Stop at final permission-order review gate
**Type:** Docs
**Board:** BOARD-103, BOARD-107 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/reviews/BOARD-103-{review,ledger}.md`, this log. Live board status updated separately by the orchestrator.
**Why:** Final source review found inherited permission dictionary equality ignores rule order and may accept a secret-weakening wildcard. The repeated mode-map finding reached the three-round cap.
**Impact:** Blocked, not merge-ready or safe to enable. Preserve checkpoint work for a human follow-up decision; template BOARD also needs session permission reload. No fourth round or actual merge, discard or mode change.
**Evidence:** `worktree.py:640-643`; existing ordered-items check `guard.py:775-778`. Builder lifecycle suite passed 31; final independent discovery ran zero tests and provides no independent pass. Auth was independently verified at 19 tests. Final report and ledger record the hold.

## [2026-11-16] Final shell-routing and new-checkout permission corrections
**Type:** Fix
**Board:** BOARD-104, BOARD-107 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `.kilo/skills/git-worktree/scripts/{guard,worktree,test_lifecycle}.py`, `docs/HANDOVER.md`, this log.
**Why:** Extend `git_commands()` to reject unsupported directory-changing chains instead of interpreting shell state. Extract the existing validated guard-policy loader as effectful `load_guard_policy(root)` so `cmd_create()` and `cmd_mode()` use the same policy/generator, not a duplicate permission implementation.
**Impact:** New checkout local maps reflect saved project mode in either direction; inherited maps are checked without changing base/canonical configs. Apps keep inheritance and scope pointers without harness copies. Invalid initialization preserves branch/worktree and records incomplete creation without changing board rows. No real lifecycle/mode, policy/config edits, commits, board/product/dependency changes in this correction. Ready for fresh round-three review, not merge.
**Verification:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -v`: 31 tests passed in 12.054s, exit 0, one suite run. Six added regressions cover directory chains, both mode/base directions, mapped-app inheritance/pointers/local maps, base preservation and invalid-map partial creation. All mutations used disposable standard-temp repositories; printed injected cleanup/unfinished-merge failures were expected.

## [2026-11-16] Authenticated capture proof and workflow closeout
**Type:** Fix
**Board:** BOARD-103, BOARD-110 through BOARD-112 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** canonical browser capture/test, QA skill, agent/root/template rules, environment/stack/structure/state/handover docs, ADR-068, review report/ledger, policy and generated config, `.gitignore`.
**Why:** Reuse the existing capture path with explicit final URL and authenticated-ready assertions; no new client, dependency or login service. The new adjacent test file covers parser/privacy behavior and real canonical capture against an isolated HTTP fixture.
**Impact:** Authenticated password-settings pages work; same-URL gates no longer qualify as access proof. Template uses ignored generated pointers. Template BOARD edits get a narrow ask exception while live boards remain denied; this session still needs a reload before that correction. No board writer or board was untracked. No real workspace merge/discard or actual mode change ran.
**Verification:** Browser suite passed 19 tests, including real login/protected-navigation/shared-session PNG capture at two viewports; lifecycle suite passed 25 disposable-repo tests. External SSO/MFA and real accounts were not exercised. Corrected-state review and the template permission hold remain tracked on the live board.

## [2026-11-16] Correct lifecycle safety review findings
**Type:** Fix
**Board:** BOARD-104 through BOARD-109 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `.kilo/skills/git-worktree/scripts/{worktree,guard,test_lifecycle}.py`, `docs/HANDOVER.md`, this log.
**Why:** Extend existing argument parsing, lifecycle journal, board association, verification and permission generator; add no parallel tool or dependency. The new effectful `require_committed_merge()` centralizes checks needed both before workspace cleanup and before source-branch deletion.
**Impact:** Resolve attached/repeated Git directory options before protected-branch checks. Prove committed named-target ancestry and clean merge state before cleanup; resume exact human-completed recorded conflicts, refusing unrelated changes. Regenerate all effective project maps from control policy with preflight/rollback. Preserve terminal board history on slug reuse. Verify against the saved base unless explicitly overridden. No actual mode/maps, live board, product, real branch/workspace or unrelated files changed by this correction; no commits.
**Verification:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -v`: 25 tests passed in 9.981s, exit 0, one suite run. All mutations used disposable standard-temp repositories. Injected cleanup and uncommitted-merge failures were expected passing cases.

## [2026-11-16] Shared-workspace rules and authenticated review guidance
**Type:** Docs
**Board:** BOARD-103 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** root/template `AGENTS.md`; `.kilo/agent/*.md`, `.kilo/scopes/*.md`, affected commands and skill markdown; factory structure, handover, state, stack, environment and decisions; project-template architecture, risks, QA, environment, stack and structure examples. Template BOARD edit was denied by session policy and remains a reported contradiction.
**Why:** Replace contradictory per-row worktrees/fixed folder bans/raw merge guidance with approved lifecycle and assigned-scope rules. Reuse existing docs/tools. New `merge-conflict-resolver.md` is required because no existing specialist resolves preexisting conflicts without completing merges.
**Impact:** Required/optional mode, shared findings workspaces, human CLI merge/discard, authenticated navigation and conflict handoff documented. No mechanics edits, live board actions, product edits, commits, merges or discards in this chunk. Historical ADRs/log entries preserved.
**Verification:** Static file review only at this point; no build or runtime verification claimed. Mechanics limitations are recorded in HANDOVER.

## [2026-11-16] Configurable shared-workspace lifecycle mechanics
**Type:** Feature
**Board:** BOARD-103 | **Branch:** feat/configurable-shared-workspace-lifecycle-and-authenticated
**Changed:** `.kilo/skills/git-worktree/scripts/{worktree,guard,test_lifecycle}.py`, `.kilo/policies/git-policy.json`, generated `kilo.jsonc`, `docs/HANDOVER.md`, this log.
**Why:** Extend the existing lifecycle, guard generator and board parser instead of adding another workspace tool. The new test module isolates regression fixtures in Python's default temporary directory; no existing test module covered lifecycle mechanics.
**Impact:** Required mode remains the default; optional mode changes the edit fallback and outside-worktree commit check without relaxing secret/protected-file rules or protected-branch commits. Shared rows reuse workspaces. Human CLI merge/discard is preview-first, confined, fail-closed and records partial progress. Board-only control dirt is allowed; unrelated tracked/untracked dirt is refused. Kilo restart required after generated permission changes. No live board edits, real merges/discards, commits, installs, untracking, or rules/agent markdown changes in this chunk.
**Verification:** Permission-map regeneration completed. The initial combined unittest attempt could not create fixtures under `/tmp/kilo`. After explicit approval to use Python's default temporary directory, the same command (`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -v`) passed all 17 tests in 5.475s, exit 0. No permission changes or additional retry were needed. The lifecycle module docstring now describes explicit discard and the local progress journal rather than obsolete never-delete/TSV claims.
## [2026-11-11] The /plan and /unslop commands
**Type:** Chore
**Board:** BOARD-113 | **Branch:** chore/add-plan-and-unslop-commands
**Changed:** `.kilo/command/plan.md`, `.kilo/command/unslop.md`, `docs/UI-UX.md` §2.1, `docs/changelog/CHANGELOG.md`
**Why:** The plan and unslop skills sit in `.kilo/skills/`, but the skill loader does not expose them, so neither was discoverable as a command. Both procedures were already the rules; they were only reachable by asking.
**Impact:** `/plan` packages the plan skill's phases into a product-planning shortcut that points at the decision gate; `/unslop` packages the unslop procedure — direction, sign audit, nine passes, checklist — and writes the audit to `artifacts/reviews/<task-id>-unslop.md`. Neither command adds a rule: both name the by-path read and defer to `AGENTS.md`. The command directory is part of the harness slice, so a project copy carries both.
**Historical note:** The former `docs/reviews/` output path is superseded by ignored `artifacts/reviews/`.

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
**Impact:** **Superseded historical entry.** The former manual Git teardown pair is obsolete. Current discard is human-only, requires `--apply --discard`, creates no backup, and marks the final linked row `Dropped`.

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
**Impact:** **Superseded historical entry.** The former force/recovery flow is obsolete. Current discard is human-only, requires `--apply --discard`, creates no backup, and marks the final linked row `Dropped`.

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
**Impact:** All UI evidence lands under `artifacts/<scope>/qa/<date>/<task-id>/` in the main checkout; the capture script computes the path itself and writes ignored local artifacts. Review reports and ledgers use ignored `artifacts/reviews/`; the former `docs/reviews/` path is superseded. A new rule makes an agent check for existing tooling and ask before building any.

## [2026-10-29] Live board viewer, bounded UI loop, gated UI tooling
**Type:** Feature
**Board:** BOARD-008, BOARD-009 | **Branch:** feat/live-board-viewer-html-dashboard-with
**Changed:** `.kilo/skills/board/scripts/board_serve.py` (new), `.kilo/skills/qa-review/scripts/{browser-review.mjs,check-finding.py,ledger.py}`, `.kilo/skills/board/scripts/board.py`, `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/{board,qa-review}/SKILL.md`, `.kilo/command/{board-view,run,ui}.md`, `.kilo/agent/{qa-reviewer,ui-critic}.md`, `kilo.jsonc` (Playwright MCP), `.devcontainer/devcontainer.json` (port 15180), `AGENTS.md`, `docs/{STACK,DECISIONS}.md`
**Why:** The markdown board is hard to scan, the UI critique → fix loop could run forever, and Playwright was installed but unreachable — so the agent built a browser driver by hand and looped proving it worked.
**Impact:** A read-only dashboard on port 15180 shows the lanes and the live worktrees. The QA loop is capped at 3 rounds with fingerprint dedupe and a ledger. The Playwright MCP is configured and the capture script resolves the global Playwright, so no hand-rolled browser client remains.
