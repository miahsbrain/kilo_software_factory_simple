# HANDOVER — software factory

> **Session Notes — BOARD-126 server/API slice, 2026-11-12**
> In `feat/expose-registered-repos-and-safe-candidates`, the dashboard reads board and worktree
> state for registered IDs only, and exposes metadata-only candidate names via
> `GET /api/repo-candidates`. Candidate scans are rooted at `/projects` and never authorize
> repository contents. The test suite failed twice on legacy unregistered-project expectations;
> final corrections were not rerun. Next: parent independent verification/review, then client work.

## BOARD-126 server inventory

- `board_serve.py:registered_repos` (effectful map read) resolves every ID through the existing
  worktree helpers. `discover_boards`, `board_available`, `read_rows`, `worktree_state`
  (effectful filesystem, SQLite or Git) read registered repositories without creating their boards.
- `board_serve.py:select_candidates` (pure) excludes registered relative paths and sorts distinct
  candidates. `scan_repo_candidates` (effectful directory metadata) checks only directories and
  `.git` marker types two levels beneath the injected root, never following symlinks.
- `Handler.do_GET`, `build_payloads` (effectful HTTP and request-time reads) expose the new
  read-only endpoint. Candidate errors return 503 with no path/exception; see
  [API_CONTRACTS.md](API_CONTRACTS.md). No new dependency, persistence or environment variable.
- Verification: documented temporary-fixture board suite ran twice and failed on legacy
  unregistered-project expectations (first 1 failure, second 3 failures). Final corrections
  require parent verification; independent QA/review and client integration remain separate.

> **Session Notes — BOARD-125 independent-review correction, 2026-11-12**
> The same `fix/repair-finalize-after-worktree-removal` worktree now publishes a
> verified, fsynced recovery temp file without replacing an existing journal. A
> failed write/link leaves no final record or merge; retry can proceed. After human
> confirmation, a SQLite `BEGIN IMMEDIATE` writer lock covers fresh Pending Merge
> validation, Git integration/cleanup and the final SQLite row update. Failed
> operations roll back the board transaction but retain a published recovery record
> for safe replay. Other writers may wait or time out (board busy timeout: 10s).
> Next: parent independent review; no agent-run finalize or merge.

## BOARD-125 corrective inventory

- `worktree.py:publish_finalize_journal` (effectful filesystem) verifies and fsyncs
  a private temp file, atomically links it without replacing existing recovery,
  syncs the directory, and removes only its own incomplete temp on failure.
- `worktree.py:finish_finalize_locked` (effectful Git/filesystem/SQLite) runs
  recovery publication, merge, cleanup and row update under the SQLite writer
  transaction. `cmd_finalize` (effectful) rechecks the approved row under that
  transaction after terminal confirmation, commits only a successful row update,
  and rolls back failure. `clear_row_worktree` (effectful) updates the passed
  connection rather than opening a nested writer; unrelated rows are preserved.

> **Session Notes — BOARD-125 finalize teardown repair, 2026-11-12**
> In `fix/repair-finalize-after-worktree-removal`, the human-only finalize command now
> displays board, base, branch and full tip before requiring an exact `yes` on TTY stdin.
> It rechecks Git and the SQLite row after confirmation. The loaded board adapter retains
> control-repo discovery when the running script is removed with its task worktree. A
> validated, fsynced Git-common-dir recovery record precedes merge/teardown; retry after
> removal clears the row without re-merging. Other repos remain Pending Merge.
> Focused scratch-repository suite passed 32 tests; independent review passed. Next: human
> inspection and finalize from the `opencode` checkout. Agents do not merge or finalize.

## BOARD-125 lifecycle inventory

- `worktree.py:load_board_module` (effectful import) binds its existing `control_root`
  to the loaded board module so the same process can update SQLite after self-removal.
- `worktree.py:cmd_finalize` (effectful Git, filesystem, SQLite) validates the recorded
  path/branch/base/tip and commit before replay, persists and syncs the recovery record
  before integration, and re-reads Pending Merge and worktree ownership after confirmation.
  `clear_row_worktree` (effectful SQLite through the board adapter) keeps other repo entries.
- `worktree.py:confirm_finalize` (effectful terminal) shows the target, accepts only
  `yes` followed by a newline, and refuses non-TTY, EOF, mismatch and stream errors.
  Confirmation is a local deterrence, not an OS security boundary.
- Verification: focused scratch-repository handoff tests from `docs/STACK.md`; parent
  reviews result before changing the board lane.

> **Session Notes — BOARD-124 terminal confirmation correction, 2026-11-12**
> In `feat/sqlite-board-bootstrap`, `confirm_finalize` uses TTY stdin and stderr rather than
> opening `/dev/tty`, which raised `io.UnsupportedOperation` on the human's interactive host.
> The exact board/base/branch/full-tip challenge and post-confirmation base recheck remain;
> non-TTY, EOF, mismatch and stream failures refuse. Focused handoff suite: 24 tests, OK.
> Next: independent parent QA/review;
> agents do not run human finalize or merge.

> **Session Notes — BOARD-124 independent QA corrections, 2026-11-12**
> Existing `feat/sqlite-board-bootstrap` worktree now supplies a pre-merge legacy import/byte
> backup check, shell-quoted absolute control-script handoff for app repos, and strict ledger IDs.
> Focused board 24, handoff 24, ledger 2 tests pass; parent review remains open.
> Next: parent independent QA/review in this same worktree; no merge or finalize by agents.

> **Session Notes — SQLite migration corrective slice, 2026-11-12**
> Worktree `feat/sqlite-board-bootstrap` keeps the live board in Git-common-dir SQLite.
> Factory `docs/BOARD.md` is untracked on this task branch; its on-disk bytes and preexisting
> SQLite import snapshot remain. A fresh clone after integration starts empty, never from
> historical tracked rows. Human-only finalize requires a real TTY and typed board ID, base,
> branch and full tip; merge preflight reports conflict paths/types, and a failed initiated merge
> is aborted if safe. QA/UI findings now return to the original builder in the same worktree;
> reviewer reports and ledger belong under `<git-common-dir>/reviews/`. Next: independent parent
> review and QA; this task is not merge-ready merely because it is committed.

## Transition and recovery

- Existing local board: `board.py show` imports main-checkout legacy bytes once into the local
  SQLite `source_bytes` snapshot without changing the Markdown. `board.py export` writes the
  current readable snapshot under Git common dir. Use a consistent SQLite backup (or export)
  when transferring a clone; Git does not synchronize live rows or reviewer reports.
- On integration of this branch, tracked `docs/BOARD.md` is deleted from the integration checkout;
  a previously initialized SQLite database retains the live rows. **Before the one-time human
  integration**, stop board writers and run from this bootstrap worktree:
  `python3 .opencode/skills/board/scripts/board.py pre-merge-check`, then
  `python3 .opencode/skills/board/scripts/board.py export`. The check imports a missing database
  from the main-checkout source, verifies its `source_bytes` match, refuses a missing/changed
  source, and writes/prints the SQLite, byte-exact legacy backup and current Markdown export
  paths in Git common dir. The second command refreshes the export. Do not proceed if either
  fails. Review the handoff, then run the absolute `finalize` command printed by
  `worktree.py handoff --board BOARD-124` from the clean `opencode` base checkout in a real TTY;
  it uses this bootstrap worktree's script, not the base's old relative script. After integration,
  a new clone with no local board initializes empty. The still-tracked blank project template is
  not historical state.
- `board.py:cmd_pre_merge_check` (effectful filesystem/SQLite), `write_export` (effectful atomic
  bytes/text snapshot) preserve the import and byte backup; `worktree.py:cmd_handoff` (effectful)
  prints the absolute shell-quoted control script and target main checkout for app/control repos.
  `ledger.py:main` (effectful CLI) validates `BOARD-[0-9]+` before Git or ledger I/O.
- `worktree.py:cmd_finalize` (effectful Git/SQLite) performs clean preflight, typed terminal
  confirmation and resumable integration. `confirm_finalize` (effectful TTY stdin/stderr) cannot
  establish identity against a process sharing the same OS user. Failed merge abort is scoped
  to `MERGE_HEAD` created during this call and unchanged pre-merge HEAD; otherwise inspect
  manually. `ledger.py:main` (effectful Git discovery) defaults to common-dir local reviews;
  `parse_ledger`/`render_ledger` (pure) retain historical Fix-row fields for old records.
- Verification: `python3 -m unittest discover -s .opencode/skills/git-worktree/scripts -p 'test_*.py'`;
  parent independently reviews evidence before marking Pending Merge.
- Focused terminal-confirmation correction: `python3 -m unittest discover -s
  .opencode/skills/git-worktree/scripts -p 'test_handoff.py'` passed 24 tests in 12.083s.

> **Session Notes — BOARD-124 lifecycle slice, 2026-11-12**
> `feat/sqlite-board-bootstrap` now makes create/resume refuse env errors; failed create records
> a Blocked partial worktree rather than losing its ownership. Human-only `finalize --board ID`
> checks Pending Merge, clean correct branch and base, committed work and conflict preflight;
> merges only from the configured base main checkout, retains a recovery record and retries
> interrupted teardown. Handoff offers only that command after its readiness gate. Next: parent
> independently reviews tests and governance before offering the task branch for human merge.

## Lifecycle slice inventory

- `env.py:inside_worktrees` (effectful filesystem), `write_file` (effectful atomic 0600 write),
  `sync_into` (effectful source validation, Git tracked-file check, exclude, provision) reject
  symlinks and tracked destinations. Only `.env` and `.env.local` from the main checkout copy.
- `worktree.py:provision_env`, `cmd_create`, `cmd_resume` (effectful) fail closed on env errors;
  `cmd_finalize` (effectful) is a human-only CLI entry point. Pending Merge is a human/reviewer
  certification: QA and verification evidence is not machine-readable; finalize prints this
  limitation and must never be called by an agent. Recovery journal is stored in the Git common
  directory's `cleanup-wt/` before merge, with branch tip and base identity; no secret contents.
- Conflict preflight reports paths and competing edits; resolve in the original task worktree.
  No merge or cleanup on preflight conflict. After a successful integration, ancestry is checked;
  cleanup removes env copies, worktree and branch, then updates SQLite board. Interrupted cleanup
  reruns from the journal. Multi-repo rows remain Pending Merge while another entry is recorded.
- Tests: `python3 -m unittest discover -s .opencode/skills/git-worktree/scripts -p 'test_*.py'`.
  First run: 19 tests, 2 failures from stale Markdown fixture mutations; changed them to
  update scratch SQLite. Second run: 19 tests, OK (9.198s). A final source-only tightening
  withholds finalize guidance for a row already marked Merged and avoids marking a multi-repo
  row Merged during legacy cleanup; these last edits were not rerun within the two-attempt cap.

> **Session Notes — SQLite board core slice, 2026-11-12**
> Worktree `feat/sqlite-board-bootstrap` implements the first data slice only. The live board is
> `<git-common-dir>/factory-board.sqlite3`; first initialization imports existing main-checkout
> `docs/BOARD.md` once and retains source bytes in the database without writing that file.
> `board.py export` writes `<git-common-dir>/factory-board-export.md` on demand. `--file` is a
> read-only Markdown fixture; board viewer default reads SQLite. `worktree.py` remains unchanged
> and uses the compatible `read_table`/`write_atomic` API. Conflicting cell edits refuse rather
> than overwrite; distinct rows/cells merge under `BEGIN IMMEDIATE`. The old tracked Markdown
> remains in this branch to avoid removing a possibly newer integration-checkout board on merge.
> Later slices must reconcile legacy tracking, lifecycle governance and human-only finalization.

## SQLite board core inventory

- `board.py:initialize_board`, `database_path`, `connect`, `live_database`, `read_table`,
  `write_atomic`, `write_export` are **effectful**: Git discovery, SQLite read/write or local
  export. `parse_table`, `merge_board_changes`, `cell_texts`, `replace_cell` are **pure**.
- Schema: one `board` row (`id=1`, Markdown snapshot, original import bytes, revision); no
  runtime files in the checkout. WAL and busy timeout serialize concurrent writers. First
  import validates the old table; malformed UTF-8/table fails closed without changing source.
- CLI `show`/`lanes` read current SQLite state; `add`, `note`, `set-status`, `set-field`,
  `add-column`, `remove` update SQLite; `export` writes a readable Markdown snapshot in the
  common Git directory. The viewer discovers per-clone control/project databases and reads
  live rows via `read_table`. Existing template starter is unchanged.
- In this transition the documented worktree lifecycle still uses its original calls and
  independently retains its old governance wording. No application data model or env vars.
- Verification: `python3 -m unittest discover -s .opencode/skills/board/scripts -p 'test_board*.py'`.
  This slice does not run the full lifecycle suite; parent must review before any merge.

> **Session Notes — BOARD-123 handoff gates, 2026-11-11**
> Branch `fix/gate-merge-handoffs-on-finished-clean-worktrees`, worktree of the same slug.
> Extended `cmd_handoff` and approved factory/template §B11 policy; derived commands/skill align.
> Initial focused run failed on Status lookup; corrected to existing `STATUS_INDEX`.
> Architect-authorized second run passed: 13 tests in 3.847s, exit 0. Independent QA/review PASS:
> `docs/reviews/BOARD-123-qa.md`, committed with ledger in `27c2e94`. Parent reports the live row
> `Pending Merge`; awaiting human merge. Parent owns the final live handoff check. Existing project untouched.
> Earlier staging exited 1 on ignored `.opencode`; architect authorized exact new-test force-add
> and narrow tracked-path staging. No broad force-add, installs, browser or build work.

## BOARD-123 handoff contract

- Effectful `cmd_handoff` (`.opencode/skills/git-worktree/scripts/worktree.py:971`) reuses the
  board parser, live-row resolver, `STATUS_INDEX`, repo/base and Git helpers. It checks live branch
  identity, staged/unstaged/untracked status, commit count and ancestry; failed/missing Git data
  refuses guidance. No second readiness framework or change to `cmd_verify`.
- Exit 1 / `REFUSED`: review/diff/log plus specific blockers, no merge or teardown. Exit 0 / `OK`:
  clean `Pending Merge` with commits ahead gets diff/log before human merge/cleanup guidance.
  Clean already-merged work retains show/cleanup without a merge command; other gates still apply.
- `Pending Merge` represents the orchestrator's passed verification/review gates; the CLI does
  not run verification or certify review itself. Manual merge commands are gated by §B11 too.
- New adjacent `test_handoff.py` reuses effectful `test_env.make_repo/run/git/write` scratch
  fixtures, isolates temporary repositories inside this task tree, and mocks only Git failures.
  Existing lifecycle `handoff()` assertions now create a task commit and set scratch Pending Merge
  before expecting merge guidance. Full lifecycle suite not run; focused command in STACK.
- Architect-authorized second focused run passed: 13 tests in 3.847s, exit 0. Dirty states,
  all nonready statuses, missing info/Git failures, commits ahead, read-only behavior and already-
  merged paths covered. Initial run failed nine status assertions; correction reused `STATUS_INDEX`.
  Independent QA/review PASS is recorded in `docs/reviews/BOARD-123-qa.md`; parent reports
  `Pending Merge`, awaiting human merge and final live handoff check. No tests rerun for this
  docs-only status update; no browser, build, installs or real board edits.

> **Session Notes — BOARD-122 builder verification complete, 2026-11-11**
> Branch `feat/keep-live-board-local-and-untracked`, worktree of the same slug. Shared bootstrap
> and marker-based control-root lookup implemented; approved root/template rules and derived
> guidance updated. First rules/docs patch was guard-refused; one authorized narrower retry
> excluding every BOARD.md target passed. Authorized corrections changed only two test fixtures:
> assert the existing missing-board error payload and recreate scratch docs before restoration.
> Second verification attempt passed: 24 tests in 0.222s, exit 0. Production behavior unchanged.
> Guard check-git returned 3 (needs approval); existing explicit authorization covered the exact
> `git rm --cached -- docs/BOARD.md`, performed only in this task worktree. Disk bytes retained:
> SHA-256 before/after `c2c5da6f78fc5e8ba6c2ad4cb16f150235dee4ee03937cd0d8bb2fdc22cee91e`.
> Index shows `D docs/BOARD.md`; runtime path is ignored, template starter still tracked/unchanged.
> No main-board/backup access, merge or separate-project edits. Next: parent review; not a merge claim.

## BOARD-122 bootstrap and migration contract

- Pure `empty_board()` in `.opencode/skills/board/scripts/board.py` derives the blank table from
  existing `COLUMNS`. Effectful `initialize_board(root)` publishes a fully written temporary
  file by exclusive hard link, preserving existing bytes and refusing symlink docs/board paths.
- CLI `main()` and viewer `main()` initialize only the missing default board at startup.
  `read_table()` and request payload callbacks remain read-only; explicit `--file` is untouched.
- `board.control_root()` reuses `worktree.control_root()`, which finds the nearest repo-map
  marker without requiring a board, then resolves Git's main checkout. Nested projects retain
  their own ownership. No board copy belongs in future task worktrees.
- Regression additions live in existing `test_board_serve.py`; no new tool or dependency.
  Verification: `python3 -m unittest discover -s .opencode/skills/board/scripts -p 'test_board*.py'`
  second attempt exited 0, 24 tests in 0.222s. Existing/malformed byte preservation, exclusive
  concurrent publication, symlink refusal, canonical linked/main/nested ownership, startup-only
  writes and scratch Git backup/merge/restore all pass. Prior attempt failed only the two
  corrected fixtures. No new abstraction or production behavior was introduced by the correction.

### Human migration, only after review and passing verification

The task branch removes only the board's index entry, retaining the on-disk task copy. Before
the eventual human merge, stop board
writers/tools and refresh the backup to include the latest row updates. The earlier BOARD-122
backup is not a substitute for this final refresh. Run in the control main checkout:

```bash
mkdir -p .git/board-backups
cp docs/BOARD.md .git/board-backups/BOARD-122-before-local-migration.md
cmp docs/BOARD.md .git/board-backups/BOARD-122-before-local-migration.md
```

Do not proceed unless the comparison passes. Git may refuse to delete a locally modified
tracked board during merge. After verifying the refreshed backup, the human must resolve that
tracked-file state without losing the backup. The merge removes the old tracked board. Before
starting any board tooling, restore local state (including its directory if Git removed it):

```bash
mkdir -p docs
cp .git/board-backups/BOARD-122-before-local-migration.md docs/BOARD.md
cmp .git/board-backups/BOARD-122-before-local-migration.md docs/BOARD.md
```

Otherwise startup could initialize a blank board. The restored runtime board is ignored;
cleanup's final row update needs no commit. The template starter remains tracked and unchanged;
future copied projects ignore their own runtime board. Existing separate project repos are
outside this migration. History is not rewritten. Reversal needs an explicit tracking decision;
preserve the local backup throughout.

> **Session Notes — BOARD-121 parent preview screenshot hold, 2026-11-11**
> Parent inspected implementation `fd89d5b` and started main preview http://127.0.0.1:15183/.
> Parent snapshot/DOM: Project selected, 14 tasks/result 14 of 14/three project worktrees;
> Harness hidden, 21 tasks/eight control worktrees. At 1000×700 CSS, no horizontal overflow;
> 60s refresh, 17px/600 section heading, no fixture notice. These are parent observations,
> not independent QA. Evidence and project branch names: `docs/reviews/BOARD-121-qa.md`.
> After tabs.focus, screenshot returned browser.operation_failed: “Screenshot needs a visible tab.
> Call browser.tabs.focus and keep its desktop window visible.” No retry/fallback or screenshot.
> Next: keep desktop window visible so parent can resume built-in screenshot/QA/critique.
> Independent visual/unslop, keyboard and full responsive checks remain held; not merge-ready.
> Existing 15-test/0.048s pass preserved. This checkpoint changes docs only: no source, browser,
> tests/builds, rules/board or artifacts workaround. Live 15180 unchanged.

> **Earlier Session Notes — BOARD-121 main workbench implementation, 2026-11-11**
> User approved the latest hierarchy gallery: “fantastic, now build main dashboard”. Assigned
> branch `feat/apply-approved-workbench-to-main-dashboard`, worktree of the same slug, based on
> approved gallery `da864ef`. Main `/` now composes the same workbench tabs, toolbar, scoped board,
> meter, cards and rail with real data; gallery fixtures remain isolated at `/gallery`.
> Pure `build_html` (`board_serve.py:1209`) replaces the old sidebar/KPI shell; extended pure
> `wb_scope_content` scopes explicit `board` labels by the longest containing main repository path
> (control root fallback supplied explicitly), not by assuming an unknown label means project.
> New pure `wb_workbench_header` extracts the gallery header for actual reuse by both pages,
> with real generated timestamp/freshness on `/` and an honest labelled preview on `/gallery`.
> Existing JS/filter/fold/storage/keyboard/refresh logic and effectful payload boundaries retained;
> `html_page` supplies root as an explicit presentation input. No endpoint/JSON changes.
> Single documented regression run exited 0: 15 tests in 0.048s. Temporary fixture trees/mocked Git,
> no live server. CSS source/generated asset unchanged, no installs/builds or new files.
> Source unslop passes preserve approved hierarchy/tokens; rendered QA/unslop not claimed.
> Parent has since started preview 15183; current screenshot hold is recorded above.
> Live 15180 untouched. Not merge-ready. No board, rule, dependency or real project edits.

> **Session Notes — BOARD-118 hierarchy correction, 2026-11-11**
> User accepted the workbench direction but found section titles and task boundaries too weak.
> CSS-only correction: 17px/600 section headings, 13px/500 lane labels, 15px/600 task titles,
> 12px metadata, bounded 8px task/worktree surfaces with theme-relative 1px borders and 12px gaps.
> Sections have 24px separation; shared presenters/behavior and live `/` remain unchanged.
> Required stylesheet authoring exited 0 (Tailwind 4.3.5, 59ms); no tests or browser calls.
> Verification limited to file review because this was a low-risk visual/static change.
> Earlier c77a72a captures/critique are historical, not proof for these changed styles.
> Next: parent captures light/dark hierarchy in built-in browser and requests user approval.
> Still HOLD, not merge-ready. No server, board, rule or dependency edits.

> **Earlier Session Notes — BOARD-118 corrected preview checkpoint, 2026-11-11**
> Reworked the rejected gallery composition on the same branch/worktree. Scoped `.wb-workbench`
> styles now use a 20px utility heading, compact lane navigation, continuous populated task groups,
> dominant 15px task titles/quiet metadata and an adjacent 288px worktree rail from 820px upward.
> Extended pure `render_board_panel(..., populated_only=False)` near `board_serve.py:1158`;
> `wb_scope_content` opts in, live `/` keeps all lanes and original styles. Existing wb_ presenters,
> filters, tabs, fold/storage state and refresh handlers reused; no new function or state source.
> CSS authoring exited 0 (59ms); one regression run passed 12 tests (0.031s). Built-in browser
> tabs.list returned browser.disconnected; no retry, fallback, installs, server or board edits.
> Parent subsequently opened fresh corrected c77a72a preview at 15182/gallery: light/system-dark
> captures at 1104×877 CSS, 20px heading, no desktop overflow, scoped Project/Harness contents,
> actual tab clicks, Harness persistence through reload and System→Light change observed.
> Bounded current-document console: zero errors/no dropped data; four network requests all 200.
> Independent round-1 screenshot critique/unslop: HOLD, no blocking visual findings in those views.
> Evidence and remaining criteria: docs/reviews/BOARD-118-ui.md (parent addendum); ledger retained.
> Narrow matrix unsupported by built-in resize tools; keyboard/focus/contrast and other unchecked
> behavior remain open. Canonical artifacts notes.md write was guard-refused; no retry/bypass.
> Docs-only checkpoint; no source/browser/test/build actions. BOARD-120 policy commit 800cb3b
> stays separate Pending Merge. Next: parent resolves evidence gaps and obtains gallery approval.
> Live 15180 unchanged; no live rollout or merge readiness claimed.

> **Earlier Session Notes — BOARD-118 browser checkpoint blocked, 2026-11-11**
> Parent reviewed gallery diff and started http://127.0.0.1:15182/gallery from this worktree;
> live 15180 and earlier preview 15181 untouched. Parent built-in browser snapshot generation 2,
> tab `5007dd99-7e7a-47c0-b5d6-3c060c359dd7`, showed Project selected by default, Project 2 /
> Harness 1 task tabs, Project summary 2 in flight / 1 blocked / 2 tasks, Project 1 worktree,
> and labelled fixture empty/error states. Parent observations, not an independent QA pass.
> Harness click ref `e46` failed: `[browser.operation_failed] browser.click failed. UnknownVizError`
> (no exit code). Following tabs.list confirmed same gallery generation 2; no retry.
> Row Blocked on browser error and gallery approval. User will review gallery directly.
> Interactions, themes, responsive/canonical evidence and independent unslop remain incomplete;
> no merge readiness. Existing 11-test pass and user install/build proof below remain unchanged.
> This checkpoint is docs-only: no further tests, browser checks, source edits or installs.
> Next: user reviews preview; parent resolves review/tooling gates before any live screen rollout.

> **Session Notes — BOARD-118 gallery ready for browser preview, 2026-11-11**
> Same branch/worktree: `feat/redesign-board-console-component-gallery`,
> `.opencode/worktrees/redesign-board-console-component-gallery`, stacked over BOARD-119.
> Preserved the user's generated CSS, then regenerated it after a small gallery-only mobile grid
> correction. Shared idle-refresh guard now also protects focus within the gallery workbench;
> fixture Notes name actual review tasks, and obsolete gallery count constants were removed.
> User-supplied proof: `npm ci` added 56 packages, audited 63 in 18s, zero vulnerabilities;
> `npm run build` used Tailwind 4.3.5, done in 61ms. No installs by this resumed builder.
> Builder asset authoring: documented stylesheet build exited 0, Tailwind 4.3.5, 62ms.
> Builder verification: `python3 .opencode/skills/board/scripts/test_board_serve.py` exited 0,
> 11 tests passed (six existing plus five gallery regressions). Pure rendering/HTML/CSS and JS
> contract assertions only; no browser execution, screenshots or unslop pass claimed.
> Live `/` markup/layout retained; no server, port, dependency/lockfile, project or board changes.
> Next: parent arranges gallery browser preview/review and user approval. Not merge-ready;
> canonical capture tooling blocker and independent UI/unslop review remain open.
>
> Earlier blocked notes below are historical, superseded by the user-supplied install/build proof.

> **Session Notes — BOARD-118 approved install timed out, 2026-11-11**
> Confirmed session remains in `.opencode/worktrees/redesign-board-console-component-gallery`.
> User explicitly approved installing existing lockfile-declared UI dependencies only.
> `npm --prefix .opencode/skills/board/ui ci` produced no output and exceeded the shell's
> 120000ms timeout; no process exit code was returned. Installation completion is unknown.
> Stopped without retry, alternate command, build, tests, browser work or source edits.
> Gallery remains the partial checkpoint below, not ready for preview or merge.
> Next: parent reports the timeout and obtains a decision on an explicitly longer install attempt.

> **Session Notes — BOARD-118 gallery checkpoint blocked, 2026-11-11**
> Branch `feat/redesign-board-console-component-gallery`, worktree
> `.opencode/worktrees/redesign-board-console-component-gallery`, stacked over BOARD-119.
> Partial gallery-only source previews Project/Harness tabs, scoped summaries/tasks/worktrees,
> keyboard tab selection, remembered scope and shared filter/refresh/theme/density handlers.
> Live `/` markup remains unchanged; new layout CSS is scoped to `.wb-workbench`.
> Asset generation `npm --prefix .opencode/skills/board/ui run build` exited 127:
> `sh: 1: tailwindcss: not found`. Stopped without installs, retries or alternative generation.
> Committed `static/board.css` is unchanged and does NOT contain the new styles. Regression
> extension/run and browser/unslop review remain incomplete. No server or board edits.
> Next: parent requests approval to provision the existing pinned Tailwind dependencies, then
> resumes asset authoring and the one regression command. Gallery and screen approval remain open.

> **Session Notes — BOARD-119 data slice, 2026-11-11**
> Branch: `fix/include-project-repository-worktrees-in-console`; worktree:
> `.opencode/worktrees/include-project-repository-worktrees-in-console`, based on BOARD-117's
> `fix/refresh-project-board-discovery-every-minute`. Extended `worktree_state()` to read the
> registry on every request and enumerate control plus initialized registered project worktrees.
> Existing entry keys remain; additive `repo` (stable control/project id) and `base` metadata
> preserve repository-specific main, dirty and ahead/behind state even with identical branches.
> Six tests passed (exit 0), using temporary fixtures and mocked Git/server only.
> No UI changes, browser checks, builds, installs, server restarts, live project or board edits.
> Approved tabs/default/remembered selection are recorded in ADR-077, not implemented here;
> gallery approval is still required before redesigned screen rollout. BOARD-117 QA remains blocked.
> Next: parent reviews this data-only diff before the gallery/tab implementation slice.

> **Session Notes — BOARD-117 QA blocked, 2026-11-11**
> Branch: `fix/refresh-project-board-discovery-every-minute`; worktree:
> `.opencode/worktrees/refresh-project-board-discovery-every-minute`.
> JSON and HTML rediscover boards on every request; ignored projects can appear or disappear
> without restarting. Default refresh is 60 seconds; explicit `--file`, `--refresh`, Pause and
> Refresh now remain. Four temporary-fixture regression tests passed (exit 0).
> The first patch was refused while session context was the factory root; after the orchestrator
> moved the session into this worktree, the authorized relative-path retry succeeded. No guard changed.
> Parent code review found no blocker. Independent regression rerun: four tests, exit 0.
> Canonical capture exited 2: Playwright was not found locally or globally (exact command below).
> Report: `docs/reviews/BOARD-117-qa.md`; no product defect was demonstrated.
> Main server 15180 is unchanged; preview 15181 was launched from this worktree. No restarts or
> dependency installation. User approved built-in QA; reviewer child disconnected, but attached
> parent observed separate harness/project panels (18/14 cards, total 32), configured 60s refresh,
> and actual Refresh now reload while paused (changed timeOrigin). Pause resets after reload.
> These are parent observations, not an independent reviewer pass; details in the QA addendum.
> Later click failed `[browser.operation_failed] browser.click failed. UnknownVizError` (no exit
> code); no retry. Search input/URL observed, filtering not proven with unreliable `.card` selector.
> Filter retention, elapsed timer, keyboard, themes, responsiveness and visual/unslop/gallery review
> remain unchecked. This is a wip checkpoint, not merge-ready; no product defect proven.
> Next: user decides whether to retry built-in checks after desktop error resolution; canonical
> capture separately needs approved Playwright provisioning or its installed location.
> BOARD-118 approved redesign gallery is queued behind BOARD-117, not implemented.

Failed capture command (exit 2; recorded, not rerun):

```sh
node .opencode/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:15181 --route / --scope factory --task-id BOARD-117 --project . --scheme both --date 2026-11-11
```
> **Session Notes — BOARD-120 governance update, 2026-11-11**
> Branch: `docs/require-catalog-skills-and-browser-ui-reviews`; worktree:
> `.opencode/worktrees/require-catalog-skills-and-browser-ui-reviews`, based on `opencode`.
> Root/template §A7 now requires catalogue selection, relevant skills/references and reporting
> for every task. §B4.2 now requires built-in-browser-only UI verification/review, replacing
> scripted captures, not supplementing them. Agents, derived commands, workflow skills and
> current UI/stack guidance align. ADR-079 records the approved policy.
> Gallery approval, independent review, accessibility, unslop, bounded ledger/fingerprint and
> finding-validation gates remain. Tools and historical evidence are unchanged; scope files
> remain read-only and their old capture directions are superseded by canonical §B4.2.
> File review completed. The architect-authorized corrected consistency command exited 0:
> six exact-block checks, seven agent checks, 23 active documents, nonbrowser script ownership,
> bounded finding gates, 27-file Markdown-only scope and whitespace checks passed.
> The first check's overbroad pattern falsely matched the board-editing rule; that rule remains
> unchanged. No build, runtime, browser or model-behavior checks. Next: architect completes review
> and decides whether to offer the local documentation commits for human merge.
> No board edits, project sync, guard/security changes, merge or push. Earlier notes are historical.

> **Session Notes — BOARD-116 documentation review passed, 2026-11-11**
> Added the approved built-in interactive browser policy to root/template §B4.2 and aligned the
> reviewer agents, QA skill, `/ui` and UI-UX guidance. Canonical captures remain script-only;
> QA and unslop gates are unchanged. Branch: `docs/use-opencode-browser-for-interactive-ui-reviews`;
> worktree: `.kilo/worktrees/use-opencode-browser-for-interactive-ui-reviews`, based on migration
> checkpoint `ec7501f` on `feat/port-factory-harness-to-opencode-v2`.
> Parent reviewed all 12 file diffs: PASS. Reviewed docs change prepared for human review;
> local task commit authorized through the existing Kilo bootstrap guard. Next: human reviews the task commit.
> Verification limited to file review because this was a low-risk visual/static change.
> No browser/runtime checks, builds or tests ran. BOARD-114 remains blocked on the security fixture
> `EACCES`; migration work was not resumed and is not merge-ready. Earlier notes are historical.

> **Session Notes — BOARD-115 documentation review, 2026-11-11**
> Added the approved §B11 committed-handoff policy to root/template rules and aligned B5,
> closeout, handover and git-worktree instructions. Branch:
> `docs/require-committed-worktree-handoff-checkpoints`; worktree:
> `.kilo/worktrees/require-committed-worktree-handoff-checkpoints`, based on the user-created
> migration checkpoint `bc3ca6c` on `feat/port-factory-harness-to-opencode-v2`.
> Parent's docs-only review passed; local task commit prepared for human review through the
> authorized existing Kilo bootstrap guard. Next: human reviews the BOARD-115 task commit.
> BOARD-114 remains blocked on the security test's `/tmp/opencode` fixture `EACCES`; no migration
> work or verification was resumed. The migration is not merge-ready; this is not approval to merge it.
> Earlier notes below describe that prior session, not current status.
> Verification limited to file review because this was a low-risk visual/static change.

> **Session Notes — BOARD-114 blocked, 2026-11-11**
> Security adapter and policy/sync changes are implemented but unverified. The command
> `node --test .opencode/plugins/factory-guard/guard.test.mjs` exited 1: two tests could not
> create fixture directories under `/tmp/opencode` (`EACCES`); policy/runtime merge test passed.
> No retry or alternate path attempted. Next: user authorizes a writable fixture location or
> repairs access. Container migration, native runtime checks and independent review remain open.
>
> **Chunk 1 evidence**
> Native OpenCode layout/config and existing harness mechanics are ported on
> `feat/port-factory-harness-to-opencode-v2`, based on `opencode`; no commit yet.
> Bootstrap worktree remains `.kilo/worktrees/port-factory-harness-to-opencode-v2`.
> Parent reviews the diff and the migrated test result next. Security/plugin and container
> chunks remain open; do not treat this work as migration-complete or ready for merge.
> Verification: `python3 .opencode/skills/git-worktree/scripts/test_env.py` exited 0,
> `all checks passed` (lifecycle/env plus native permissions, preservation and base checks).
>
> The older session notes below are retained as context, not current lane status.

> **Session Notes** (keep at the very top, updated every session)
> - **Last session:** 2026-11-10 — the 67 upstream specialist skills were ported as a
>   read-on-demand catalogue at `.opencode/catalog/`, with an index at `.opencode/catalog/README.md`.
>   The catalogue sits outside the auto-discovered skills folder, so the loader never sees it.
>   BOARD-107, branch `feat/port-the-specialist-skill-catalog`.
> - **In flight:** that branch waits for the user to merge it. The plan skill branch
>   (2026-11-10, BOARD-106) also still waits for a merge, and so does the live board viewer
>   change (2026-11-04, BOARD-102).
> - **Next action:** the user reviews and merges `feat/port-the-specialist-skill-catalog`.
> - **Before:** 2026-11-10 — the upstream `feature-forge` and `architecture-designer` skills
>   were merged into one plan skill at `.opencode/skills/plan/`, with their references carried over
>   intact and every phase mapped onto a document this repository already has. BOARD-106, branch
>   `feat/port-a-merged-plan-skill`.
> - **In flight:** that branch waits for the user to merge it. The live board viewer change
>   (2026-11-04, BOARD-102) also still waits for a merge.
> - **Next action:** the user reviews and merges `feat/port-a-merged-plan-skill`.
> - **Before:** 2026-11-04 — the live board viewer became a vertical accordion: collapsible
>   lanes, compact cards that expand to their detail, the last 10 merged rows with a "Show all"
>   control, and folds kept in the browser. BOARD-102, branch
>   `feat/compact-accordion-redesign-of-the-live`.
> - **In flight:** that branch waits for the user to merge it. The board file and the JSON
>   endpoints are unchanged; the viewer still writes nothing.
> - **Next action:** the user reviews and merges the branch. The earlier factory/project split
>   (2026-11-02) also still waits for a merge.
> - **Before:** 2026-11-02 — split the factory from the project. The factory repository now
>   holds only the harness; the Inhouz Cloud AI platform moved to its own git repository at
>   `project/`, with its own board, documentation set and 75 microservice repositories under
>   `project/apps/`. ADR-053, ADR-054 and ADR-055 record the split.

## 1. Overview

- **What it is:** the software factory — a written rule set, a live work board, specialised
  builder and reviewer agents, and a loop that carries every task from decision to merged branch.
  There is no application runtime here.
- **Who uses it:** one human owner and the OpenCode agents that act for them. The owner approves
  decisions and merges branches; the agents build and review inside worktrees.
- **Tech stack:** Markdown rules plus the OpenCode V2 agent and command system (`.opencode/agents/`,
  `.opencode/commands/`) running on git worktrees. Python 3.9+ standard library for the scripts.
  Details in `docs/STACK.md`.
- **How to use it:** open the factory in OpenCode with the `architect` primary agent. Read `AGENTS.md` at the root. Run `/board` to
  see the live board, `/decide` to approve a decision, `/run` to build a row in a worktree, `/ui`
  for the QA lane, `/closeout` to refresh docs, `/handover` to refresh the application memory map.

## 2. Directory map

| Path | Contents |
|---|---|
| `AGENTS.md` | Root rules for the architect, orchestrator, and every builder (Part A, Part B). |
| `README.md` | The front page: what the factory is, how to point it at a project, quick start. |
| `.opencode/agents/` | `architect` primary and six specialist subagents: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`. No model overrides. |
| `.opencode/commands/` | The eight slash commands: `decide`, `board`, `board-view`, `run`, `components`, `ui`, `handover`, `closeout`. |
| `.opencode/policies/` | The canonical guard-rail policy: `git-policy.json`. |
| `.opencode/repos.json` | The repo map of this repository. The only way into a repository. |
| `.opencode/scopes/` | The canonical scope rules, one file per scope. `guard.py sync` writes them into a project's app repositories as their `AGENTS.md`. |
| `.opencode/skills/` | The five skills with their scripts: `board`, `git-worktree`, `qa-review`, `unslop`, `plan`. |
| `.opencode/skills/plan/` | The merged plan skill (MIT, © 2025 Jeffallan — upstream `feature-forge` and `architecture-designer`). `SKILL.md` plus `references/`: the interview bank, the specification template, EARS syntax, acceptance criteria, pre-discovery subagents, system design, architecture patterns, database selection, ADR template, NFR checklist, and the two superpowers research documents. |
| `.opencode/catalog/` | 67 upstream specialists (MIT, © 2025 Jeffallan, https://github.com/Jeffallan/claude-skills), with preserved upstream content/licences and OpenCode tool adaptation headers. Outside `.opencode/skills/` discovery; not configured as an extra skill source, so read only on demand. |
| `.opencode/catalog/README.md` | The catalogue index: read before every task, then apply each relevant skill and required reference; report skills used or that none matched. Example lists do not limit selection (§A7). |
| `.opencode/worktrees/` | Agent worktrees, one per task. Git-ignored. |
| `.devcontainer/` | Container definition: `Dockerfile`, `devcontainer.json`, the redaction script. |
| `docs/` | The factory's own governance set. Product documentation lives in the project repository. |
| `.opencode/scopes/service.md` | The default scope rules for a work surface with no scope file of its own. A work surface carries a pointer to this file, never a copy of it. |
| `templates/project/` | The blank project skeleton a new project starts from. |
| `project/` | A project repository in this workspace. Its own git repository. Never tracked here. |

## 3. Entry points

| Entry point | What it does |
|---|---|
| `AGENTS.md` | The rule set, read by every agent at the start of a task. |
| `.opencode/commands/*.md` | Slash commands that package the workflow. |
| `.opencode/skills/board/scripts/board.py` | The board's only writer. `show`, `add`, `set-status`, `set-field`, `note`, `remove`, `lanes`, `add-column`. |
| `.opencode/skills/board/scripts/board_serve.py` | The read-only factory board console on port 15180. Server-rendered, offline, standard library at runtime: a three-column dashboard shell (lane/filter sidebar, KPI strip, segmented flow meter, dense lane panel, sticky worktrees rail), search and status/type/priority filters with URL state, parsed Notes checklists, branch copy, and `j`/`k`/`/`/`Enter`/`Esc` keyboard control. Serves `/static/board.css` and the two self-hosted Geist fonts. `/api/board` retains its shape; `/api/worktrees` retains its array/fields and adds `repo` and `base` metadata. |
| `.opencode/skills/board/ui/` | The Tailwind v4 source for the console (`package.json`, `src/app.css`); `npm --prefix .opencode/skills/board/ui run build` writes the committed `static/board.css`. |
| `.opencode/skills/board/static/` | The committed stylesheet and the Geist Sans/Mono variable fonts with their SIL OFL licence. |
| `.opencode/skills/git-worktree/scripts/worktree.py` | Creates, lists, verifies and cleans the worktree of a board row. `create`, `resume`, `discard` (`--force`, `--yes`), `handoff`, `list`, `verify`, `cleanup` (by slug or by `--board`). The teardown commands set the row's lane: `cleanup --board` sets `Merged`, `discard --board` sets `Ready`. |
| `.opencode/skills/git-worktree/scripts/env.py` | Provisions the local env files of a worktree. `sync`, `status`, `clean`. |
| `.opencode/skills/git-worktree/scripts/guard.py` | The guard rails: `check-git`, `check-policy`, `check-delete`, `check-worktree`, `check-repos`, `sync` (one repo or `--all`). |
| `.opencode/skills/git-worktree/scripts/scope.py` | The generated pointer a work surface carries, and the local exclude rule that keeps it out of every commit. |
| `.opencode/skills/qa-review/scripts/browser-review.mjs` | Historical Playwright capture tool, retained unchanged; not UI verification/review evidence. Built-in browser workflow: QA skill and §B4.2. |
| `.opencode/skills/qa-review/scripts/check-finding.py` | Validates a QA finding and prints its fingerprint. |
| `.opencode/skills/qa-review/scripts/ledger.py` | Opens, closes and reports the QA↔fix rounds of a row. |
| `.opencode/skills/unslop/scripts/snapshot.mjs` | Retained historical page snapshot tool, not UI QA or a built-in browser fallback. Live URLs follow the same §B4.2 browser policy. |

## 4. Modules and functions

Chunk 1 reuses these existing boundaries:
- `guard.generated_permission()` (pure) emits native ordered `{action, resource, effect}` rules;
  `write_permission_map()` (effectful) preserves unrelated config keys while replacing that array.
- `worktree.default_base()` (effectful git inspection) prefers `opencode` only for a factory;
  project/app defaults stay unchanged. `repo_root()` (effectful) uses Git's main checkout.
- `board_serve.worktree_state()` (effectful filesystem/Git inspection) reuses registry resolution,
  repository validation, worktree parsing and base selection for per-repository state.
- Native read/edit path rules remain; grep/glob target-path and automatic context enforcement
  are pending the limited guard plugin. Legacy bootstrap is not accepted by steady-state guards.

| Symbol | File | Responsibility | Kind |
|---|---|---|---|
| `board.py` | `.opencode/skills/board/scripts/board.py` | Deterministic manipulation of the markdown board. Never writes prose. | effectful (file I/O) |
| `board_serve.py` | `.opencode/skills/board/scripts/board_serve.py` | Serves the board and the live worktree state read-only, as a server-rendered factory console with a segmented flow meter, keyboard-first filtering, parsed Notes checklists, a sticky worktrees rail, and the static Tailwind CSS and font files. | effectful (network, file I/O) |
| `discover_boards()` / `build_payloads()` | `.opencode/skills/board/scripts/board_serve.py:124`, `:1704` | Discovery checks filesystem paths, including ignored `project/docs/BOARD.md`; payload callbacks rediscover on every HTML/board-JSON request unless explicit paths were supplied. Existing parser and pure renderer stay shared. Default refresh: 60 seconds; CLI override and manual controls retained. | effectful (filesystem, git, clock); HTML rendering is pure |
| `worktree_state()` | `.opencode/skills/board/scripts/board_serve.py:171` | Reloads the existing registry and enumerates control/project via `load_repos`, `resolve_repo`, `is_git_repo`, `list_worktrees`, `default_base` and `git_out`. Omits absent/uninitialized projects. Each entry adds `repo` and `base`; existing array and fields stay intact. Main detection and counts use only that repository. Invalid maps flow through existing payload exception handling. | effectful (filesystem, Git); entry construction is deterministic from results |
| `wb_scope_default()` / `wb_scope_tabs()` / `wb_scope_content()` | `.opencode/skills/board/scripts/board_serve.py:1449`, `:1456`, `:1470` | Pure reusable selection fallback, tablist and scoped content presenters; map harness to control worktrees and reuse existing counts/panels/lanes/cards/rail. Gallery only; asset authored, browser review pending. | pure |
| `gallery_scope_fixtures()` / `build_gallery_html()` | `.opencode/skills/board/scripts/board_serve.py:1494`, `:1519` | Pure labelled fixtures and gallery composition; identical BOARD-001 IDs are separated by board keys. No live data or second task store. | pure |
| `selectScope()` / `wb_wt_row(show_base=True)` | `.opencode/skills/board/scripts/board_serve.py:242`, `:1061` | JS tab DOM/storage effects reuse dashboard state and existing handlers; pure worktree row optionally adds base/reference labels, preserving default live output. | effectful JS; pure Python presenter |

Gallery regression inventory: `test_board_serve.py:211` adds five tests for default/missing scope,
unique DOM IDs and tab/panel links, duplicate task IDs across boards, isolated counts/worktrees,
error/empty/escaped output, default worktree markup compatibility, shared handler contracts and
gallery-only layout/CSS themes. These do not execute JS or prove browser behavior.
| `worktree.py` | `.opencode/skills/git-worktree/scripts/worktree.py` | Creates the worktree for a board row, derives its name and branch, records it back on the row. `resume` reuses a live worktree, `discard` removes one, `discard --force --yes` destroys one after writing a recovery copy, `handoff` prints the hand-off block, `cleanup` removes a merged worktree by slug or by the row that owns it. A teardown by row sets that row's lane: `cleanup` sets `Merged`, `discard` sets `Ready`. | effectful (git, filesystem) |
| `env.py` | `.opencode/skills/git-worktree/scripts/env.py` | Copies the two local env files from a repository's main checkout into a worktree, excludes them from git, and removes them again. Never prints a value. | effectful (filesystem, git exclude) |
| `test_env.py` | `.opencode/skills/git-worktree/scripts/test_env.py` | Self-test for the env provisioning and the worktree reuse rules, in a throwaway repository under a temp directory. | effectful (filesystem, git) |
| `guard.py` | `.opencode/skills/git-worktree/scripts/guard.py` | The guard rails and the sync that carries them into an app repository. | effectful (git, filesystem) |
| `check-finding.py` | `.opencode/skills/qa-review/scripts/check-finding.py` | Validates a finding and derives its fingerprint. | pure |
| `ledger.py` | `.opencode/skills/qa-review/scripts/ledger.py` | The round ledger of a row. | effectful (file I/O) |
| `browser-review.mjs` | `.opencode/skills/qa-review/scripts/browser-review.mjs` | Historical capture tool; not UI verification/review. Source unchanged. | effectful (browser, filesystem) |
| `snapshot.mjs` | `.opencode/skills/unslop/scripts/snapshot.mjs` | Saves a live page or a local file as one standalone HTML file with its assets inlined, and saves a screenshot next to it. Resolves Playwright and chromium the same way the QA script does. | effectful (browser, filesystem) |

## 5. Data

| Artefact | Where | What it holds |
|---|---|---|
| The board | `docs/BOARD.md` | One row per unit of factory work. The only state. |
| The decisions | `docs/DECISIONS.md` | Append-only ADR table, ADR-001 onward. |
| The changelog | `docs/changelog/CHANGELOG.md` | The engineering log, newest first, one section per change. |
| The repo map | `.opencode/repos.json` | Repo id → path, relative to this repository's root. |
| The policy | `.opencode/policies/git-policy.json` | The guard-rail rules. The source of the generated permission map. |

## 6. States and state transitions

The board's lanes are the state machine of the factory:
`Backlog` → `Ready` → `In Progress` → `In Review` → `Pending Merge` → `Merged`, plus `Blocked`
and `Dropped`. A row may not reach `Pending Merge` while a `Fix` row it spawned is open, and the
QA↔fix loop is capped at three rounds. Full rules in `AGENTS.md` §B4.

## 7. Public interfaces

The factory exposes no network API. Its public surface is the file layout above and the CLI of
the scripts. The worktree CLI is `worktree.py` (`create`, `resume`, `discard`, `handoff`, `list`,
`verify`, `cleanup`) and `env.py` (`sync`, `status`, `clean`). `discard` takes `--apply`, `--force`
and `--yes`: `--force` alone prints the destruction plan, and `--force --yes` acts after writing a
recovery copy under the repository's `cleanup-wt/` folder. `handoff --board <ID>` prints review
commands and changes nothing. Merge/teardown guidance requires the live §B11 readiness gate;
refused handoffs show blockers only after review commands (see BOARD-123 contract above).
`cleanup` takes the worktree either as a slug or as `--board <ID>`, which
resolves the row's `Branch/Worktree` cell and clears it when the worktree is gone; giving both or
neither is a usage error. The lane each command sets: `create` and `resume` put the row in
`In Progress`, `cleanup --board` puts it in `Merged`, `discard --board` puts it back in `Ready`,
and the slug form of `cleanup` touches nothing on the board.

## 8. Configuration and environment

See `docs/ENVIRONMENT.md`. Names only, never values.

## 9. Dependencies

| Dependency | Why |
|---|---|
| Python 3.9+ standard library | Every script. No third-party package. |
| Playwright (global install in the dev container) | Retained historical/test tooling; not UI QA. |
| Chromium (`/usr/bin/chromium`) | Retained historical/test tooling; not UI QA. |
| The unslop skill | CC BY 4.0 — Damir Sokolovsky ([@heydamir](https://x.com/heydamir)). The credit line must survive in every copied file of `.opencode/skills/unslop/`. |
| The plan skill | MIT — © 2025 Jeffallan (https://github.com/Jeffallan), upstream skills `feature-forge` and `architecture-designer`. The credit line must survive in every copied file of `.opencode/skills/plan/`. |
| The superpowers research documents | MIT — © Jesse Vincent (obra/superpowers), copied into `.opencode/skills/plan/references/`. The credit line must survive in both files. |
| Git | Worktrees, branches, the guard rails. |

## 10. Testing

<<<<<<< HEAD
Verification uses focused script tests. The verification of a change is the smallest relevant script run, recorded with
=======
UI verification/review uses only OpenCode's built-in browser (§B4.2, QA skill). Browser evidence
stays under `artifacts/<scope>/qa/<date>/<task-id>/` with route, viewport, theme, steps, expected
and observed results. Screenshot/`files.get` paths are server-local; desktop file IDs require
transfer. Unavailable browser access or measurements hold criteria, with no fallback or pass claim.

No test suite. The verification of a change is the smallest relevant script run, recorded with
>>>>>>> docs/require-catalog-skills-and-browser-ui-reviews
its result and a `file:line` proof (AGENTS.md §B4 "Verification cost rule"). The dev container
ships `.devcontainer/test-kilo-redact.sh`, which checks the redaction startup file.

`python3 .opencode/skills/git-worktree/scripts/test_env.py` builds
a throwaway git repository under a temp directory and proves the env provisioning, the
worktree reuse rules, the hand-off block and the teardown named by a board row.

`python3 .opencode/skills/board/scripts/test_board_serve.py` uses standard-library unittest,
temporary fixture boards and a mocked server. Six tests pass for BOARD-117/119: new/removed project
discovery in HTML and JSON, separate tasks even with identical IDs, fixed explicit file selection
with fresh reads, default 60 seconds, CLI override and existing control source. No sockets, live
project reads, server restarts or external dependencies. Control-source assertions are not browser
interaction or timer evidence. BOARD-119 reuses actual registry, Git parsing and base helpers with
mocked Git results; covers changed registry paths, same-name branches across repositories,
per-repo main/base/counts/dirty state, missing/uninitialized project, SHA/count fallback, additive
endpoint keys and existing malformed/invalid registry handling. No live Git calls.

## 11. Known issues and risks

- BOARD-114 is partial. OpenCode runtime discovery, plugin security and container integration
  are not verified by the Python lifecycle test. Do not claim legacy grep/glob path denies work.
- The native edit path patterns alone are not a proof of worktree confinement for Location-relative
  paths; automatic context enforcement belongs to the next chunk.

- The factory has no remote, so the harness cannot be shared yet. The user decides where it goes.
- A project copies the harness by hand, so a factory change does not reach the project
  automatically (ADR-054). The copy is deliberate: the project owns its copy from then on.

## 12. Open questions

- Where the factory repository is published, and where the project repository is pushed.
- Whether the factory's `.opencode/` changes reach the project by a command the user runs, or by a
  hook. Today it is `guard.py sync --repo project --apply`.

## 13. Document map

- `AGENTS.md` — the rules.
- `docs/PROJECT_STRUCTURE.md` — the layout.
- `docs/UI-UX.md` — the visual language, the anti-slop rules and the QA evidence spec.
- `docs/BOARD.md` — the factory's live board.
- `docs/DECISIONS.md` — the factory's decisions.
- `docs/STACK.md` — the tools and commands.
- `docs/ENVIRONMENT.md` — the environment variables.
- `docs/PROJECT_STATE.md` — where the work stands.
- `docs/changelog/` — the engineering log.
- `templates/project/` — the blank project skeleton.
