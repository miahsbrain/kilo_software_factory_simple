# Project Structure

This repository is the factory. BOARD124 changes only its assigned linked worktree; existing `project/` and apps are not migrated.

| Path | Purpose |
|---|---|
| `AGENTS.md` | Factory working agreement, including narrow new-bootstrap commit approval |
| `.kilo/agent/`, `.kilo/command/`, `.kilo/skills/`, `.kilo/policies/` | Factory-tracked harness source; project/service copies are ignored local tooling |
| `.kilo/skills/git-worktree/scripts/bootstrap.py` | New project/service bootstrap and factory-sourced clone restore |
| `.kilo/repos.json` | Local lifecycle map; generated project maps contain control plus separate services |
| `.kilo/worktrees/` | Ignored assigned workspaces |
| `.devcontainer/`, `kilo.jsonc` | Factory-tracked environment/config; ignored when copied to projects/services |
| `templates/project/services.json` | Blank tracked product service manifest, no competing tracked repo map |
| `templates/project/` | Product docs, local agreement, static ignores, factory-tracked blank board |
| `docs/BOARD.md`, `artifacts/` | Ignored live board and review evidence |
| `docs/` | Factory state, decisions, handover, structure and engineering history |
| `project/` | Existing independent ignored project, untouched |

New product repositories track source, product docs, `.gitignore` and `services.json`, not `.kilo/`, `.devcontainer/`, `kilo.jsonc`, generated root `AGENTS.md` or live board. Product docs remain independent of the harness. The manifest contains only `services` entries with `name`, `path: apps/<name>` and `git: separate|project`. The ignored map reconstructs `control: .` plus separate services, never integrated ones.

All services live in `project/apps/<service-name>`: `shop-frontend`, `shop-backend`, `shop-backend-experimental`, `billing-worker`, `inventory-cron`, or any meaningful lowercase kebab-case role. There are no fixed slots or suffix enum. Bootstrap asks unclear names and ownership. Separate mode creates one initial ignore-only commit; integrated mode creates no nested repo/staging/control commit. Both register the manifest and update the local map; control registration changes await separate authorized review/commit.

New project bootstrap copies blank docs and complete local tooling/devcontainer, creates empty `apps/`, initializes and initial-commits only intended tracked files. New repos only; no reinitialization. Existing identity/hooks and hard policy denials remain active under the narrow new-repo commit exception. All feature implementation still needs an assigned linked worktree.

Factory CLI `restore --destination <clone> [--project <control>]` restores missing ignored tools/config/instructions/devcontainer and project blank board, leaving identical files and refusing conflicts before writes. It regenerates the map from the manifest and reports missing checkouts without network access. Restore control first; separate app clones must occupy registered paths so existing lifecycle root discovery works. Apps inherit control tooling with local ignored files, no app map/board. Source/index/HEAD/Git config are unchanged; local excludes protect restored files. No install/build or implicit Git mutations on restore.
