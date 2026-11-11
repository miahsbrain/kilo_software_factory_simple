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

## Interactive QA addendum — 2026-11-11

Requested target: commit `16ffa7c`, existing preview `http://127.0.0.1:15181`. This addendum does not reverify the earlier command results or change the verdict.

Loaded the built-in `browser` skill and discovered exact tools with Code Mode `search`. The first browser operation was `tools.browser.tabs.list()`; it returned:

```text
[browser.disconnected] No desktop browser is connected to this session. Open this session in the desktop app and wait for it to connect. Then call browser.tabs.list({}). Repeating browser actions while disconnected will not help.
```

This is a tool error, not a shell command; no exit code was supplied. Reviewer session: `ses_e353521ebffe98nk7trQD9wqQK`. The parent's successful browser attachment does not establish attachment to this child session. No browser retries or alternate drivers were used.

| Requested interactive check | Result |
|---|---|
| Factory board visibility | Unverified: no tab could be listed/opened. |
| Project board visibility through project switch | Unverified: no interactive page access. |
| Configured 60s schedule and elapsed automatic refresh | Unverified: no live control or timer observation. |
| Pause, then Refresh now causes actual reload | Unverified: no clicks or navigation observed. |
| Filters retained across refresh | Unverified: no controls exercised. |
| Theme toggles and keyboard behavior | Unverified: no controls exercised. |
| Console and network errors | Unverified: no page logs available; absence of errors is not claimed. |

No screenshots or new canonical artifacts were produced. No board/source/data mutation, capture retry, test/build command, installation, restart or commit was performed. Session moved to the assigned worktree before writing this addendum.

Recommendation: attach the desktop app to this reviewer session, or have the already attached parent perform the interactive checks with explicit evidence. Parent execution avoids a child-attachment dependency but is not an independent reviewer pass. Canonical capture remains blocked separately by the recorded Playwright dependency failure and is not waived. No proven product defect warrants a Fix row or criterion return to In Progress from this attempt; BOARD-117 remains verification-blocked, not merge-ready.

## Parent interactive observations — 2026-11-11 (not an independent pass)

User approved available built-in browser QA. The attached parent used tab
`tab_1515e945-56cb-4cd3-8052-b5e97be46e3b` at `http://127.0.0.1:15181`.
These are parent-reported observations, separate from the disconnected child review above;
this documentation checkpoint made no browser calls and does not change the verdict.

| Action / evidence | Observed result and limit |
|---|---|
| Snapshot depth 10, generation 3 | Separate harness 18-card and project 14-card panels, total 32; footer refresh 60s. Configured interval observed, not elapsed automatic scheduling. |
| Click Pause `refe1`, then evaluate | Resume label, `aria-pressed=true`, refresh 60, `timeOrigin=1794403699070.3`, boards harness/project. |
| Click Refresh now `refe4` while paused; loading true, then wait(load), evaluate generation 4 | `timeOrigin=1794403751072.6`, boards harness/project. Changed time origin proves an actual reload while paused. Pause resets after reload (existing behavior). |
| Press `/`, then evaluate | `activeElement=BODY`; keyboard shortcut not proven. |
| Fresh generation-4 snapshot; fill search `refe39` with `BOARD-117` | URL `?q=BOARD-117`, input `BOARD-117`. `visibleCards` queried with `.card` returned `[]`; selector is unreliable, so no filtering pass is claimed. |
| Click Refresh now `refe33` | `[browser.operation_failed] browser.click failed. UnknownVizError`; tool supplied no exit code. Subsequent `tabs.list` confirmed the same URL, generation 4, loading false. No retry. Filter retention across refresh not proven. |

Filter retention, elapsed timer, keyboard, themes and responsiveness remain unchecked; visual,
unslop and gallery review are not complete. No product defect was proven. Canonical capture
still lacks Playwright; no installation, source change, restart or alternate driver. Main
15180 unchanged; preview 15181 only. BOARD-118 approved redesign gallery remains queued,
not implemented. User decision needed on whether to retry built-in checks after the desktop
error is resolved; canonical tooling approval/location remains separately required. Not merge-ready.
