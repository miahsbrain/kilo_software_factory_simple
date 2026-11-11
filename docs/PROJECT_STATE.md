# PROJECT STATE — software factory

## Current session — BOARD-118 gallery checkpoint blocked (2026-11-11)

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
