---
description: Run the QA and UI/UX review lane with Playwright and produce evidence
---

Run the QA lane and the UI/UX critique for a frontend row. Evidence, not assertions.
Spec: `docs/UI-UX.md` §3 and §5.

1. **Confirm the app runs.** Use the dev command from `docs/STACK.md`. If it does not start,
   report the blocker; do not fake a review.
2. **Capture with the script** — it drives the project's own Playwright and writes a full-page
   screenshot, `console.log`, `page-errors.log`, and `network.json` per route per viewport, plus a
   `summary.json` with the counts and the overflow result:

       node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url <url> --route /path \
           --artifact-dir apps/<scope>/artifacts/qa/<date>/<task-id> --project apps/<scope>

   Viewports: 390×844 (mobile), 834×1112 (tablet), 1440×900 (desktop), 1920×1080 (wide), and
   320×800 as the overflow floor.
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
5. **UI/UX critique** against the 15 anti-slop rules in `docs/UI-UX.md` §2, **and** the
   user-centred (U1–U8) and modern (M1–M10) criteria in §3. Each finding names the rule, the
   screenshot or `file:line` that proves it, and the fix. A screen that passes §2 and fails §3
   is still a FAIL.
6. **Verdict**: a frontend row cannot leave `In Review` until both QA and the critique are
   green. Any finding returns the row to `In Progress` with the finding restated.

Report in this order: what was done, what is proven, what is not done and why, next action.
