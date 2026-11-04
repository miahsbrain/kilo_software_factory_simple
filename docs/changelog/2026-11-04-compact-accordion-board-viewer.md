# Compact accordion board viewer

**Date:** 2026-11-04
**Branch:** `feat/compact-accordion-redesign-of-the-live`
**Board:** BOARD-102

## Why

The live board viewer was a horizontal kanban with eight lane columns and every lane always
open. The Merged lane grows with every merged row, so the page became a wide horizontal scroll
with no way to see the current work without scrolling past history. The board was functional and
hard to read.

## What changed

`.kilo/skills/board/scripts/board_serve.py` renders a vertical accordion instead of a lane grid.

- Lanes are native `<details>` sections in one column, ordered by what matters now: Ready,
  In Progress, In Review, Pending Merge, Blocked, then the historical Backlog, Merged, Dropped.
- Backlog, Merged and Dropped are collapsed on first load; the rest are open.
- A card is a compact row — ID, task, type, priority, risk — that expands in place to show
  blocked-by, worktree, fingerprint and the row's Notes text.
- The Merged lane shows the last 10 rows with a "Show all N" control for the rest.
- Fold state and expanded cards persist in `localStorage`, so the 10s auto-refresh does not
  undo what the reader folded.
- The filter still hides non-matching cards, shows `shown/total` per lane, and offers to open
  lanes that hold a match.
- The worktrees panel is collapsible and its summary names the non-main branches.

## Decisions

Approved with the user before the build:

| Decision | Choice |
|---|---|
| Layout | Vertical accordion, one column, no horizontal scrolling |
| Card density | Compact row, details on expand |
| Merged lane | Collapsed by default, last 10 shown, "Show all" for the rest |
| Fold state | Remembered in `localStorage` |

## Impact

Read-only viewer only. The board file, `board.py` and the worktree scripts are unchanged, the
server still writes nothing, and the JSON endpoints keep their shape.
