# PROJECT STRUCTURE

Authoritative folder layout. Update this file immediately when folders are added, renamed,
moved, or discovered to be different from what is recorded here. This file records reality;
it does not impose it.

## Current layout

    project-root/
    ├── AGENTS.md              # architect + orchestrator rules
    ├── DOMAIN.md              # product scope, terminology, user-facing rules
    ├── ROADMAP.md             # planned work not in progress
    ├── CHANGELOG.md           # product-facing changelog (user-approved only)
    ├── README.md
    ├── kilo.jsonc             # Kilo config, permission map, MCPs
    ├── .gitignore
    ├── .kilo/
    │   ├── agent/             # agent definitions
    │   ├── command/           # slash commands
    │   ├── policies/          # canonical guard-rail policy
    │   ├── repos.json         # repo id → path map
    │   ├── scopes/<id>.md     # canonical scope rules
    │   ├── skills/            # skills and their scripts
    │   └── worktrees/         # original repo-specific change workspace sets (git-ignored)
    ├── apps/                  # one folder per application or microservice
    ├── artifacts/             # ignored, control main checkout only; shared by worktrees, never commit
    │   ├── reviews/           # <task-id>-qa/ui/review/ledger.md and findings
    │   └── <scope>/qa/<date>/<task-id>/  # existing dated UI capture hierarchy
    └── docs/
        ├── PROJECT_STRUCTURE.md
        ├── HANDOVER.md
        ├── ARCHITECTURE.md
        ├── BUSINESS-LOGIC.md
        ├── UI-UX.md
        ├── BOARD.md
        ├── STACK.md
        ├── PROJECT_STATE.md
        ├── DECISIONS.md
        ├── RISKS.md
        ├── API_CONTRACTS.md
        ├── ENVIRONMENT.md
        ├── README.md
        ├── handover/          # memory map: README.md index + one file per unit
        └── changelog/         # engineering log

## Path → purpose

| Path | Purpose |
|---|---|

## Rules

- Seven specialists: frontend-dev, backend-dev, mobile-dev, qa-reviewer, ui-critic, docs-writer,
  merge-conflict-resolver. Assign actual repos/paths; specializations are not fixed folder bans.
- Required mode is default; optional permits assigned nonprotected current checkout edits/commits.
  Reuse original paths across all lanes/findings; new workspaces need an explicit request or the
  next approved task after the previous change merged. Never create an empty one after merge.

- The map in `.kilo/repos.json` is the only way into a repository. Never address one by path.
- One application per folder under `apps/`. Never a folder inside another application.
