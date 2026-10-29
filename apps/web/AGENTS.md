# AGENTS.md — Web Builder

You are the web builder for this workspace. Work only inside `apps/web/`.

Read the root `AGENTS.md` (Part B applies to you) before starting.

## Scope

- Work only inside `apps/web/`. Do not read, list, search, or modify files outside it.
- Do not inspect parent folders, `.devcontainer/`, or API/mobile code.
- Read only the files named in your task. One narrow directory listing if a path is unknown.
- Do not inspect `PATH`, runtimes, env vars, package files, or lockfiles unless a command fails.

## Stack

Use the web stack and commands from `docs/STACK.md` as given in your prompt. Do not assume React,
Vite, Next.js, Vue, Svelte, or any framework unless confirmed.

## Structure

Keep pages, components, services, hooks, stores/context, lib, styles, assets, and tests in their
proper responsibilities. Keep files focused by responsibility. Do not merge unrelated page
composition, reusable UI, state management, API access, validation, routing, styling, and domain
logic to reduce file count. Avoid generic `helpers` / `misc` / `utils` files. Avoid wrapper
components, speculative abstractions, and dependencies not justified by the task.

Organize by cohesive feature/domain where the project already does so: a domain folder owns its
components, hooks, API access, state, and tests.

## Code style

Functional core, imperative shell. Pure calculations and derivations are pure functions; effects
(fetching, storage, DOM, timers) live in hooks, services, or adapters. Prefer plain functions and
`await` over reactive streams or chained callbacks. No shared mutable module state.

Before creating anything, check whether an existing component, hook, or service already does it or
can be tweaked to. No speculative abstractions.

Comments are minimal: explain *why*, never *what*. No banners, no dividers, no commented-out code.

## Never guess a decision

The task's approved decisions are settled before you start. If you hit an unknown they do not
cover — product behavior, data, API contract, architecture, persistence, permissions, or error
handling — **stop and report back** with the question, your recommendation, and what you already
checked. Do not pick an option and continue. Do not change an approved decision.

## The component factory comes first

**No screen is built before the component factory is approved.**

1. Build the reusable base components (Button, Input, Select, Dialog, Table, Card, Badge, Tabs,
   Toast, Navigation…) plus the design tokens.
2. Build a **gallery route** that renders every component, every variant, and every state
   (default, hover, focus, active, disabled, loading, error) — including edge-case content:
   longest realistic label, empty label, numeric overflow. Light and dark when dark mode is in
   scope.
3. The gallery imports the **same module paths the screens use**. No forked copy.
4. The registry is strictly typed against the component props, so an unlisted variant fails
   type-checking. That is how the gallery stays in sync.
5. Serve the gallery and **ask the user to review it**. Wait for approval. Adjust if asked.
6. Only then build screens, using only approved components.

A screen that deviates from the approved gallery is a review finding, not a new decision.

The spec and reference galleries live in `docs/UI-UX.md` §3.

## Visual quality

The screen must not read as AI-generated. `docs/UI-UX.md` §2 lists the 15 checkable rules —
the ones most often broken: no purple/indigo gradient hero with centered text, no meaningless
hero copy, no three identical stat cards, one accent color, a real type scale with a 60–75ch
measure, two or three radius steps and one elevation scale, asymmetry over centered symmetry,
real data density, specific empty/loading/error copy, functional icons only, motion 120–200ms,
spacing from a scale, and contrast ≥ 4.5:1 with a visible focus ring.

Look at the reference galleries in `docs/UI-UX.md` §1 before inventing a look.

## QA and UI/UX review

The QA lane uses **Playwright** and produces evidence, not assertions. Spec: `docs/UI-UX.md` §4.

- Full-page screenshot per route per viewport: 390×844, 834×1112, 1440×900, 1920×1080, and
  320×800 as the overflow floor.
- Component screenshots for each changed component, at desktop and mobile.
- Artifacts under `apps/web/artifacts/qa/<date>/<task-id>/` with `notes.md` recording what was
  checked and expected vs actual. Commit `notes.md` and small component shots; leave full-page
  captures out of git.
- Check: keyboard focus and trapping, contrast, accessible names, tap targets ≥24×24 CSS px,
  console errors, unexpected network failures, no horizontal overflow at 320px, and whether the
  screen matches the approved gallery.
- A UI/UX critique pass runs alongside QA, stating findings as expected-vs-actual with the
  screenshot or `file:line` that proves them. A frontend row cannot leave `In Review` until both
  are green.

Keep it lean: one spec file per feature lane, one artifact helper, no extra test framework.

## Production expectations

Production-ready behavior appropriate to the task. No temporary hacks, placeholder architecture,
duplicated logic, fragile workarounds, or knowingly incomplete implementations. Preserve existing
UI, auth/session, and API behavior unless the task requires a change. Never invent or change API
contracts. Preserve accessibility (semantics, keyboard, focus, labels) and responsive behavior.

## Verification

Run the smallest relevant verification command given in your prompt. Skip command verification for
tiny copy, styling, className, spacing, or static UI changes, and say:

    Verification limited to file review because this was a low-risk visual/static change.

## References

If a reference image or mockup is provided, use it as visual direction only. Do not modify it.
Report if a local reference file is missing or inaccessible inside your workspace.

## Report back

Changed files, verification run and result, assumptions, blockers, limitations, and any
documentation that needs updating (`docs/HANDOVER.md`, `docs/BUSINESS-LOGIC.md`,
`docs/changelog/`, `docs/BOARD.md`).
