# QA review — BOARD-112 Rebuild factory pages as a split workbench console

**Reviewed commit:** `38eeb53` (branch `feat/rebuild-factory-pages-as-a-split`)
**Verdict:** PASS for all capture-verifiable criteria; interaction criteria source-verified, not click-verified.

Evidence: `artifacts/factory/qa/2026-11-11/BOARD-112/board-dashboard2/` (5 viewports × light/dark)
and `.../dashboard2/` for `/gallery`.

## Capture-verified

| Criterion | Verdict | Evidence |
|---|---|---|
| `/` renders the three-column shell at ≥1180px (240px sidebar, main, 320px rail) | PASS | 1440/1920 captures |
| Sidebar/filters collapse below 1180px; everything stacks at ≤640px; meter 3 + 2 | PASS | 834/390/320 captures |
| Dense rows: 44px lane summaries, 40px card rows | PASS | CSS + 1440 capture |
| Zero console errors, page errors, network failures | PASS | 10/10 captures |
| No horizontal overflow at 320/390/834/1440/1920, both schemes | PASS | `summary.json` |
| `/`, `/gallery`, `/health`, `/static/board.css`, both fonts 200; `/api/board`, `/api/worktrees` JSON | PASS | route checks |
| Read-only: `board.py`, `worktree.py`, `guard.py`, `docs/BOARD.md` unchanged; API builders byte-identical to `main` | PASS | `git diff main --name-status` |
| Merged preview and all eight lanes present | PASS | 1440 capture |

## Source-verified, not click-verified

The capture script cannot click, type or press keys. The following are confirmed in
`board_serve.py` source and were also exercised by the builder's own Playwright self-check
(reported, not an independent capture): sidebar/meter/toolbar filter sync with `aria-pressed`,
search and result count, reset visibility, `/` focus, `j`/`k`/`Enter`/`Esc`, theme cycle,
density toggle, URL state (`q`/`status`/`type`/`priority`/`density`), folds, parsed Notes,
branch copy, pause/resume.

## Findings

| # | Severity | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | low | Footer pluralises correctly | "12 cards across 1 boards" | Fixed: singular/plural helper in `build_html` |
| 2 | low | Every control ≥24×24 CSS px | `.wb-copy` was 20px high | Fixed: `min-height: 24px` |
| 3 | observation | Lane status filters reachable below 1180px | Sidebar nav hides; Type/Priority move to the toolbar, status stays on the meter stops | Accepted: the meter is the status control and remains visible |
