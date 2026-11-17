# The board console passes the unslop audit

BOARD-109 shipped the console. A sign-by-sign audit against
`.kilo/skills/unslop/references/signs.md` found four groups still in the CSS. The palette, type
scale, layout and controls were already deliberate, so the fix was polish mode: change only what
the audit named.

## What the audit found

- **Components — equal cards side by side.** Five bordered `.pipe` cards of the same shape and
  content for the lane counts.
- **Type — uppercase tracked labels.** `.pipe-name`, `.lane-name` and `.wt-table th` used
  `text-transform: uppercase` with positive tracking.
- **Type — negative letter spacing on small text.** `.wordmark`, `.panel-head h2` and
  `.panel-title` carried `-0.01em`.
- **Type — weights above the scale.** `650` and `700` appeared on the wordmark, headline, lane
  name, card id, card task and branch.

## What changed

The five stops became one `.flow` panel: a single hairline frame with five lane stops separated
by hairlines. The counts, proportional bar widths, click-to-filter and `aria-pressed` sync are the
same. Emphasis follows the data: the stop with the highest non-zero count gets `data-active` and
the only accent count and bar; the rest stay neutral, and a zero stop shows an empty track. On a
narrow screen the panel scrolls instead of stacking into the equal cards the audit rejected.

Labels are sentence case with normal tracking, small-text tracking is zero, and weights stop at
600. The approved token record in `docs/UI-UX.md` §6.1 now states the values that are actually in
the CSS, including the one-flow-instrument rule.
