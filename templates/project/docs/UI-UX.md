# UI And UX

Record the project's actual user, task, product character, visual references, and chosen styling system here as they become known. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Do not assume preservation or inherit the factory board's visual style.

Default to shadcn/ui with Tailwind for compatible web apps; honor an approved alternative. Record the actual theme/token source and component location here. Before adding a primitive, inspect `components.json` if present, resolve the app's aliases and verify an export and a consuming import. Use that module, not a presumed shadcn import path. If missing, obtain authorization before installation or generation.

Use shared spacing, typography, semantic color, radius and elevation tokens. Present the initial component gallery and run focused QA on relevant states. Fix and recheck before composing screens from the same components; no gallery per screen. For new applications and user-facing features, present the complete flow for approval before backend/API implementation. Label fixtures clearly; backend-only maintenance needs no unrelated frontend work.

Design deliberate hierarchy, useful density, specific content, and responsive composition. Preserve keyboard access, visible focus, accessible names, contrast, and usable targets. Avoid generic dashboard templates and decorative noise.

Use the existing `browser-review.mjs` capture through `.kilo/skills/qa-review/SKILL.md`. Share evidence with `ui-critic`. Focus on meaningful defects, consolidate findings once, then have the builder fix and recheck; reviewers do not edit source. Keep raw evidence and report limitations. A proven harmless development-only missing favicon is nonblocking; do not ignore auth, script, or API failures.

Run capture from the assigned source repo/worktree. All generated review artifacts, images, Playwright output, reports and logs belong in its ignored `artifacts/`, not control-main, root, `/tmp` or external paths; ad-hoc review scripts go in `artifacts/scripts/`. Maintained `.kilo/` review tool source stays tracked and bootstrap copies tools, never evidence. Canonical source fixtures are distinct from generated fixture output, which uses `artifacts/tmp/tests/`. The QA skill defines contained overrides and symlink checks. For MCP saves, explicitly use `artifacts/...` filenames: `--output-dir` only controls automatically named output and is not a sandbox for arbitrary filenames or all browser-managed temp/cache files.

Project direction and approved styling choices: TBD.
