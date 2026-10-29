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
           --scope <scope> --task-id <task-id> --project apps/<scope>

   The script computes the canonical artifact path itself — `artifacts/<scope>/qa/<date>/<task-id>/`
   in the **main checkout** — so no agent has to remember it.

   Viewports: 390×844 (mobile), 834×1112 (tablet), 1440×900 (desktop), 1920×1080 (wide), and
   320×800 as the overflow floor.

   **The script is the only way to capture UI evidence.** Ad-hoc `chromium`, `npx playwright
   screenshot`, `curl`-and-guess, or any other browser command run from bash is not acceptable
   evidence for a UI review. If the script cannot do something the review needs, extend the
   script — do not work around it with another tool.

   Extra flags: `--scheme light|dark|both`, `--component <css-selector>` (repeatable),
   `--compare <dir>` (before | after sheet), `--label <slug>` (names the round's capture),
   `--chromium <path>` (fallback binary over CDP when the project has no Playwright).
3. **Check the round ledger** — a row goes through at most 3 QA↔fix rounds, and each round's
   review is done by a fresh reviewer who reads the ledger, not the previous reviewer's
   reasoning:

       python3 .kilo/skills/qa-review/scripts/ledger.py status --task-id BOARD-005

   The ledger lives at `docs/reviews/<task-id>-ledger.md`.
4. **Store artifacts** under `artifacts/<scope>/qa/<YYYY-MM-DD>/<task-id>/` with a
   `notes.md` recording what was checked and expected vs actual. Commit `notes.md` and small
   component shots only. Review reports stay in `docs/reviews/<task-id>-qa.md` and
   `docs/reviews/<task-id>-ui.md` — those are documents, not artifacts.
5. **Check** and report findings as expected-vs-actual:
   - keyboard focus, visible focus ring, focus trapping in dialogs
   - contrast, accessible names on controls, alt text
   - tap targets ≥ 24×24 CSS px
   - console errors, unexpected 4xx/5xx
   - horizontal overflow at 320px
   - does the screen match the approved component gallery (tokens, states, density)
6. **UI/UX critique** against the 15 anti-slop rules in `docs/UI-UX.md` §2, **and** the
   user-centred (U1–U8) and modern (M1–M10) criteria in §3. Each finding names the rule, the
   screenshot or `file:line` that proves it, and the fix. A screen that passes §2 and fails §3
   is still a FAIL.
7. **Validate each finding and take its fingerprint**:

       python3 .kilo/skills/qa-review/scripts/check-finding.py --body-file <finding.md> \
           --kind bug --priority medium --category functional --route /path

   Exit 0 prints the fingerprint on stdout. Pass it to `board.py add --fingerprint`; a repeat
   fingerprint is refused and the existing row is escalated to `Blocked` instead.
8. **Verdict**: a frontend row cannot leave `In Review` until both QA and the critique are
   green. Any finding returns the row to `In Progress` with the finding restated. The round cap
   is 3 — when it is reached and the row still fails, the row moves to `Blocked` with a summary
   of what was tried and the question the human must answer.

Report in this order: what was done, what is proven, what is not done and why, next action.
