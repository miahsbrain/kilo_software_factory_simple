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
| `templates/project/` | Blank product documents, tracked `services.json`, local tooling ignores; no placeholder services |
| `.devcontainer/` | Development environment |

## Start A New Project

Use `/bootstrap` or the deterministic CLI from the factory checkout root. Never manually copy a new project:

```bash
python3 .kilo/skills/git-worktree/scripts/bootstrap.py project
# Optional isolated destination; its parent must already exist:
python3 .kilo/skills/git-worktree/scripts/bootstrap.py project --destination /path/to/new-project
```

The default destination is the caller factory root's `project/`. Existing paths, even empty directories or dangling symlinks, are refused. Source is the executing checkout, including assigned worktrees. It copies blank product documents, the four-directory `.kilo` harness, config, generated root agreement, blank local board and complete supported devcontainer, creates empty `apps/`, then initializes Git and creates exactly one initial source commit. Source, product docs, `.gitignore` and the small `services.json` manifest are tracked. `.kilo/`, `.devcontainer/`, `kilo.jsonc`, generated root `AGENTS.md`, live board, secrets and outputs are ignored; the factory itself continues tracking its harness and blank template board. Local runtime inputs and factory live state are not copied.

From the initialized **project control root**, create any number of services when needed, not fixed frontend/backend slots:

```bash
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app shop-frontend --git separate
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app shop-backend --git separate
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app shop-backend-experimental --git separate
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app billing-worker --git project
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app inventory-cron --git project
```

Project Git is mandatory; service Git ownership is explicit (`--git separate|project`, no default). `/bootstrap` asks ownership unless specified and asks for a meaningful product-role name if unclear. Names start with a lowercase letter and use lowercase kebab-case; `control` is reserved. Arbitrary meaningful roles are supported, not a suffix enum. All services occupy `apps/<service-name>`. Separate mode initializes an independent repo with an initial `.gitignore` commit; integrated mode creates no nested Git/staging/commit and adds only a targeted control unignore. Both update the single tracked control manifest and ignored local map; review/commit control registration separately with authorization. No scaffolding or install. Invalid names/paths, symlinks, collisions and inconsistent manifests/maps are refused.

Both modes snapshot control ignore rules without control-only service directory patterns and explicitly ignore local tooling. Source, product docs and `.env.example` remain trackable. Later ignore edits do not refresh snapshots. `services.json` records only `services: [{"name":"shop-backend","path":"apps/shop-backend","git":"separate"}]`; blank projects use `{"services":[]}`. Generated `.kilo/repos.json` contains `control: .` plus separate services; integrated services use control's worktree. Do not maintain another tracked ownership manifest.

Requires Python 3.9+ and Git; unset `GIT_*` overrides. User approval authorizes one initial commit only in a genuinely new repository created by that invocation, with an unborn HEAD and empty index. Only intended initial source/docs/manifest/ignore files are staged. The narrow new-repo protected-branch/worktree exception leaves saved policy untouched, checks actual init/add/commit commands against hard denials, and honors hooks and existing Git identity without inventing identity or skipping hooks. Identity preflight fails before creation when possible; later commit/init failures retain partial files/index and report failure. Never retry by reinitializing or deleting retained state. Existing control/factory/app repositories are not auto-committed or migrated; feature implementation waits for successful initialization and an assigned linked worktree.

## Restore A Clone

Run the script from a factory checkout containing `templates/project` and the complete harness/devcontainer source, not the clone's missing tooling:

```bash
python3 /path/to/factory/.kilo/skills/git-worktree/scripts/bootstrap.py restore --destination /path/to/project
# After you clone a registered separate service into its manifest path:
python3 /path/to/factory/.kilo/skills/git-worktree/scripts/bootstrap.py restore --destination /path/to/project/apps/shop-frontend --project /path/to/project
```

Restore control first. It regenerates ignored `.kilo/repos.json` from `services.json`, reports missing service checkouts and restores local tooling, config, root instructions, blank board and devcontainer. No clone/fetch/network or remote URL fabrication. The human supplies actual separate clones in registered paths. App restore requires the control context (`--project`, or safe canonical `apps/<name>` inference); it inherits existing control tooling and adds ignored local instructions/config/harness, not an app-local devcontainer or app map/board. Open the control project's folder in its devcontainer, then work under `apps/<name>` inside that container; an app-only mount cannot see its parent control. Service instructions use portable `../../` context, lifecycle tools discover the ancestor board/map, and control `KILO_CONFIG` uses the mounted workspace path rather than host paths. External standalone app paths are refused; place the clone at its registered path first so lifecycle control-root discovery remains valid. Existing app-local devcontainers are not deleted or modified by restore; review them manually and use the control container for supported inherited tooling.

All outputs are preflighted: missing files are restored, identical files left alone, any differing/custom file or unsafe path causes refusal before writes. No force/overwrite mode. Clone-local `.git/info/exclude` protects restored tooling without changing source `.gitignore`, Git config, index or HEAD; source and product docs are untouched. Factory and linked-worktree destinations, symlinks/traversal, incomplete source and malformed manifests are refused. No init/add/commit/install/build on restore. Generated devcontainer retains supported Dockerfile/features/env/ports but replaces the factory-only post-create step with local shell-guard installation, without global Git configuration. Images are not built by the command.

Restore also refuses any Git-tracked output or ancestor (including deleted files, symlinks and gitlinks) before writing tooling or excludes. Separate-app bootstrap checks both executing-source and target-control policy; neither source nor control hard init/add/commit denials can be overridden by the other's allowance.

## Work

Read the working agreement and relevant task context. Use `/plan` for substantial planning and `/decide` for material unknowns, not routine details. For an app with an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Build reusable components first with Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen theme; the library need not already be installed. Compose the frontend flow for user approval using clearly labeled fixtures, then implement backend/APIs and integration. Backend-only maintenance skips unrelated UI work.

The coordinator maintains the main checkout's live board through `board.py`. `/run` uses the assigned workspace and focused checks. `/ui` shares capture evidence with parallel independent UI critique and a general read-only unslop task; findings are consolidated once. `/handover` updates concise current documentation, not exhaustive inventories. A confirmed harmless development-only favicon failure is nonblocking, but raw evidence remains and auth/script/API failures are still reviewed.

Use existing lifecycle tools in `.kilo/skills/git-worktree/SKILL.md`. Commits, destructive operations, merge, and push require applicable authorization. `worktree.py handoff --board <ID>` prints review and human lifecycle commands; it does not merge. The board viewer runs with `python3 .kilo/skills/board/scripts/board_serve.py --port 15180`.

All FEATURE implementation uses an assigned linked worktree, not the primary checkout. Explicitly assigned features may share its worktree/branch with `worktree.py create --board NEW --reuse EXISTING --repo ID`, preserving scope/ownership without auto-switching branches. Project-tracked apps use control's worktree; separate apps use their mapped repo's worktree. Optional policy remains for non-feature maintenance; do not alter saved mode or permissions for feature assignments.

## Requirements And State

Existing tools use Git 2.30+, Python 3.9+, and Node.js 18+ with available Playwright/Chromium for UI capture. The board's existing stylesheet authoring requires Node 22; serving it is Python-only and offline. Do not install missing dependencies without authorization.

Harness sync copies only `agent`, `command`, `skills`, and `policies`, plus the harness ignore file and generated permissions, into mapped project control repositories. App sync and worktree creation do not generate instruction files or copy scope/catalog layers; existing handwritten app instructions are left alone. Apps inherit the project's local configuration. See `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, and `docs/changelog/CHANGELOG.md` for verification and current status. Review artifacts remain ignored under `artifacts/`; the live board is ignored, while the blank template board stays tracked.

## Licence

No repository-wide licence is selected. Retained third-party skills keep their own attribution and licences.
