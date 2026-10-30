# Close the build loop

**Date:** 2026-10-29
**Branch:** `chore/close-the-build-loop-iteration-rule`
**Board:** BOARD-007

## The three gaps this closes

The factory had every part of the requested pipeline but three of them were not actually closed.

### 1. The lanes were a pipeline, not a loop

`Build → QA → Review` existed, and findings became `Type: Fix` rows. But nothing said the original
row **waits** for its fix rows, that a fix runs the same lanes, or that the original row is
re-verified afterwards. So "the loop continues until it works" was implied, not enforced.

Now, in `AGENTS.md` §B4:

- A row cannot reach `Pending Merge` while any Fix row it spawned is open.
- Every Fix row runs the same three lanes. A fix is not trusted because it looks right.
- After the fixes merge, the original row is re-verified — the failed criterion must now pass and
  nothing around it may have regressed.
- A finding that repeats **three times** blocks the row. Three failures of the same kind means the
  approach is wrong, not the implementation.
- A red critical path — money, data loss, auth, security — blocks immediately and is never retried
  silently.
- The loop ends on the spec, not the diff.

### 2. "Reuse before creation" was unverifiable

The rule existed in `AGENTS.md` §B6 and in every builder agent. Nobody could check it, so nobody
could enforce it.

Now the analysis is reported. Every builder's report says what existing code covers the ground
(`file:line`), what it did about it (extended / used as-is / did not fit because…), and what is
new and why. For a Fix row it also names the existing function that carried the bug.

A **Feature** row carries a reuse acceptance criterion, so the question is answered at planning
time rather than discovered at review time. The Review lane treats a new function next to a
near-identical one as a finding — and a second source of truth for state that already exists.

### 3. "Modern and user-centred" was not a criterion anywhere

The 15 anti-slop rules stop a screen looking generated. Nothing stopped it being useless — a screen
could pass every rule and still be a bad product.

`docs/UI-UX.md` §3 now defines the standard as answerable questions, not preferences:

- **§3.1 User-centred, U1–U8** — who is this for and what are they doing; what outcome did they
  come for; is the primary action obvious; are they doing the organisation's work; is their time
  respected; are destructive actions reversible; do errors say what to do next; does it work
  keyboard-only, at 200% zoom, at 320px, and with screen-reader names.
- **§3.2 Modern, M1–M10** — current platform convention: real input types, inline validation,
  skeletons over spinners, optimistic feedback where predictable, one text face, keyboard
  shortcuts for power users, dark mode when the product needs it, copy that names the job, no
  layout shift, 44×44 touch targets.
- **§3.3 Density matches the task** — dense for scanning, spacious for reading, comfortable for
  data entry. A form laid out like a spreadsheet is a finding.

Both the QA reviewer and the UI critic are now required to answer these, and the verdict rule is
explicit: **a screen that passes §2 and fails §3 is still a FAIL.** Beautiful and useless is not
done.

## What did not change

The component factory gate was already correct and is untouched: reusable base components and
design tokens first, a gallery route that renders every component, variant, and state, the human
approves it, and only then do screens get built using only approved components. A screen that
deviates from the approved gallery remains a review finding, not a new decision.
