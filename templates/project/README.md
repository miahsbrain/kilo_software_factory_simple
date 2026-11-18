# <Project name>

Describe the product and its users here.

## Bootstrap

Follow the factory README's new-project copy commands: copy this skeleton plus `.kilo/agent`, `command`, `skills`, `policies`, `.kilo/.gitignore`, and `kilo.jsonc`. Retain this project's `AGENTS.md` and control-only `.kilo/repos.json`. The skeleton alone is not the complete harness; there is no second maintained harness tree in the template.

Append `/docs/BOARD.md` to the destination `.gitignore`, then run `git init` immediately after the full copy. The blank template board stays tracked in the factory; the copied live board is local and ignored. Staging and an initial commit require explicit user authorization. Worktrees need an existing commit; request authorization when needed.

`apps/` starts empty, without fixed API/web/mobile placeholders; empty directories may be absent after checkout. Create an application only when needed, initialize Git immediately in a genuinely new app directory, and map its ID/path in `.kilo/repos.json` before work. Do not reinitialize existing repositories or make an initial commit without explicit authorization. Nested `apps/*/` repositories are ignored by the control repo. No app-level `AGENTS.md` is required.

## Delivery

Build the frontend flow for user approval before backend/APIs for new apps and user-facing features, using clearly labeled fixtures. Backend-only maintenance needs no unrelated frontend. Use the working agreement and existing board/lifecycle/capture tools. Record the actual stack, development command, and ports in `docs/STACK.md`; no product stack is selected by this template.

## Documentation

Keep `DOMAIN.md`, `ROADMAP.md`, and relevant `docs/` current and concise. `docs/HANDOVER.md` describes current reality; `docs/DECISIONS.md` records material approved choices; `docs/changelog/` records engineering changes. Update the root product `CHANGELOG.md` only when requested. The project owns its copied harness independently of the factory.
