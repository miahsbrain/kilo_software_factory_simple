---
description: Run the QA and UI/UX review lane with Playwright and produce evidence
---

Run the QA lane and the UI/UX critique for a frontend row. Evidence, not assertions.
Spec: `docs/UI-UX.md` §4.

1. **Confirm the app runs.** Use the dev command from `docs/STACK.md`. If it does not start,
   report the blocker; do not fake a review.
2. **Capture with Playwright** — full-page screenshot per route per viewport:
   - 390×844 (mobile), 834×1112 (tablet), 1440×900 (desktop), 1920×1080 (wide), and 320×800
     as the overflow floor.
   - Component screenshots for each changed component, at desktop and mobile.
   - Console errors and failed network requests during each flow.
3. **Store artifacts** under `apps/<scope>/artifacts/qa/<YYYY-MM-DD>/<task-id>/` with a
   `notes.md` recording what was checked and expected vs actual. Commit `notes.md` and small
   component shots only.
4. **Check** and report findings as expected-vs-actual:
   - keyboard focus, visible focus ring, focus trapping in dialogs
   - contrast, accessible names on controls, alt text
   - tap targets ≥ 24×24 CSS px
   - console errors, unexpected 4xx/5xx
   - horizontal overflow at 320px
   - does the screen match the approved component gallery (tokens, states, density)
5. **UI/UX critique** against the 15 anti-slop rules in `docs/UI-UX.md` §2. Each finding names
   the rule, the screenshot or `file:line` that proves it, and the fix.
6. **Verdict**: a frontend row cannot leave `In Review` until both QA and the critique are
   green. Any finding returns the row to `In Progress` with the finding restated.

Report in this order: what was done, what is proven, what is not done and why, next action.
