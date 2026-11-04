# QA — BOARD-102 compact accordion board viewer

**Date:** 2026-11-04
**Branch:** `feat/compact-accordion-redesign-of-the-live`
**Verdict:** PASS (after two fix rounds)

## Acceptance criteria

| Criterion | Proof |
|---|---|
| Lanes render as a vertical accordion, one column; no horizontal scrolling | `artifacts/factory/qa/2026-11-04/BOARD-102/round2/root/1440x900/light/full.png`; `horizontal_overflow_check_passed: true` at all five viewports |
| Backlog, Merged, Dropped collapsed by default; active lanes open | `board_serve.py` `lane_open_by_default`; a lane with no cards is collapsed, the Merged lane with 11 cards is folded in the capture |
| Cards are compact rows; click expands blocked-by, worktree, fingerprint, notes | the capture shows one-line rows; browser check: card `open: true`, `.card-detail` height > 0 after a reload |
| Merged shows the 10 most recent rows, with a show-all control | the capture shows `Show all 11`; browser check: `.card.extra` display `none` → `block` |
| Open/closed lanes and expanded cards persist in localStorage | browser check: state written on click and applied after a reload (`laneOpen: false`, `cardOpen: true`) |
| Filter still hides non-matching cards | the filter code path is unchanged in behaviour; the capture loads with an empty filter and all rows visible |
| Board file, board.py and worktree scripts unchanged | `git diff main --stat`: only `.kilo/skills/board/scripts/board_serve.py` and `docs/` |

## Findings and rounds

Round 0 raised four findings: 320px horizontal overflow, a clipped header count line, empty lanes
open by default, and a favicon 404. All four were fixed in commit `4f79977`, with the gutter
correction in `8bcf3b3`. Round 2 came back clean at every viewport.

## Limits

- Only the light scheme was captured; the dark scheme was not captured.
- The filter's hide behaviour was not exercised with a live query in the browser.
- The reviewer did not drive a real board change through the viewer while it was open.
