---
description: Run the QA and UI/UX review lane with Playwright and produce evidence
---

Run the QA lane and the UI/UX critique for a frontend row. Evidence, not assertions.
Spec: `docs/UI-UX.md` §3 and §5.

Follow `AGENTS.md` §A7: read the catalogue index, apply all relevant skills and required references,
and report skills used or that none matched. Follow §B4.2 and
`.opencode/skills/qa-review/SKILL.md` for Playwright capture and MCP investigation.

1. **Confirm the app runs.** Use the dev command from `docs/STACK.md`. If it does not start,
   report the blocker; do not fake a review.
2. **Capture and investigate with Playwright.** Run the existing `browser-review.mjs` for
   screenshots, console, page-error and network evidence; use Playwright MCP for actual interactions
   and DOM measurements per route and in-scope theme. Viewports: 390×844 (mobile),
   834×1112 (tablet), 1440×900 (desktop), 1920×1080 (wide), and 320×800 as the overflow floor.
   Record actual viewport and theme. Capture exit 0 is not a passing verdict. If the runner, MCP
   or any required measurement is unavailable, report the failure and hold the affected criterion;
   do not install or substitute tools without approval.
3. **Check the round ledger** — a row may go through at most 10 QA↔fix rounds. Round 10 is the
   last. If it still fails, move the row to `Blocked` with what was tried and the question for the
   human; do not open an eleventh round. Each round's
   review is done by a fresh reviewer who reads the ledger, not the previous reviewer's
   reasoning:

       python3 .opencode/skills/qa-review/scripts/ledger.py status --task-id BOARD-005

    The ledger lives at `<primary-checkout>/.factory-state/reviews/<task-id>-ledger.md`; update it
    only through `ledger.py`, never concurrently.
4. **Store reports and evidence** under
   `<primary-checkout>/artifacts/<scope>/qa/<YYYY-MM-DD>/<task-id>/`, outside the task worktree.
    QA writes `qa.md` and evidence; UI critique writes `ui.md`; builders write only in `builder/`.
    Reviewers leave shared artifacts uncommitted.
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
   The critique also runs the unslop pass: every sign in `.opencode/skills/unslop/references/signs.md`
   that the capture shows, with where it lives. The precedence rule for a disagreement is in
   `AGENTS.md` §B4.3.
7. **Validate each finding and take its fingerprint**:

       python3 .opencode/skills/qa-review/scripts/check-finding.py --body-file <finding.md> \
           --kind bug --priority medium --category functional --route /path

   Exit 0 prints the fingerprint on stdout. Record it in the original row's notes and local
   ledger. Return an in-task finding to the same builder and worktree; a repeated fingerprint
   blocks the original row. Only an independently approved defect gets a separate Fix task.
8. **Verdict**: a frontend row cannot leave `In Review` until QA and independent critique are
   green and the unslop audit is recorded. Gallery approval and accessibility gates remain
   mandatory. Any finding returns the row to `In Progress` with the finding restated. If round 10
   still fails, move the row to `Blocked` with what was tried and the question for the human; do
   not open an eleventh round.

Report in this order: what was done, what is proven, what is not done and why, next action.
