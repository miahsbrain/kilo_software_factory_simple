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
    ├── opencode.jsonc                # OpenCode V2: default architect, MCP, ordered permissions
    ├── .gitignore                    # ignores /project/ and the local scratch folders
    ├── .devcontainer/                # container: Dockerfile, devcontainer.json, redaction script
    ├── .opencode/
    │   ├── agents/                   # architect primary plus six specialist subagents
    │   ├── catalog/                  # 67 specialist skills, read as files on demand
    │   │   ├── README.md             # the catalogue index: one row per skill
    │   │   └── <skill>/SKILL.md      # one folder per upstream skill, references/ inside
    │   ├── commands/                 # slash commands, derived from AGENTS.md
    │   ├── policies/git-policy.json  # canonical guard-rail policy
    │   ├── repos.json                # repo map of this repository: control only
    │   ├── scopes/<id>.md            # canonical scope rules, one per scope
    │   ├── skills/                   # board, git-worktree, qa-review, unslop, plan + their scripts
    │   └── worktrees/                # one worktree per board row (git-ignored)
    ├── docs/
    │   ├── README.md                 # index of the factory documentation set
    │   ├── PROJECT_STRUCTURE.md      # this file
    │   ├── HANDOVER.md               # living description of the factory as it is now
    │   ├── BOARD.md                  # factory work only; project work lives in the project repo
    │   ├── DECISIONS.md              # append-only factory decisions (ADR-001…)
    │   ├── UI-UX.md                  # visual language, anti-slop rules, QA evidence spec
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
| `.opencode/agents/` | `architect` primary plus six specialist subagents: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`. All inherit session model selection. |
| `.opencode/commands/` | Ten slash commands that package the workflow. Derived from `AGENTS.md`, never a source of rules. |
| `.opencode/skills/` | Five skills, each with the scripts that enforce the rules: `board`, `git-worktree`, `qa-review`, `unslop`, `plan`. |
| `.opencode/skills/unslop/` | The unslop skill (CC BY 4.0, Damir Sokolovsky) with its references, its snapshot script and its examples. Its signs list is the extended checklist of the QA lane. |
| `.opencode/skills/plan/` | The merged plan skill (MIT, © 2025 Jeffallan — upstream `feature-forge` and `architecture-designer`). `SKILL.md` and `references/`: the interview bank, the specification template, EARS syntax, acceptance criteria, pre-discovery subagents, system design, architecture patterns, database selection, ADR template, NFR checklist, and two superpowers research documents (MIT, © Jesse Vincent). |
| `.opencode/catalog/` | 67 upstream skills (MIT, © 2025 Jeffallan — https://github.com/Jeffallan/claude-skills), each a `SKILL.md` plus `references/`. Outside native `.opencode/skills/` discovery and not registered as an extra skill source; read on demand. `guard.py sync` carries them into a project. |
| `.opencode/policies/` | Canonical guard policy; generates native ordered `permissions`. Search-path enforcement and automatic guard plugin pending. |
| `.opencode/repos.json` | The repo map of this repository. The only way into a repository. |
| `.opencode/scopes/` | The canonical scope rules, one file per scope. `guard.py sync` writes them into a project's app repositories as their `AGENTS.md`. |
| `templates/project/` | The blank project skeleton. A new project copies it, then fills it in. |
| `docs/` | The factory's own governance set. Product documentation lives in the project repository. |
| `opencode.jsonc` | OpenCode V2 settings: default architect, Playwright MCP and generated permissions. |
| `.devcontainer/` | The container the factory runs in: Node, Python, Rust, chromium, Kilo Code. |
| `project/` | A project repository in this workspace. Never tracked by the factory. |

## Rules

- BOARD-114's existing `.kilo/worktrees/port-factory-harness-to-opencode-v2` is bootstrap-only,
  ignored and never moved by agents. New worktrees remain confined to `.opencode/worktrees/`.
- This integration branch is `opencode`; `main` retains Kilo. Devcontainer/security port pending.

- The map in `.opencode/repos.json` is the only way into a repository. Never address one by path.
- The factory never tracks a project. `project/` is git-ignored, and every project is its own git
  repository.
- A project copies the harness (`AGENTS.md`, `.opencode/`, the permission map) into itself and owns
  the copy from then on (ADR-054).
