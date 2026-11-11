# UI/UX critique — BOARD-109 Elevate the live board UI into a factory console

**Reviewed commit:** f36959a (round 1), re-checked at 83749c8 (round 2)
**Verdict round 1:** FAIL — one medium accessibility defect, three low/medium polish items.
**Verdict round 2:** PASS — every finding fixed and re-captured.

Captures: `artifacts/factory/qa/2026-11-11/BOARD-109/after/` (5 viewports × light/dark).

## Findings and resolution

| # | Severity | Rule | Expected | Actual (round 1) | Resolution (round 2) |
|---|---|---|---|---|---|
| F1 | medium | §2.15, U8 | Text ≥ 4.5:1 at rendered size | `--ink-faint #767e87` fell to 3.80:1 on bg, 4.11:1 on surface; light accent text `#2f6feb` 4.42:1 on white | `--ink-faint` → `#646c75` light, `#8b939c` dark; new `--accent-ink` `#1f5fd6` light / `#6f9dff` dark for accent text. Verified min ratios 4.61 light, 4.79 dark |
| F2 | low | M10, U8 | ≥ 44×44 touch targets on mobile | `.btn` and `.search-clear` 28px high at 390/320 | 44px min-height for app-bar, copy and more buttons, card and lane summaries at ≤480px |
| F3 | low–medium | M6, U8, U5 | Refresh preserves reading state | 10s full reload reset focus, keyboard selection and open cards | Auto-refresh now skips while a card is open, a filter is active, the tab is hidden, or focus is inside the content column |
| F4 | low | U7, rule 9 | Error names problem and next action | Banner said only "could not read the board: <exception>" | Banner now names the recovery step: check `--file`/`docs/BOARD.md` and the table format |
| F5 | medium (QA) | §2.15, U8 | Sticky lane header visible under the app bar | Lane headers pinned at a fixed 60px while the bar wrapped to ~166px at 320px | App-bar height is measured into `--appbar-h`; the bar is static and lane headers pin at 0 on mobile |

## What passed

- Rules 1–14 of `docs/UI-UX.md` §2: no gradient hero, operational copy, one accent plus semantic status colours, real type scale and measure, left axis, real data density, specific empty and error copy, functional single SVG mark, no pill-everywhere, no synthetic imagery, brief motion, spacing from the scale, visible 2px focus ring, no 320px overflow.
- Gallery conformance: accent `#2f6feb`/`#6f9dff`, system font with mono for ids/branches/paths, scale 11/13/15/20/28, spacing 4–48, radii 6/10, one shadow, 1360px shell. Chips use a deliberately small 4px radius; not significant.
- U1–U8: the outcome (what is active, pending, blocked) is the first line; the pipeline is the primary control; IDs and paths are the point in this tool; the view is read-only so no destructive action; empty and error copy name the next action.
- M1–M10: search semantics, no spinners, designed dark mode, keyboard shortcut and j/k navigation, no layout shift, content-shell alignment at 1440 and 1920.
- Density: high-density accordion with 36–44px rows, appropriate to scanning many rows.
- Unslop signs present: uppercase wide-tracked lane labels and sub-pixel negative tracking on small labels. Nothing else on the signs list is present.

## Limitations

The capture script does not click, type, or press keys, so expanded cards, filters, the theme toggle, keyboard navigation and the all-clear state are judged from source and the served HTML, not from interaction captures. No scrolled capture exists; the sticky-header finding is CSS geometry plus the rendered bar height.
