# UI And UX

All gallery QA and critique below are conditional: check `worktree.py reviews status` before delegation and in the specialist. Run only enabled scopes, use existing evidence only for critique with QA off, and use manual review if policy is invalid. At completion link the manual checklist for skipped scopes even without a blocker.

Record the project's actual user, task, product character, visual references, and chosen styling system here as they become known. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Do not assume preservation or inherit the factory board's visual style.

Default to shadcn/ui with Tailwind for compatible web apps; honor an approved alternative. Record the actual theme/token source and component location here. Before adding a primitive, inspect `components.json` if present, resolve the app's aliases and verify an export and a consuming import. Use that module, not a presumed shadcn import path. If missing, obtain authorization before installation or generation.

Use shared spacing, typography, semantic color, radius and elevation tokens. Present the initial component gallery and run focused QA on relevant states. Fix and recheck before composing screens from the same components; no gallery per screen. For new applications and user-facing features, present the complete flow for approval before backend/API implementation. Label fixtures clearly; backend-only maintenance needs no unrelated frontend work.

Design deliberate hierarchy, useful density, specific content, and responsive composition. Preserve keyboard access, visible focus, accessible names, contrast, and usable targets. Avoid generic dashboard templates and decorative noise.

Use the existing `browser-review.mjs` capture through `.kilo/skills/qa-review/SKILL.md`. Share evidence with `ui-critic`. Focus on meaningful defects, consolidate findings once, then have the builder fix and recheck; reviewers do not edit source. Keep raw evidence and report limitations. A proven harmless development-only missing favicon is nonblocking; do not ignore auth, script, or API failures.

When capture is authorized, run `browser-review.mjs` from the assigned source worktree. Its Git working directory, not `--project` or the script location, selects the `artifacts/` root. Keep generated fixtures in `artifacts/tmp/tests/` and scratch scripts in `artifacts/scripts/`; bootstrap copies maintained `.kilo/` tools, never evidence.

The factory disables Playwright MCP. Its output directory does not constrain explicit screenshot, snapshot or log filenames. Use a live read-only inspection without saving, or the confined runner for saved browser evidence. Do not use an external tool as a capture fallback. This default is not a system-wide sandbox or a migration of existing installs.

Project direction and approved styling choices: TBD.
