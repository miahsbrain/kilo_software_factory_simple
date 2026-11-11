# QA review — BOARD-117 Refresh project board discovery every minute

**Reviewed commit:** ccfc828245eda5d4b2405a72cdd3d4e12fa49b37   **Verdict:** FAIL (verification blocked)
**Command:** `python3 .opencode/skills/board/scripts/test_board_serve.py`
**Result:** Exit 0; 4 tests passed in 0.014s. Canonical browser capture failed before evidence capture. This is not a demonstrated application defect.

## Acceptance criteria

- [x] Extend existing discovery/payload and refresh controls without a second parser/state source — evidence: `git diff HEAD^ HEAD -- .opencode/skills/board/scripts/board_serve.py`; existing `build_payloads` now invokes `discover_boards` per request, existing `board_states` and controls retained.
- [x] Project boards appear/disappear after initialization, with separate tasks in HTML/JSON — evidence: regression command exit 0; `test_board_serve.py:58–80` cycles absent/present/absent/present under an ignored fixture project directory. This is fixture handler evidence, not an actual-browser check or proof of a separate git repository.
- [ ] Default 60-second scheduling, manual refresh while paused, explicit file selection — default/control markup and fixed-file behavior passed fixture assertions (`test_board_serve.py:82–111`); actual clicks and elapsed timer behavior remain unverified.
- [ ] Independent QA proves discovery/refresh, read-only behavior and unchanged endpoint shapes — fixture tests pass and assert `/api/board` keys and `/api/worktrees` response; browser evidence unavailable. No live boards or test data were edited.
- [ ] Decisions, handover, engineering log and local commit — reviewed SHA exists; documentation completeness was not checked before the environmental stop.

## Findings

| # | Severity | Expected | Actual | Repro | Evidence |
|---|---|---|---|---|---|
| — | Blocker | Canonical capture runs against preview | Playwright cannot be resolved | Run capture command below | Exit 2 and exact error below |

No product defect was proven. No validated finding or Fix row is proposed from the environment failure.

## Capture blocker

Command:

```sh
node .opencode/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:15181 --route / --scope factory --task-id BOARD-117 --project . --scheme both --date 2026-11-11
```

Exit code: **2**.

```text
browser-review: Playwright was not found in the project "/projects/miahsbrain/yt/.opencode/worktrees/refresh-project-board-discovery-every-minute" or in the global npm install. Searched the project directory and the global npm root (npm root -g, NODE_PATH, /usr/local/share/npm-global/lib/node_modules).
```

Meaning: the required evidence runner cannot resolve its browser automation dependency.

Recommendation: have the architect/user restore or explicitly provision the documented Playwright dependency, then authorize resuming QA. Provisioning changes the environment but preserves the required capture workflow; deferring provisioning keeps the environment untouched but leaves the merge gate closed. No installation, alternate browser driver, restart or workaround was attempted.

## Not done

- No canonical screenshots, console/page-error/network evidence, or overflow measurements were produced. Intended canonical directory: `/projects/miahsbrain/yt/artifacts/factory/qa/2026-11-11/BOARD-117/`.
- Built-in browser skill loaded, but no browser call was made after the fatal capture failure; availability is unknown, not reported as disconnected.
- Actual two-board UI, Pause/manual refresh, filter retention, 60-second elapsed scheduling, keyboard focus/dialog behavior, contrast, accessible names/alt text, target measurements, 200% zoom, 320px layout, happy/empty/loading/error states, and U1–U8/M1–M10/density critique remain unchecked. Source assertions do not prove interactions.
- Unslop audit and gallery conformance remain unchecked because there are no current captures to grade.
- Ledger status before review: 0 of 3 rounds used; no ledger write, board edit, source edit or commit made.

**Disposition:** keep BOARD-117 blocked on verification tooling rather than claim merge readiness. No criterion is a proven product failure requiring a Fix row or a build return yet; interactive/canonical QA must resume after the architect decides how to resolve the dependency blocker.
