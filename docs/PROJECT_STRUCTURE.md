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
    │   ├── catalog/                  # specialist skills, read as files on demand
    │   │   ├── README.md             # the catalogue index: one row per skill
    │   │   └── <skill>/SKILL.md      # one folder per upstream skill, references/ inside
    │   ├── command/                  # slash commands, derived from AGENTS.md
    │   ├── policies/git-policy.json  # canonical guard-rail policy
    │   ├── repos.json                # repo map of this repository: control only
    │   ├── scopes/<id>.md            # canonical scope rules, one per scope
    │   ├── skills/                   # board, git-worktree, qa-review + their scripts
    │   └── worktrees/                # shared repo-specific change workspaces (git-ignored)

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
    ├── artifacts/                    # ignored evidence in the control main checkout, shared by worktrees
    │   ├── reviews/                  # review reports, findings and bounded-round ledgers; never commit
    │   └── <scope>/qa/<date>/<task>/  # existing dated screenshot/capture hierarchy
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
| `.kilo/agent/` | Agent definitions for builders, reviewers, documentation, and conflict resolution. The last resolves preexisting conflicts without completing merges. |
| `.kilo/command/` | Slash commands that package the workflow. Derived from `AGENTS.md`, never a source of rules. |
| `.kilo/skills/` | Skills and their scripts that enforce the rules. |
| `.kilo/skills/unslop/` | The unslop skill (CC BY 4.0, Damir Sokolovsky) with its references, its snapshot script and its examples. Its signs list is the extended checklist of the QA lane. |
| `.kilo/skills/plan/` | The merged plan skill (MIT, © 2025 Jeffallan — upstream `feature-forge` and `architecture-designer`). `SKILL.md` and `references/`: the interview bank, the specification template, EARS syntax, acceptance criteria, pre-discovery subagents, system design, architecture patterns, database selection, ADR template, NFR checklist, and two superpowers research documents (MIT, © Jesse Vincent). |
| `.kilo/catalog/` | The upstream specialist skill catalogue (MIT, © 2025 Jeffallan — https://github.com/Jeffallan/claude-skills), each entry a `SKILL.md` plus `references/`. Outside the auto-discovered skills folder on purpose — the loader only scans directories named `skill`/`skills`, so these are read as files when the task needs them. `guard.py sync` carries them into a project with the rest of the harness. |
| `.kilo/policies/` | The canonical guard-rail policy. The `permission` map in `kilo.jsonc` is generated from it. |
| `.kilo/repos.json` | The repo map of this repository. The only way into a repository. |
| `.kilo/scopes/` | Canonical specialization rules. Work surfaces receive an ignored generated `AGENTS.md` pointer; task assignments define repository/path boundaries. |
| `.kilo/skills/git-worktree/scripts/test_lifecycle.py` | Disposable-repository regression tests for lifecycle mechanics. |
| `.kilo/skills/qa-review/scripts/browser-review.test.mjs` | Focused authenticated-navigation and evidence-capture regression tests. |
| `.kilo/skills/qa-review/scripts/test_ledger.py` | Isolated stdlib tests for shared ledger paths, ignored output, migration preservation, overrides and the three-round cap. |
| `artifacts/reviews/` | Ignored review reports, findings and ledgers in the control main checkout, shared by all worktrees. Includes migrated BOARD-102/103 evidence; never stage or commit. |
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
