# The unslop skill, adopted and merged into the QA lane

**Board:** BOARD-105
**Branch:** `feat/add-the-unslop-skill-and-merge`
**Date:** 2026-11-10

## What

The unslop skill by Damir Sokolovsky is adopted as a standalone skill at
`.kilo/skills/unslop/`, and its signs list is merged into the QA lane as the extended checklist
of the anti-slop rules.

## Why

The 15 anti-slop rules in `AGENTS.md` §B4.3 are a floor. They catch the loud tells — the purple
gradient hero, the three identical stat cards, the pill for everything. They do not catch the
quiet ones: `mt-[13px]`, a mixed number format, an icon nudged off its column, a badge that
reads `New ✨`.

The upstream skill carries a full sign-by-sign checklist, grouped by surface, type, icons,
spacing, copy, components, heroes, visuals, motion and the template look. That list is the
value, and it belongs in the review lanes where a verdict is actually reached — not only in a
skill a builder has to remember to open.

So the skill comes across whole, and its checker is merged into the lanes that judge a screen.

## How it is merged

- `AGENTS.md` §B4.3 states the precedence rule once, next to the 15 rules: where the unslop
  skill and this repository's rules disagree, this repository's rules win. The skill is guidance;
  the rules are the standard.
- `.kilo/skills/qa-review/SKILL.md` §4 adds the unslop pass to "Judge the evidence": go through
  the signs list against the capture and report every sign that is present, with where it lives.
  One paragraph and the pointer — the list is not pasted into the file.
- `.kilo/agent/ui-critic.md` adds the same pass to "What to do", right after the 15 rules, and
  an `## Unslop signs` table to the review report it writes.
- `docs/UI-UX.md` §2.1 carries a short subsection that points at the signs list and references
  the precedence rule instead of restating it.

Every other file references the rule in `AGENTS.md` §B4.3 rather than repeating it.

## The adaptations

The upstream text is kept as intact as the decisions allow. Four things changed.

**The story video is gone.** It needs ffmpeg, it produces a marketing artifact, and the factory
has no use for either. The whole "Story video" section is deleted from the copied `SKILL.md`, and
step 8 of "Run it" with it. `scripts/story.mjs` does not come across. `scripts/snapshot.mjs`
does, because a live URL with no local source is a real case the QA capture script cannot cover.

**Image generation is gone.** The Visuals pass stays as guidance, but every instruction to
generate an image is removed from `SKILL.md`, `references/visuals.md` and
`references/effects.md`. The adapted text says: build the visual in code. An image can be
reviewed — the model can be shown one and judge it — but it is never generated here. The
upstream "Generate it" section becomes "Build it", and the "Prompt recipe" becomes "The scene in
code".

**The direction defers to the UI gate.** The upstream skill sets its own direction and stops.
Here the direction is confirmed with the user like any other approval, and the component
factory and the gallery the user approved remain the reference for the visual language. The
skill does not replace the gate.

**The evidence comes from this repo's capture path.** `SKILL.md` now points at
`node .kilo/skills/qa-review/scripts/browser-review.mjs`, which writes into
`artifacts/<scope>/qa/<date>/<task-id>/`, and keeps the skill's own `snapshot.mjs` for the one
case that script cannot cover.

`snapshot.mjs` itself was rewritten to match `browser-review.mjs`: the project's own Playwright
first, then the global install the devcontainer provides; the browser binary is the first of
`--chromium`, `$PLAYWRIGHT_CHROMIUM_PATH`, the browser Playwright downloaded, and the system
chromium. When none is found it exits 2 and prints the places it searched. It never installs a
browser and never falls back to another driver.

## The licence

The upstream skill is CC BY 4.0 by Damir Sokolovsky ([@heydamir]). The credit line — "Part of
unslop by Damir Sokolovsky (@heydamir), CC BY 4.0. Keep this credit in copies and adaptations."
— is present in every copied `.md` and `.html` file, and the attribution is recorded in
`docs/HANDOVER.md` where the memory map lives.

`docs/UI-UX.md` is created from `templates/project/docs/UI-UX.md`, with §2.1 added. The file was
referenced by `AGENTS.md`, the qa-review and ui-critic agents, the frontend and mobile builders
and the scope rules, and it did not exist in this repository.
