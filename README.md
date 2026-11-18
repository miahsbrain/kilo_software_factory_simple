# Kilo Software Factory

A small delivery harness for [Kilo Code](https://kilo.ai): a working agreement, specialist agents, a live board, and scripts for workspaces and review evidence. This repository maintains the harness, not a product. The existing `project/` is an independent ignored repository and is not migrated by factory changes.

## Contents

| Path | Purpose |
|---|---|
| `AGENTS.md` | Compact working agreement |
| `.kilo/agent/`, `.kilo/command/` | Seven specialist roles and short workflow shortcuts |
| `.kilo/skills/` | Focused procedures and existing lifecycle/capture scripts |
| `.kilo/policies/`, `kilo.jsonc` | Canonical guard policy and generated permissions/configuration |
| `.kilo/repos.json` | Actual repository IDs and paths |
| `docs/` | Factory documentation; local live board and engineering history |
| `templates/project/` | Blank product documents and control-only repo map; no placeholder apps |
| `.devcontainer/` | Development environment |

## Start A New Project

Choose a new empty destination and copy the skeleton plus the full supported harness before initializing Git. From the factory root:

```bash
cp -r templates/project/. /path/to/project/
cp -r .kilo/{agent,command,skills,policies} /path/to/project/.kilo/
cp .kilo/.gitignore /path/to/project/.kilo/.gitignore
cp kilo.jsonc /path/to/project/kilo.jsonc
printf '\n/docs/BOARD.md\n' >> /path/to/project/.gitignore
git -C /path/to/project init
```

Keep the template's `AGENTS.md` and `.kilo/repos.json`; do not overwrite them with the factory map. The template skeleton alone is not the complete harness. The copied project owns its harness independently. Git initialization follows the full copy immediately; staging and the initial commit require explicit user authorization. Worktree creation needs an existing commit, so request that authorization when needed rather than creating one silently.

`apps/` starts empty with no fixed API/web/mobile slots and may not exist in a fresh Git checkout, since Git does not store empty directories. Create an app directory only when the approved project needs it. When creating a genuinely new app directory, initialize its repository immediately with `git -C /path/to/project/apps/<name> init`, then register its real ID/path in the project's `.kilo/repos.json` before work. Initial commits still require explicit authorization. Do not reinitialize an existing app repository. The template ignores `apps/*/` so nested repositories are not tracked by the control repo. No app-level `AGENTS.md` or duplicate harness is required.

For an existing project, agree on the migration scope first and preserve its actual layout and repo map. This change does not migrate the existing `project/`. There is no new provisioning CLI.

## Work

Read the working agreement and relevant task context. Use `/plan` for substantial planning and `/decide` for material unknowns, not routine details. For an app with an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Build reusable components first with Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen theme; the library need not already be installed. Compose the frontend flow for user approval using clearly labeled fixtures, then implement backend/APIs and integration. Backend-only maintenance skips unrelated UI work.

The coordinator maintains the main checkout's live board through `board.py`. `/run` uses the assigned workspace and focused checks. `/ui` shares capture evidence with parallel independent UI critique and a general read-only unslop task; findings are consolidated once. `/handover` updates concise current documentation, not exhaustive inventories. A confirmed harmless development-only favicon failure is nonblocking, but raw evidence remains and auth/script/API failures are still reviewed.

Use existing lifecycle tools in `.kilo/skills/git-worktree/SKILL.md`. Commits, destructive operations, merge, and push require applicable authorization. `worktree.py handoff --board <ID>` prints review and human lifecycle commands; it does not merge. The board viewer runs with `python3 .kilo/skills/board/scripts/board_serve.py --port 15180`.

## Requirements And State

Existing tools use Git 2.30+, Python 3.9+, and Node.js 18+ with available Playwright/Chromium for UI capture. The board's existing stylesheet authoring requires Node 22; serving it is Python-only and offline. Do not install missing dependencies without authorization.

Harness sync copies only `agent`, `command`, `skills`, and `policies`, plus the harness ignore file and generated permissions, into mapped project control repositories. App sync and worktree creation do not generate instruction files or copy scope/catalog layers; existing handwritten app instructions are left alone. Apps inherit the project's local configuration. See `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, and `docs/changelog/CHANGELOG.md` for verification and current status. Review artifacts remain ignored under `artifacts/`; the live board is ignored, while the blank template board stays tracked.

## Licence

No repository-wide licence is selected. Retained third-party skills keep their own attribution and licences.
