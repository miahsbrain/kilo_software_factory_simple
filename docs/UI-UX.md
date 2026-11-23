# UI And UX

Design for a named user doing a real task, with the product's own content and character. Make hierarchy, primary action, density, and responsive composition deliberate. Avoid interchangeable dashboards, decorative noise, and generic copy. Preserve accessibility. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction; do not assume preservation.

## Delivery

Develop reusable components first with Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme. Choices are not limited to installed libraries; obtain authorization before new dependency installation. Reuse suitable components without preserving unwanted styling and cover relevant interaction/accessibility states. Present the initial component gallery and run focused QA. Have the builder fix meaningful issues and recheck before composing screens from those same components; do not require a new gallery for every screen. For new applications and user-facing features, present the frontend flow for user approval before backend/API implementation. Clearly label fixtures and incomplete integration. Backend-only maintenance needs no unrelated frontend work.

## Review

Use `.kilo/skills/qa-review/SKILL.md` and its existing capture script for shared screenshots, console/page errors, network evidence, and responsive overflow checks. Focus on actual acceptance criteria and relevant states, keyboard access, visible focus, accessible names, readable contrast, and usable targets.

Run capture from the assigned source repo/worktree. All generated review artifacts, images, Playwright output, reports and logs belong in its ignored `artifacts/`, not control-main, root, `/tmp` or external paths; ad-hoc review scripts go in `artifacts/scripts/`. Maintained `.kilo/` review tool source stays tracked and bootstrap copies tools, never evidence. Canonical source fixtures are distinct from generated fixture output, which uses `artifacts/tmp/tests/`. The QA skill defines contained overrides and symlink checks. For MCP saves, explicitly use `artifacts/...` filenames: `--output-dir` only controls automatically named output and is not a sandbox for arbitrary filenames or all browser-managed temp/cache files.

Run `ui-critic` against the same capture to evaluate hierarchy, usability, and product character without source changes. Consolidate findings once with QA results, apply agreed polish and meaningful bug fixes through the builder, then recheck. Preserve raw evidence. A proven harmless development-only missing favicon is nonblocking; auth, script, and API failures are not excused by that exception.

## Existing Factory Language

The board viewer remains a precise, dense industrial console for seeing work in flight and decisions waiting. Its existing Tailwind CSS v4 source is `.kilo/skills/board/ui/src/app.css`; committed CSS and self-hosted Geist fonts are served locally for offline operation. `/gallery` uses the same components as the board, not a separate implementation.

| Group | Existing values |
|---|---|
| Light | canvas `#f5f6f8`, surface `#ffffff`, ink `#0b0f14`, signal `#c2410c` |
| Dark | canvas `#0b0d10`, surface `#14171c`, ink `#eef0f3`, signal `#ff8a5b` |
| Type | Geist Sans for UI; Geist Mono for IDs, branches, paths, and counts; 11/12/13/15/20/32px |
| Spacing | 4/8/12/16/24/32/48/64px |
| Radius | 6px chip, 8px control, 12px panel |
| Effects | One soft card shadow; 150ms reduced-motion-aware transitions |

The existing shell uses sidebar/main/worktree columns at 1180px and above, adapts filters below that, and stacks at 640px and below. Signal red-orange emphasizes the meter and busiest lane; semantic colors convey status. This change does not redesign the board or alter its assets. Stylesheet authoring uses `npm --prefix .kilo/skills/board/ui run build` after approved class changes; it is not a required check for text-only work.
