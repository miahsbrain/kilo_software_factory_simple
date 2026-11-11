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
    ├── opencode.jsonc         # OpenCode V2 config, ordered permissions, MCPs
    ├── .gitignore
    ├── .opencode/
    │   ├── agents/            # architect primary plus six specialist subagents
    │   ├── commands/          # slash commands
    │   ├── policies/          # canonical guard-rail policy
    │   ├── repos.json         # repo id → path map
    │   ├── scopes/<id>.md     # canonical scope rules
    │   ├── skills/            # skills and their scripts
    │   └── worktrees/         # one worktree per board row (git-ignored)
    ├── apps/                  # one folder per application or microservice
    ├── artifacts/             # UI evidence, under artifacts/<scope>/qa/<date>/<task-id>/
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
        ├── reviews/           # QA and UI/UX reports and round ledgers
        ├── handover/          # memory map: README.md index + one file per unit
        └── changelog/         # engineering log

## Path → purpose

| Path | Purpose |
|---|---|

## Rules

- The map in `.opencode/repos.json` is the only way into a repository. Never address one by path.
- One application per folder under `apps/`. Never a folder inside another application.
