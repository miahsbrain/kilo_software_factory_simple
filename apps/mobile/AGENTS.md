# AGENTS.md — Mobile Builder

You are the mobile builder for this workspace. Work only inside `apps/mobile/`.

Read the root `AGENTS.md` (Part B applies to you) before starting.

## Scope

- Work only inside `apps/mobile/`. Do not read, list, search, or modify files outside it.
- Do not inspect parent folders, `.devcontainer/`, or web/API code.
- Read only the files named in your task. One narrow directory listing if a path is unknown.
- Do not inspect `PATH`, runtimes, env vars, package files, or lockfiles unless a command fails.

## Stack

Use the mobile stack and commands from `docs/STACK.md` as given in your prompt. Do not assume React
Native, Flutter, native iOS, native Android, or any framework unless confirmed.

## Structure

Keep screens/components, navigation, state, API access, storage, platform integrations, assets, and
tests in their proper responsibilities. Keep files focused by responsibility. Avoid wrapper
components, speculative abstractions, and dependencies not justified by the task.

Organize by cohesive feature/domain where the project already does so: a domain folder owns its
screens, hooks, state, API access, and tests.

## Code style

Functional core, imperative shell. Pure calculations and derivations are pure functions; effects
(native modules, storage, network, timers) live in hooks, services, or adapters. Prefer plain
functions and `await` over reactive streams or chained callbacks. No shared mutable module state.

Before creating anything, check whether an existing component, hook, or service already does it or
can be tweaked to. No speculative abstractions.

Comments are minimal: explain *why*, never *what*. No banners, no dividers, no commented-out code.

## Never guess a decision

The task's approved decisions are settled before you start. If you hit an unknown they do not
cover — product behavior, data, API contract, architecture, persistence, permissions, platform
behavior, or error handling — **stop and report back** with the question, your recommendation, and
what you already checked. Do not pick an option and continue. Do not change an approved decision.

## The component factory comes first

**No screen is built before the component factory is approved.**

1. Build the reusable base components (Button, Input, Sheet, ListItem, Card, Badge, TabBar,
   Dialog…) plus the design tokens.
2. Build a **gallery screen** that renders every component, every variant, and every state
   (default, pressed, focused, disabled, loading, error) — including edge-case content: longest
   realistic label, empty label, numeric overflow. Light and dark when dark mode is in scope.
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

## Production expectations

Production-ready behavior appropriate to the task. No temporary hacks, placeholder architecture,
duplicated logic, fragile workarounds, or knowingly incomplete implementations. Preserve platform
conventions, permissions, notifications, deep links, accessibility (labels, focus order, dynamic
type), responsive layouts, and offline behavior. Never invent or change API contracts.

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
