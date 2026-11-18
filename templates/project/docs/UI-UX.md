# UI And UX

Record the project's actual user, task, product character, visual references, and chosen styling system here as they become known. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Do not assume preservation or inherit the factory board's visual style.

Develop reusable components first with Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme. Choices are not limited to installed libraries; obtain authorization before new dependency installation. Reuse suitable components without preserving unwanted styling and cover relevant interaction/accessibility states. Present the initial component gallery, ask whether the user wants an unslop pass, and run focused QA regardless. Have the builder fix meaningful issues and recheck before composing screens from those same components; do not require a new gallery for every screen. For new applications and user-facing features, present the frontend flow for user approval before backend/API implementation. Label fixtures clearly; never present mocked behavior as integrated. Backend-only maintenance does not need unrelated frontend work.

Design deliberate hierarchy, useful density, specific content, and responsive composition. Preserve keyboard access, visible focus, accessible names, contrast, and usable targets. Avoid generic dashboard templates and decorative noise.

Use the existing `browser-review.mjs` capture through `.kilo/skills/qa-review/SKILL.md`. Share evidence with `ui-critic` and, if unslop was requested, a separate general read-only task loading `.kilo/skills/unslop/SKILL.md`, running in parallel. Focus on meaningful defects, consolidate findings once, then have the builder fix and recheck; reviewers do not edit source. Declining unslop does not skip QA. Keep raw evidence and report limitations. A proven harmless development-only missing favicon is nonblocking; do not ignore auth, script, or API failures.

Project direction and approved styling choices: TBD.
