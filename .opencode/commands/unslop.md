---
description: Run the unslop pass on a screen — direction, sign audit, nine passes, checklist — and record the audit for the row
---

Run the unslop skill on a screen. This command is a shortcut for the procedure in
`.opencode/skills/unslop/SKILL.md`; the rules in `AGENTS.md` §B4.2, §B4.3 and `docs/UI-UX.md` §2.1
are the contract.

**Load the discoverable `unslop` skill**, or read it by path:
`.opencode/skills/unslop/SKILL.md`, `.opencode/skills/unslop/references/signs.md`, and
`.opencode/skills/unslop/references/tokens.md` for the exact values of each pass.

**When it runs.** On every UI change, alongside the QA capture — never instead of it. A UI row
cannot leave `In Review` until the audit is recorded (`AGENTS.md` §B4.2).

1. **Look at the screen.** Apply the catalogue selection/reporting rule in `AGENTS.md` §A7.
   Load `browser` first and use only OpenCode's built-in browser for UI verification/review
   under §B4.2 and the QA skill, including live URLs. Use interactions, screenshots, DOM
   measurements, console and network observations; no Playwright, browser MCP alternatives,
   `browser-review.mjs` or snapshot-script fallback.
   Store evidence under `artifacts/<scope>/qa/<date>/<task-id>/` with route, viewport, theme,
   steps, expected and observed results. Use returned server-local screenshot/`files.get` paths,
   not assumed shared desktop paths. Hold unavailable access/measurements and report the limit.
   Gallery approval, independent review, accessibility and unslop gates remain mandatory.
2. **Audit.** Go through `.opencode/skills/unslop/references/signs.md` group by group and list every sign found, one
   line each, with where it lives. The list is long; work through it in groups rather than
   pasting it.
3. **Decide the mode.** Heavy slop → the full process. Light slop → polish mode: fix only what
   the audit found and take the direction from the existing brand. No slop → say so plainly,
   suggest two or three small refinements with exact values, and stop.
4. **Set the direction and stop.** Write the five lines — product, character, world, moments,
   signature — and show the audit and the direction to the user. Wait for the answer before
   editing; changing the direction later means redoing everything. The approved component
   gallery and the decision sheet's visual language stay the reference (`AGENTS.md` §A7).
5. **Nine passes, in order.** Spacing, colour, icons, copy, type, layout, details, visuals,
   motion. Finish a pass across the whole screen before the next. Render to check at most three
   times.
6. **Check.** Run the checklist at the end of the skill file, render again, and compare against
   the audit list. Anything still on the list gets fixed.
 7. **Record the audit** in `ui.md` at
    `<primary-checkout>/artifacts/<scope>/qa/<YYYY-MM-DD>/<task-id>/`: the direction, the sign-group
    audit, a line per pass, the checklist result, and a PASS/FAIL verdict. A row with no recorded
    audit stays `In Review`.
8. **File the findings.** Write each finding as expected-vs-actual with the screenshot or
   `file:line` that proves it, validate it, and take its fingerprint:

       python3 .opencode/skills/qa-review/scripts/check-finding.py --body-file <finding.md> \
           --kind ux --priority medium --category visual --route /path

   The orchestrator creates one `Fix` row per finding with the script, with the fingerprint, so a
   repeat finding escalates the existing row instead of opening a second one.
9. **Verdict.** A UI row leaves `In Review` only when the QA lane is green, the UI/UX critique
   is green, and this audit is recorded.

Report in this order: what was done, what is proven, what is not done and why, next action.
