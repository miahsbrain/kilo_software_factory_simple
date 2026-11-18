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

Use `/bootstrap` or the deterministic CLI from the factory checkout root. Never manually copy a new project:

```bash
python3 .kilo/skills/git-worktree/scripts/bootstrap.py project
# Optional isolated destination; its parent must already exist:
python3 .kilo/skills/git-worktree/scripts/bootstrap.py project --destination /path/to/new-project
```

The default destination is the caller factory root's `project/`. Every existing destination is refused, even an empty directory or dangling symlink. The source is the executing script's checkout, including assigned worktrees, never a stale primary checkout. It copies the blank template (retaining project `AGENTS.md` and the flat `{"control":"."}` map), then `agent`, `command`, `skills`, `policies`, the exact `.kilo/.gitignore`, and `kilo.jsonc`. It creates empty `apps/` and initializes Git only after the complete copy. The project owns its copied harness independently. Local files, env/secrets, generated outputs, artifacts, factory map and live board are not copied; only the blank template board is copied, already ignored by static template rules. `.kilo/local/qa-navigation.json` is optional local runtime input, not a source-config prerequisite; source policies, config and tests remain trackable.

From the initialized **project control root**, create each real frontend, backend or other app only when needed:

```bash
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app customer-portal --git separate
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app billing-worker --git project
```

Project Git is mandatory; individual app Git is optional. `/bootstrap` must ASK whether the user wants separate app Git or source tracked in project Git unless already specified. The CLI requires `--git separate|project` with no default; omission fails before mutation. App names/IDs are lowercase kebab-case starting with a letter (`control` is reserved). Both modes create only `apps/<name>`. `separate` writes an app-local `.gitignore`, initializes Git, then registers `<name>: apps/<name>` in flat `.kilo/repos.json`. Its ignore snapshot removes only the control-only `apps/*/` rule, retaining secret/local-output protections and trackable source/`.env.example`; later project ignore edits do not update that snapshot. `project` creates no nested Git or independent map entry: source belongs to the control repository. It appends only `!/apps/<name>/` to the project ignore file, preserving prior patterns and secret/runtime ignores; other apps remain ignored. A missing/nonregular/symlink project `.gitignore` is refused before creation. No arbitrary destination, scaffolding, app `AGENTS.md`, duplicate harness or installation. Existing paths/symlinks, malformed maps, ID/path collisions, traversal and nonproject roots are refused in both modes. `apps/` may be absent after checkout; app mode creates it.

Both modes receive the app-local ignore snapshot so control-root-relative runtime rules also protect integrated app paths. The snapshot is not automatically refreshed by later project ignore edits.

Requires Python 3.9+ and Git. Authorized bootstrap includes scoped init consent where initialization occurs, satisfying the guard's `ask` result; hard denials/errors still stop project bootstrap and separate mode. Project-tracked app mode performs no init or init guard check. Policy files are unchanged. Unset `GIT_*` overrides. Preconditions are checked before writing where feasible. Failures retain partial state, never destructive rollback or copying fallback. No staging or commits occur. Initial scaffolding/bootstrap needs no worktree; request explicit initial-commit authorization before feature implementation in an assigned linked worktree. Existing projects/repositories, including the ignored `project/` and its apps, are never reinitialized or migrated.

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
