# The factory page language moves to Tailwind

**Board:** BOARD-112
**Branch:** `feat/rebuild-factory-pages-as-a-split`

The first board console was one Python file with hand-written CSS. It was readable, but the
screen read as a stack of bordered white cards — the Bootstrap shape — and every new component
meant another block of bespoke CSS. The user asked for a modern factory page language and chose
Tailwind.

## Why a prebuilt stylesheet

The viewer must work offline and the harness must stay copyable into a project without a Node
runtime. The Play CDN breaks both. So Tailwind is an authoring tool only:

- `ui/src/app.css` holds the `@theme` tokens, the two `@font-face` rules and the `wb-` component
  classes.
- `npm --prefix .kilo/skills/board/ui run build` writes `static/board.css`.
- The stylesheet and the two variable fonts are committed. `board_serve.py` serves them from
  `/static/`, standard library only.

The cost is a rebuild after a class change and a generated file in the repo. A missing class fails
silently, so the QA capture is what proves the page still looks right.

## Why Geist, self-hosted

System fonts were the single biggest reason the page looked like a default framework. Geist Sans
and Geist Mono are SIL OFL, so the two variable woff2 files can live in the repo and load with no
network. The page is still offline, and the fonts are part of the design rather than a runtime
dependency on a CDN.

## The direction

Swiss-industrial: paper `#f4f2ec` and graphite `#0c0e10`, ink and hairlines instead of cards, a
strict grid, tabular mono data, and one signal red-orange used only where a decision is waiting.
The flow meter is one segmented instrument with five stops, and the worktrees move into a sticky
right rail, which also removes the bottom-section alignment bug from the previous layout.

## Approval

The component gallery at `/gallery` is the approval artefact. It renders the same `wb_` functions
the board will use, so the board screen cannot drift from what was approved.
