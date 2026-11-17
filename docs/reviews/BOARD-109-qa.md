# QA review — BOARD-109 Elevate the live board UI into a factory console

**Reviewed commit:** f36959a (branch `feat/elevate-the-live-board-ui-into-a-factory-console`)
**Verdict round 1:** FAIL
**Verdict round 2 (83749c8):** PASS — both findings fixed. See "Round 2" at the end.
**Command:** `node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:15181 --route / --scope factory --task-id BOARD-109 --scheme both --label after --compare /workspaces/yt/artifacts/factory/qa/2026-11-11/BOARD-109`
**Result:** capture completed, exit 0. 5 viewports × 2 schemes: 0 console errors, 0 page errors, 0 network failures, no horizontal overflow (320px included). Two findings, both accessibility/layout.

Round: 1 of 3 (`docs/reviews/BOARD-109-ledger.md`, rounds used 0 before this round).

## Acceptance criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Sticky app bar: brand, live-updated indicator, auto-refresh pause/resume, refresh now, theme toggle system/light/dark persisted | PASS | Capture `after/root/1440x900/light/1440x900-light.png` shows brand, "updated 12:05:27 AM · live", Pause, Refresh now, System, Comfortable. CSS/JS: `board_serve.py:264-267` (sticky bar), `:1353-1355` (live text), `:851-859` (pause/resume), `:860-862` (refresh now), `:791-797` + `:603-611` (three-state theme), `:512-527` (localStorage key `board-dashboard-state`, saved on click, applied on load at `:900`) |
| 2 | Theme toggle persisted across reload | UNVERIFIED | Persistence is implemented (`board_serve.py:512-527`, `:610`, `:900`) but the capture script does not click, so no reload-after-toggle evidence exists. Static reading only |
| 3 | Flow overview strip: five active lanes with counts | PASS | `ACTIVE_LANES` `board_serve.py:32`; `render_pipeline` `:1247-1262`; 5 `.pipe` buttons with `data-status-filter` in the served HTML; capture shows READY 0, IN PROGRESS 1, IN REVIEW 0, PENDING MERGE 0, BLOCKED 0 |
| 4 | Overview strip clickable to filter | UNVERIFIED | Handler exists `board_serve.py:783-789`; not exercised because the capture does not click |
| 5 | All-clear state | UNVERIFIED | Implemented `board_serve.py:1304-1314` ("All clear — nothing in flight", last merged id, date). Not reachable without mutating the board, which this review may not do |
| 6 | Toolbar: search (`/`), status/type/priority filters, density toggle, result count, clear, URL reflects state | UNVERIFIED | Markup `board_serve.py:1265-1290`, filters `:624-721`, URL write `:637-648`, density `:798-804`, `/` focus `:872-876`. All controls present in the served HTML (`#search`, `#type-filter`, `#priority-filter`, `#result-count`, `#reset`, `#density-toggle`); no interactive evidence |
| 7 | Lane stacks: sticky headers, status rail, counts | FAIL | Headers stick at a fixed `top: var(--appbar-h)` (`board_serve.py:392`, `:203`, `:494`) while the app bar wraps to ~133px at 390px and ~166px at 320px, so the header pins behind the bar. Finding 2. Desktop (1440px) is correct |
| 8 | Cards show id/task/type/priority/risk | PASS | `render_card` `board_serve.py:1089-1149`; rendered card in the served HTML (`data-card="BOARD-109"`); capture shows `BOARD-109`, task, `Feature`, `P2`, `medium` risk chip |
| 9 | Cards expand to a parsed Notes checklist with proof lines | UNVERIFIED (interaction) / PASS (rendering) | Server renders the expanded body: `parse_notes` `:945-972`, `render_notes` `:975-1009`, `split_proof` `:937-942`. The served HTML contains 62 `.note-check` items (53 done) and 41 `.note.note-proof` lines for the merged cards. Expand-on-click is native `<details>`; not exercised because the capture does not click |
| 10 | Worktrees as a table (branch, path, ahead/behind, dirty, main) | PASS | `render_worktrees` `board_serve.py:1068-1080`, `render_worktree` `:1040-1065`; served HTML row for the feature branch: branch, `clean`, ahead 2, behind 0, path; main row carries `main` + `dirty`. The panel is collapsed by default (`<details class="panel wt-panel shell">` with no `open`), so the table is not visible in the capture until expanded |
| 11 | Every empty lane has a specific empty state | PASS (static) | `EMPTY_TEXT` `board_serve.py:47-56`; each lane renders `<p class="empty" data-empty-default="...">`; 8 lane defaults found in the served HTML ("Nothing ready. Add a row with board.py add.", "Nothing in review.", …). Visible only after expanding an empty lane, which the capture does not do |
| 12 | Keyboard j/k/Enter/Esc | UNVERIFIED | Handlers `board_serve.py:867-892` (`/`, Esc, j/k, Enter); the capture script does not press keys |
| 13 | Visible focus ring | PASS (static) | `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }` `board_serve.py:257`; selected card also gets a 2px outline `:425` |
| 14 | Targets ≥ 24×24 CSS px | PASS (computed from CSS) | `.btn` min-height 28px `:278`; `.search-clear` 28×28 `:327`; `.copy` min-height 24px `:447`; `.more` 28px `:466`; lane summary 44px `:394`; card summary 36px `:416`; selects/search 32px `:317`,`:333`; pipeline 60px `:303` |
| 15 | Read-only guarantee: `board.py` and worktree scripts unchanged; `/`, `/api/board`, `/api/worktrees`, `/health` keep their shape | PASS | `git diff main --name-only` touches `.kilo/skills/board/SKILL.md`, `board_serve.py`, `docs/HANDOVER.md`, `docs/UI-UX.md`, two changelog files — `board.py` and `worktree.py` diff empty. `curl /health` → 200 `{"ok": true}`; `/api/board` → 200, keys `boards`, `generated_at`, board keys `counts,error,label,lanes,path,rows`, row keys unchanged from main (`board_serve.py` on `main` has the same shape); `/api/worktrees` → 200 array of `path,branch,sha,ahead,behind,dirty,main`. `board_serve.py` has no filesystem write path (only `self.wfile.write` and `webbrowser.open` under `--open`) |
| 16 | No console errors, no page errors, no horizontal overflow at 320px, light and dark | PASS | `artifacts/factory/qa/2026-11-11/BOARD-109/summary.json`: all 10 viewport/scheme results `console_error_count 0`, `page_error_count 0`, `network_failure_count 0`, `horizontal_overflow false`. All `console.log`/`page-errors.log` files are 0 bytes; `network.json` is `[]` |

## Findings

| # | Severity | Expected | Actual | Repro | Evidence |
|---|---|---|---|---|---|
| 1 | medium (P2) | Meta/empty/footer/proof text ≥ 4.5:1 in both schemes (`docs/UI-UX.md` §2 rule 15, §5) | `--ink-faint` measures 3.80:1 on `--bg`, 4.11:1 on `--surface`, 3.98:1 on `--surface-2`; dark 4.32:1 on `--surface-2`, 3.94:1 on `--accent-soft`. Used at 11px for lane descriptions (`:408`), empty states (`:469`), footer (`:470`), paths (`:370`), table headers (`:362`), card keys (`:443`), proof lines (`:460-461`), `kbd` (`:323`) | Load `/`, read a lane description / footer / an expanded empty lane; switch to Dark and expand a merged card | `board_serve.py:193`, `:219`; capture `after/root/1440x900/{light,dark}/1440x900-*.png` |
| 2 | medium (P2) | Sticky lane header stays visible under the app bar at every viewport | `top: var(--appbar-h)` is a fixed 60px (56px ≤480px) but the app bar is intrinsic and wraps to ~133px at 390px and ~166px at 320px; lane headers (`z-index: 5`) pin behind the opaque app bar (`z-index: 30`) | Load `/` at 390×844 or 320×800, scroll to a lane header; it is covered by the app bar | `board_serve.py:203`, `:264-268`, `:392`, `:494`; captures `after/root/390x844/light/390x844-light.png`, `after/root/320x800/light/320x800-light.png`; desktop `1440x900` is correct at 60px |

Finding 2 is derived from the CSS and the rendered app-bar height in the captures; the capture script does not scroll, so there is no scrolled screenshot. It is not claimed as an interactive capture.

## Product critique (`docs/UI-UX.md` §3)

- U1/U2: The console serves one user — the orchestrator or human checking what is in flight and what needs a decision. The outcome (what is active, pending, blocked) is the first line of the page. PASS.
- U3: Primary action is the lane filter / search; the view is read-only by design, so "one dominant action" is not a button but the pipeline strip. Acceptable.
- U4: Rows show real IDs and worktree paths, which are the point in this tool; each card names the task in words. PASS.
- U5: The board is read fresh per request; the app bar states the refresh interval and offers Pause. PASS.
- U6: No destructive action exists (read-only). N/A.
- U7: Empty states are specific ("Nothing ready. Add a row with board.py add."), and a read failure renders a banner (`board_serve.py:1301-1303`). PASS on copy; the banner path is unexercised.
- U8: Keyboard handlers, focus ring, 24px targets, no 320px overflow, dark mode, `sr-only` labels on search/selects, `aria-pressed` on pipeline and density. Partial failure: sticky headers on narrow viewports (finding 2) and low-contrast meta text (finding 1).
- M1–M4: `type="search"` + `autocomplete="off"`; no form validation needed; no spinner or skeleton because the page is server-rendered; the reload is explicit and pausable. PASS.
- M5: One system sans + a mono for IDs/paths, documented scale (`--t-xs`…`--t-xl`). PASS.
- M6: `/`, `j`/`k`, `Enter`, `Esc` implemented. PASS static.
- M7: Both themes are token-designed, not an inverted filter. PASS.
- M8/M9: Copy names the job ("Factory Board", "what is in flight right now", "Paused", "Refresh now"); no layout shift observed. PASS.
- M10: 24px review floor met; touch-primary 44px is met only for lane summaries and pipeline tiles, not the 28px app-bar buttons — accepted for a desktop-first console.
- Density: high-density accordion with 36–44px rows for scanning, appropriate to the task.
- Reuse: `board_serve.py` extends the existing read-only viewer (same endpoints, same `board.py`/`worktree.py` helpers loaded by path); no duplicate board parser or worktree reader. PASS.

## Not done

- Interactive states were not exercised: the capture script does not click, hover, type, or press keys, and the review may not drive a browser another way. Filters, theme/density toggles, card expansion, keyboard navigation, and the all-clear state are verified only by static reading of `board_serve.py`, not by interaction.
- No scrolled capture exists, so finding 2 rests on CSS geometry plus the visible app-bar height in the 390/320 screenshots.
- Finding files could not be written to `artifacts/factory/qa/2026-11-11/BOARD-109/` (edit permission is denied in the main checkout); their text is in this report and in the final message.
- `docs/BOARD.md` was not touched and no board rows were created, per the task.

## Round 2 — fixes and re-verification

**Fixed at commit:** 83749c8 `♿ [fix] board: meet contrast, sticky and touch-target review findings`

- Finding 1 (contrast): `--ink-faint` raised to `#646c75` light and `#8b939c` dark; new `--accent-ink` `#1f5fd6` light and `#6f9dff` dark for accent text. Minimum ratio 4.61:1 light, 4.79:1 dark.
- Finding 2 (sticky offset): the real app-bar height is measured into `--appbar-h` on load, resize and via `ResizeObserver`; at ≤480px the bar is static and lane headers pin at `top: 0`.
- Also fixed from the UI critique: 44px mobile targets, auto-refresh skips while reading, error banner names the recovery step.

**Re-capture:** `artifacts/factory/qa/2026-11-11/BOARD-109/after/` — 5 viewports × 2 schemes, `console_error_count` 0, `page_error_count` 0, `network_failure_count` 0, `horizontal_overflow_check_passed` true everywhere.

Verified criteria that were PASS stay PASS (cards, worktrees table, empty states, read-only endpoints). The criteria previously marked UNVERIFIED remain unverified interactively: the capture script cannot click, type or press keys. They are implemented in source and are not claimed as interaction-passed.
