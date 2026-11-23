# UI And UX

Design for a named user doing a real task, with the product's own content and character. Make hierarchy, primary action, density, and responsive composition deliberate. Avoid interchangeable dashboards, decorative noise, and generic copy. Preserve accessibility. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction; do not assume preservation.

## Delivery

All gallery QA and critique below are conditional: check `worktree.py reviews status` before delegation and in the specialist. Run only enabled scopes, use existing evidence only for critique with QA off, and use manual review if policy is invalid. At completion, return an absolute workspace link to the validated central manual checklist for skipped scopes even without a blocker.

Default to shadcn/ui with Tailwind for compatible web apps; retain an approved alternative. Before proposing a primitive, trace a real screen import through the project's alias configuration to its exported component. For shadcn, check `components.json`, the actual UI directory and its exports; the registry name alone is not an import path. Report the module and caller, or the missing piece. Obtain authorization before installing dependencies or generating components. In the factory's Python-rendered board, trace rendering functions instead: `wb_row_card` uses `wb_card` in `.kilo/skills/board/scripts/board_serve.py`. This is reuse, not a shadcn installation.

Use the approved spacing, type, color-role, radius and elevation tokens. Present the initial component gallery with relevant interaction states and run focused QA. Fix meaningful findings and recheck before composing screens from those same components; do not require a gallery per screen. Label fixtures and incomplete integration. For new apps and user-facing features, obtain user approval of the complete flow before backend/API implementation. Backend-only maintenance needs no unrelated frontend work.

## Review

Use `.kilo/skills/qa-review/SKILL.md` and its existing capture script for shared screenshots, console/page errors, network evidence, and responsive overflow checks. Focus on actual acceptance criteria and relevant states, keyboard access, visible focus, accessible names, readable contrast, and usable targets.

When capture is authorized, run `browser-review.mjs` from the assigned source worktree. Resolve `python3 <qa scripts>/ledger.py artifact-root` there and keep captures, raw files, logs and scratch scripts beneath the returned primary control artifacts root. Bootstrap copies maintained `.kilo/` tools, never evidence.

The factory disables Playwright MCP. Its output directory does not constrain explicit screenshot, snapshot or log filenames. Use a live read-only inspection without saving, or the confined runner for saved browser evidence. Do not use an external tool as a capture fallback. This default is not a system-wide sandbox or a migration of existing installs.

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
