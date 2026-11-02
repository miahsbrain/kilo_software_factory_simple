# PROJECT STRUCTURE — software factory

Authoritative folder layout of the **factory repository**. Update this file immediately when
folders are added, renamed, moved, or discovered to be different from what is recorded here.
This file records reality; it does not impose it.

The factory holds the harness and nothing else. Every project lives in its own git repository
and is never tracked here (ADR-053).

## Current layout

    factory-repo/
    ├── AGENTS.md                     # the rules, Part A (architect) and Part B (every agent)
    ├── README.md                     # front page: what the factory is, how to point it at a project
    ├── kilo.jsonc                    # Kilo config: MCP servers + generated permission map
    ├── .gitignore                    # ignores /project/ and the local scratch folders
    ├── .devcontainer/                # container: Dockerfile, devcontainer.json, redaction script
    ├── .kilo/
    │   ├── agent/                    # agent definitions (frontend-dev, backend-dev, docs-writer…)
    │   ├── command/                  # slash commands, derived from AGENTS.md
    │   ├── policies/git-policy.json  # canonical guard-rail policy
    │   ├── repos.json                # repo map of this repository: control only
    │   ├── scopes/<id>.md            # canonical scope rules, one per scope
    │   ├── skills/                   # board, git-worktree, qa-review + their scripts
    │   └── worktrees/                # one worktree per board row (git-ignored)
    ├── docs/
    │   ├── README.md                 # index of the factory documentation set
    │   ├── PROJECT_STRUCTURE.md      # this file
    │   ├── HANDOVER.md               # living description of the factory as it is now
    │   ├── BOARD.md                  # factory work only; project work lives in the project repo
    │   ├── DECISIONS.md              # append-only factory decisions (ADR-001…)
    │   ├── PROJECT_STATE.md          # current phase, progress, next step
    │   ├── STACK.md                  # the tools the factory needs, and the commands they run
    │   └── changelog/                # engineering log: CHANGELOG.md + one file per change
    ├── templates/
    │   └── project/                  # blank project skeleton a new project starts from
    │       ├── AGENTS.md             # the rules, copied into the project
    │       ├── DOMAIN.md             # product scope and terminology
    │       ├── ROADMAP.md            # planned work not in progress
    │       ├── CHANGELOG.md          # product-facing changelog (user-approved only)
    │       └── docs/                 # blank governance set: BOARD, HANDOVER, STACK, …
    └── project/                      # a project repository lives here in the workspace.
                                      # It is its own git repository and the factory never
                                      # tracks it (.gitignore).

## Path → purpose

| Path | Purpose |
|---|---|
| `AGENTS.md` | The rules. Part A governs the architect and orchestrator, Part B binds every agent. Read it first. |
| `.kilo/agent/` | Six agent definitions: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`. |
| `.kilo/command/` | Eight slash commands that package the workflow. Derived from `AGENTS.md`, never a source of rules. |
| `.kilo/skills/` | Three skills, each with the scripts that enforce the rules: `board`, `git-worktree`, `qa-review`. |
| `.kilo/policies/` | The canonical guard-rail policy. The `permission` map in `kilo.jsonc` is generated from it. |
| `.kilo/repos.json` | The repo map of this repository. The only way into a repository. |
| `.kilo/scopes/` | The canonical scope rules, one file per scope. `guard.py sync` writes them into a project's app repositories as their `AGENTS.md`. |
| `templates/project/` | The blank project skeleton. A new project copies it, then fills it in. |
| `docs/` | The factory's own governance set. Product documentation lives in the project repository. |
| `kilo.jsonc` | Kilo settings: the Playwright MCP server and the generated permission map. |
| `.devcontainer/` | The container the factory runs in: Node, Python, Rust, chromium, Kilo Code. |
| `project/` | A project repository in this workspace. Never tracked by the factory. |

## Rules

- The map in `.kilo/repos.json` is the only way into a repository. Never address one by path.
- The factory never tracks a project. `project/` is git-ignored, and every project is its own git
  repository.
- A project copies the harness (`AGENTS.md`, `.kilo/`, the permission map) into itself and owns
  the copy from then on (ADR-054).
