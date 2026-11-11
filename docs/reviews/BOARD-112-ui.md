# UI/UX review — BOARD-112 Rebuild factory pages as a split workbench console

**Reviewed commit:** `38eeb53`   **Verdict:** PASS after the docs reconciliation
**Evidence:** `artifacts/factory/qa/2026-11-11/BOARD-112/board-dashboard2/` and `.../dashboard2/`

## Gallery conformance

The board and `/gallery` render the same `wb_` functions. The earlier §6.2 table described the
paper/editorial iteration; the user then approved the dense dashboard direction, so the shipped
cool-neutral, 6/8/12-radius, one-soft-shadow, 32px-title language is now recorded in `§6.2`.
No screen diverges from the approved dashboard.

## §2 anti-slop (1–15)

1–15 pass. No gradient hero, no meaningless copy, no three identical stat cards (one KPI strip),
one accent, a real type scale, two radii families plus the panel, asymmetric three-column layout,
real data density with specific empty/error copy, functional icons, shapes not all pills, no
synthetic imagery, 150ms motion, spacing from the scale, contrast ≥4.5:1 and a visible focus ring.

## §3.1 user-centred

U1 outcome first (KPI strip) · U2 primary action clear (Refresh now, lane filters) · U3 ids and
paths are the point in this tool · U4 read-only, no destructive action · U5 reduced motion
respected · U6 keyboard-aware · U7 specific empty and error copy · U8 focus visible, targets ≥24px
after the copy-button fix.

## §3.2 modern

M1 search semantics · M2 no spinners · M3 designed dark mode · M4 keyboard `/` and `j`/`k` · M5 no
layout shift · M6 native scroll · M7 loading/error states · M8 no modal traps · M9 one accent ·
M10 touch targets (copy fixed).

## §3.3 density

Scanning density: 44px lane rows, 40px card rows, 240/320px rails; comfortable/compact toggle kept.

## Findings

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | medium | Docs described the earlier paper language | Fixed in `§6.2` |
| 2 | low | Footer plural | Fixed |
| 3 | low | Copy button 20px | Fixed to 24px |
| 4 | observation | Tablet folds the worktrees rail below the board (BOARD-104) | Known row, not re-filed |
| 5 | observation | "Factory board" appears as both wordmark and page title | Accepted brand+title convention |

**Verdict: PASS.** Distinct, dense, and useful; no §2 rule broken.
