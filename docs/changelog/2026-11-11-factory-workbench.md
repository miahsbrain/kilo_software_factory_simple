# 2026-11-11 — The factory workbench language

BOARD-112 splits into two chunks. This chunk settles the visual language and proves it in a
gallery; the next chunk rebuilds the board screen from the same functions.

The direction is a machine-shop workbench: paper and graphite surfaces, one safety-orange signal,
and no other saturated colour. The two moments are the segmented flow meter and the parsed
acceptance checklist. The signature is the single orange meter segment plus the orange rail on
the active lane.

The `wb-` functions live in `board_serve.py` because the viewer is one standard-library script
and the gallery must import the exact modules the board will use. `wb_card` calls the existing
`render_notes()` and escaping rather than carrying a second parser. `GET /` still renders through
its current functions; only the colour tokens and one footer link changed.

The gallery fixtures cover a zero lane, a peak lane, an open lane with two cards, an expanded card
with a parsed checklist and a fingerprint, a three-row worktree rail, chips and a specific empty
state. Tokens are shown as swatches, type steps, spacing bars and radius boxes so the language is
inspectable rather than implied.
