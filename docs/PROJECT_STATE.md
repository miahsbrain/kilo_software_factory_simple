# PROJECT STATE — software factory

## Current session — BOARD-121 main workbench (2026-11-11)

- Gallery approval granted by user: “fantastic, now build main dashboard”. Main `/` now uses the
  approved shared workbench composition with real repository-scoped tasks/counts/worktrees.
- Project default/remembered-scope fallback, criteria, filters/URL, keyboard selection, theme,
  density, 60s/Pause/manual refresh retained. Real timestamp/live/stale status shown; no fixture
  notice or fixture rendering on main. Explicit `--file` stays fixed and associates by repo path.
- Single regression run: `python3 .opencode/skills/board/scripts/test_board_serve.py` exited 0,
  15 tests in 0.048s. No CSS change/regeneration, dependencies, server/port, board or rule changes.
- Parent inspected `fd89d5b` and started main preview 15183. Supplied snapshot/DOM: Project default,
  14 tasks/result 14 of 14/three project worktrees; hidden Harness 21 tasks/eight control worktrees.
  At 1000×700 CSS no horizontal overflow; 60s refresh, 17px/600 heading, no fixture notice.
- Parent observations only, not independent QA: `docs/reviews/BOARD-121-qa.md`. Screenshot after
  tabs.focus returned browser.operation_failed: “Screenshot needs a visible tab. Call
  browser.tabs.focus and keep its desktop window visible.” No retry/fallback or screenshot.
- Next: visible desktop window, then parent resumes built-in screenshot/QA/critique. Independent
  visual/unslop, keyboard and full responsive checks held; no blanket pass or merge readiness.
  Docs-only checkpoint, no new tests/builds/browser calls. Production 15180 and BOARD-120 unchanged.

## Earlier session — BOARD-118 hierarchy correction (2026-11-11)

- User found section/task boundaries too weak. CSS-only change strengthens 17px/600 section
  headings, differentiates 13px lane labels, and bounds task/worktree surfaces with 1px borders,
  8px corners and 12px gaps; 15px/600 task titles stay above 12px metadata in both densities.
- Existing theme palette, shared presenters and interaction state retained; live `/` unchanged.
- Required stylesheet authoring exited 0 (59ms). File review only; no tests/browser calls.
- Earlier c77a72a captures and round-1 HOLD are historical, not validation of changed CSS.
- Next: parent inspects fresh light/dark built-in screenshots for hierarchy and resolves remaining
  review/approval gates. No server/board/rules/dependency changes. Not merge-ready.

## Earlier session — BOARD-118 corrected preview checkpoint (2026-11-11)

- Replaced rejected meter/card composition with compact utility header, inline lane navigation,
  populated task groups, two-line task hierarchy and desktop-adjacent worktree rail (≥820px).
- Shared renderers/styles retained; optional populated-only board mode leaves live `/` unchanged.
  No duplicated filter/storage state. Preview fixtures only; no live redesign authorized yet.
- CSS generation: exit 0, 59ms. Single Python regression run: exit 0, 12 tests in 0.031s.
- Parent fresh c77a72a preview 15182/gallery: light/system-dark at 1104×877 CSS, 20px heading,
  no desktop overflow; scoped tab contents, actual clicks, saved Harness/reload and Light change
  observed. Current-document console zero errors/no truncation; four network requests all 200.
- Independent round-1 screenshot critique/unslop HOLD, no blocking visible findings. Parent
  interactions are not independent QA. Evidence/unchecked criteria: reviews/BOARD-118-ui.md.
- Built-in tools lack viewport resize; narrow matrix, keyboard/focus/contrast and remaining
  behavior unverified. Canonical artifacts notes.md patch was refused; no retry/write bypass.
- Docs-only checkpoint includes critic report and ledger. No source edits/browser/tests/builds.
  BOARD-120 policy commit 800cb3b remains separate Pending Merge. Live 15180 unchanged.
- Next: parent resolves evidence gaps and requests gallery approval; not merge-ready.

## Earlier session — BOARD-118 browser checkpoint blocked (2026-11-11)

- **Preview:** Parent reviewed diff and started http://127.0.0.1:15182/gallery from BOARD-118
  worktree. Live 15180 and prior preview 15181 unchanged. User will review gallery directly.
- **Parent observation:** Built-in browser tab `5007dd99-7e7a-47c0-b5d6-3c060c359dd7`, snapshot
  generation 2: Project selected default, Project 2 / Harness 1 tasks; Project summary 2 in flight,
  1 blocked, 2 tasks, 1 worktree; labelled fixture empty/error states. Not independent QA.
- **Stop:** Harness click ref `e46` returned `[browser.operation_failed] browser.click failed. UnknownVizError`
  (no exit code); following tabs.list confirmed same gallery generation 2. No retry.
- **Blocked:** Browser error plus gallery approval. Interactions/themes/responsive/canonical
  evidence and independent unslop incomplete; not merge-ready. Parent handles remaining gates.
- **Checkpoint:** Docs only, no new checks/source edits/installs. Existing 11 tests passed and
  user install/build proof below preserved. Next: user reviews preview; no live screen rollout.

## Earlier session — BOARD-118 gallery ready for browser preview (2026-11-11)

- **Phase:** Gallery implementation and focused regression verification complete; browser review
  and gallery approval pending. Same assigned worktree/branch, stacked over BOARD-119.
- **User proof:** Existing locked dependency `npm ci` added 56 packages, audited 63 in 18s,
  zero vulnerabilities; stylesheet build Tailwind 4.3.5 completed in 61ms. Builder preserved CSS.
- **Builder proof:** Required CSS regeneration after mobile grid correction exited 0 (62ms).
  `python3 .opencode/skills/board/scripts/test_board_serve.py` exited 0: 11 tests passed.
  Rendering/markup/CSS and shared JS contract assertions, not browser execution.
- **Scope:** Gallery only, live `/` markup/layout unchanged. No installs, lockfile changes,
  server/port changes, real project/board or permanent-rule edits in this resumption.
- **Next:** Parent arranges `/gallery` browser preview and independent review/user approval.
  Canonical capture and unslop remain unchecked. Ready for preview, not merge-ready.

## Earlier BOARD-118 blocked checkpoints (2026-11-11)

- **Approved resumption:** User authorized `npm --prefix .opencode/skills/board/ui ci` for
  existing locked dependencies only. It produced no output before the 120000ms tool timeout;
  no exit code returned. Installation completion unknown. Stopped without retry/workaround.
  No build, regression command, browser work or source edits in this resumption.
- **Current next action:** Parent requests a decision on a longer explicit install attempt.
  Gallery remains incomplete and not ready for preview or merge; original blocker below is history.

- **Task:** `feat/redesign-board-console-component-gallery`, assigned worktree of the same slug,
  stacked over BOARD-119. Gallery-only source partially implemented; no live screen rollout.
- **Blocker:** `npm --prefix .opencode/skills/board/ui run build` exited 127 with
  `sh: 1: tailwindcss: not found`. No dependency installation, retry or workaround.
- **Incomplete:** Generated CSS remains unchanged; test extension and regression command not run
  after this environmental stop. Canonical capture/unslop/browser review and gallery approval open.
- **Next:** Parent asks user to approve provisioning existing pinned stylesheet dependencies.
  Resume asset generation and focused verification only after that decision. Not merge-ready.

## Earlier session — BOARD-119 data slice (2026-11-11)

- **Phase:** Build complete; parent review pending for the data-only slice.
- **Active task:** `fix/include-project-repository-worktrees-in-console` in
  `.opencode/worktrees/include-project-repository-worktrees-in-console`, based on BOARD-117.
- **Changed:** Request-time registry-driven control/project worktree enumeration; additive `repo`
  and `base` metadata. Existing Git/map helpers and endpoint array/entry fields are reused.
- **Verification:** `python3 .opencode/skills/board/scripts/test_board_serve.py` → exit 0,
  six tests passed; temporary fixtures, mocked Git/server, no real project reads or mutations.
- **Scope:** No tabs/screens, browser checks, installs, builds, restarts or board edits. Tabs,
  Project default when present, remembered selection and gallery-before-rollout approval are
  recorded in ADR-077 for later slices. Existing 60-second/manual refresh is unchanged.
- **Next action:** Parent reviews this diff, then sequences gallery/tab work. BOARD-117's QA
  blockers below are not resolved by these tests; this slice does not claim browser QA completion.

## Earlier session — BOARD-117 (2026-11-11)

- **Phase:** QA blocked on canonical tooling and later desktop click error; wip, not merge-ready.
- **Active task:** `fix/refresh-project-board-discovery-every-minute` in
  `.opencode/worktrees/refresh-project-board-discovery-every-minute`.
- **Changed:** Request-time board rediscovery for JSON/HTML, 60-second default, focused regressions
  and ADR-076. Explicit file selection, refresh override and existing controls retained.
- **Verification:** Independent `python3 .opencode/skills/board/scripts/test_board_serve.py` rerun
  → exit 0, four tests passed. Parent code review found no blocker. No tests rerun here.
- **Interactive evidence:** User approved built-in QA; child `ses_e353521ebffe98nk7trQD9wqQK`
  disconnected. Attached parent observed separate harness/project panels (18/14, total 32),
  configured 60s and actual manual reload while paused via changed timeOrigin. Pause resets on reload.
  This is not an independent pass. Exact tab/generation/ref evidence: QA report's parent addendum.
- **Interactive stop:** Later Refresh now click returned `[browser.operation_failed] browser.click failed. UnknownVizError`
  (no exit code); tabs.list showed same URL/generation 4, loading false; no retry. Search input/URL
  observed, filtering not proven (unreliable `.card` selector). Filter retention, elapsed timer,
  keyboard, themes, responsiveness and visual/unslop/gallery review remain unchecked. No product defect proven.
- **Capture:** `node .opencode/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:15181 --route / --scope factory --task-id BOARD-117 --project . --scheme both --date 2026-11-11`
  → exit 2: Playwright not found in this project or global npm install. Exact error and unchecked
  criteria: `docs/reviews/BOARD-117-qa.md`. No additional tests/captures run for this checkpoint.
- **Next action:** User decides whether to retry built-in checks after desktop error resolution;
  canonical capture separately needs approved Playwright provisioning or its installed location.
  BOARD-118 approved redesign gallery is queued behind this, not implemented.
- **Servers:** Main 15180 unchanged; preview 15181 launched from this worktree. No restarts,
  dependency installation, main board or ignored project edits.
- **Context:** Initial patch refused from factory-root session context; orchestrator moved the
  session to this worktree, and the authorized relative-path retry succeeded without guard changes.

## Earlier session context (historical)
- **Phase:** BOARD-120 governance-only implementation; corrected consistency check passed, awaiting architect review.
- **Active task:** `docs/require-catalog-skills-and-browser-ui-reviews` in
  `.opencode/worktrees/require-catalog-skills-and-browser-ui-reviews`, based on `opencode`.
- **Change:** mandatory catalogue selection/application/reporting for every task; UI verification
  and review use only OpenCode's built-in browser. ADR-079 supersedes script-only capture policy.
  Gallery approval, independent review, accessibility, unslop and bounded findings gates remain.
- **Verification:** file review completed. Architect authorized one corrected browser-specific
  consistency check after the first check's board-editing false positive. Corrected command exited 0:
  six exact-block checks, seven agent checks, 23 active documents, preserved nonbrowser script
  ownership/finding gates, 27 Markdown-only files and clean whitespace. No build/runtime/browser/model tests.
  No board, tool-source, dependency, guard/security or project-copy edits.
- **Next action:** architect completes review and decides whether to offer the local documentation
  commits for human merge. Existing migration limitations remain unresolved.

## Historical state (before BOARD-120)
- **Phase:** BOARD-116, parent docs review passed; reviewed change prepared for human review/local commit.
- **Active task:** `docs/use-opencode-browser-for-interactive-ui-reviews` in
  `.kilo/worktrees/use-opencode-browser-for-interactive-ui-reviews`, based on migration checkpoint
  `ec7501f` on `feat/port-factory-harness-to-opencode-v2`. Approved built-in interactive browser
  policy and derived instructions updated; canonical captures remain script-only and QA/unslop
  gates remain mandatory. No approval to merge the migration.
- **Migration:** BOARD-114 remains blocked during security verification; not resumed by BOARD-116.
- **Progress:** Native `.opencode/agents`, `commands`, `skills`, `catalog` and `opencode.jsonc`;
  architect primary plus six specialists; models inherit session selection. Existing Python/JS
  mechanics migrated, native ordered permission generator, factory base preference `opencode`.
- **Integration:** `opencode` receives this factory port; `main` retains Kilo. No merge or push.
- **In flight:** `feat/port-factory-harness-to-opencode-v2` in the unchanged bootstrap worktree
  `.kilo/worktrees/port-factory-harness-to-opencode-v2`. No board files edited by the builder.
- **Not complete:** security adapter implemented but not verified; container port, native
  runtime validation and independent review remain. This is not a security-complete or merge-ready port.
- **BOARD-116 verification:** Verification limited to file review because this was a low-risk visual/static change.
  Zero verification commands; no browser/runtime checks, builds or tests.
- **Earlier migration verification:** `python3 .opencode/skills/git-worktree/scripts/test_env.py`
  → exit 0, `all checks passed`; not rerun for BOARD-116.
- **Security check:** `node --test .opencode/plugins/factory-guard/guard.test.mjs` exited 1:
  two fixture tests hit `EACCES` creating directories under `/tmp/opencode`; policy/runtime merge
  test passed. No retry, dependency install or alternate fixture path attempted.
- **Next action:** human reviews the BOARD-116 task commit; parent approved all 12 file diffs
  and authorized a local docs-only commit through the existing Kilo bootstrap guard.
  BOARD-114 remains blocked and
  not merge-ready; it separately awaits user authorization of a
  writable fixture location or repair of temporary-directory access.
