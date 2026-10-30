# PROJECT STRUCTURE

Authoritative folder layout. Update this file immediately when folders are added, renamed,
moved, or discovered to be different from what is recorded here.

## Current layout

    project-root/
    ├── AGENTS.md              # main architect + orchestrator rules
    ├── DOMAIN.md              # product scope, terminology, user-facing rules
    ├── ROADMAP.md             # planned work not in progress
    ├── CHANGELOG.md           # product-facing changelog (user-approved only)
    ├── artifacts/             # one canonical folder for UI evidence (git: notes and .md only)
    │   └── <scope>/qa/<date>/<task-id>/
    ├── .kilo/command/         # Kilo slash commands (derived from AGENTS.md)
    ├── .kilo/agent/           # Kilo agent definitions (frontend-dev, backend-dev, qa-reviewer…)
    ├── .kilo/skills/          # Kilo skills (git-worktree, board, qa-review) + their scripts
    ├── .kilo/policies/        # canonical guard-rail policy (git-policy.json)
    ├── docs/
    │   ├── PROJECT_STRUCTURE.md
    │   ├── HANDOVER.md        # living description of the app as it is now
    │   ├── ARCHITECTURE.md    # domain, layers, decisions, roadmap
    │   ├── BUSINESS-LOGIC.md  # question → answer business rules
    │   ├── UI-UX.md           # visual language, anti-slop rules, component factory, QA spec
    │   ├── BOARD.md           # work tracking board
    │   ├── STACK.md           # stack, commands, ports, database, auth
    │   ├── PROJECT_STATE.md   # phase, progress, active task, next step
    │   ├── DECISIONS.md       # append-only approved decisions
    │   ├── RISKS.md           # active risks
    │   ├── API_CONTRACTS.md   # API structure, auth, error formats
    │   ├── ENVIRONMENT.md     # env vars and config keys (placeholders only)
    │   ├── reviews/           # QA and UI/UX reports and round ledgers (documents, not artifacts)
    │   ├── handover/           # application memory map: one file per app + the global index
    │   └── changelog/         # engineering changelog
    └── apps/                  # only when this becomes a multi-app project
        ├── web/
        ├── mobile/
        └── api/

## Path → purpose map

| Path | Purpose |
|---|---|
| `AGENTS.md` | Rules that govern every agent working here |
| `docs/` | All project documentation |
| `artifacts/` | The one canonical folder for UI evidence: `<scope>/qa/<date>/<task-id>/` |
| `docs/reviews/` | Review reports and round ledgers — documents, not artifacts |
| `docs/handover/` | The application memory map: `README.md` is the global index, `<unit>.md` is one per application |
| `.kilo/policies/git-policy.json` | Canonical guard-rail policy. The `permission` map in `kilo.jsonc` and `guard.py check-git` are both generated from it. |
| `apps/<name>/` | One folder per app or microservice (new projects only) |

## Rules

- Existing layouts are kept as discovered; this file records reality, it does not impose it.
- New projects use `apps/web`, `apps/mobile`, `apps/api` as the starting shape.
- Every app or microservice gets its own folder and its own `AGENTS.md`.
