# HANDOVER — software factory

> **Session Notes** (keep at the very top, updated every session)
> - **Last session:** 2026-11-04 — the live board viewer became a vertical accordion: collapsible
>   lanes, compact cards that expand to their detail, the last 10 merged rows with a "Show all"
>   control, and folds kept in the browser. BOARD-102, branch
>   `feat/compact-accordion-redesign-of-the-live`.
> - **In flight:** that branch waits for the user to merge it. The board file and the JSON
>   endpoints are unchanged; the viewer still writes nothing.
> - **Next action:** the user reviews and merges the branch. The earlier factory/project split
>   (2026-11-02) also still waits for a merge.
> - **Before:** 2026-11-02 — split the factory from the project. The factory repository now
>   holds only the harness; the Inhouz Cloud AI platform moved to its own git repository at
>   `project/`, with its own board, documentation set and 75 microservice repositories under
>   `project/apps/`. ADR-053, ADR-054 and ADR-055 record the split.

## 1. Overview

- **What it is:** the software factory — a written rule set, a live work board, specialised
  builder and reviewer agents, and a loop that carries every task from decision to merged branch.
  There is no application runtime here.
- **Who uses it:** one human owner and the Kilo Code agents that act for them. The owner approves
  decisions and merges branches; the agents build and review inside worktrees.
- **Tech stack:** Markdown rules plus the Kilo Code agent and command system (`.kilo/agent/`,
  `.kilo/command/`) running on git worktrees. Python 3.9+ standard library for the scripts.
  Details in `docs/STACK.md`.
- **How to use it:** open the factory in Kilo Code. Read `AGENTS.md` at the root. Run `/board` to
  see the live board, `/decide` to approve a decision, `/run` to build a row in a worktree, `/ui`
  for the QA lane, `/closeout` to refresh docs, `/handover` to refresh the application memory map.

## 2. Directory map

| Path | Contents |
|---|---|
| `AGENTS.md` | Root rules for the architect, orchestrator, and every builder (Part A, Part B). |
| `README.md` | The front page: what the factory is, how to point it at a project, quick start. |
| `.kilo/agent/` | The six agent definitions: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`. |
| `.kilo/command/` | The eight slash commands: `decide`, `board`, `board-view`, `run`, `components`, `ui`, `handover`, `closeout`. |
| `.kilo/policies/` | The canonical guard-rail policy: `git-policy.json`. |
| `.kilo/repos.json` | The repo map of this repository. The only way into a repository. |
| `.kilo/scopes/` | The canonical scope rules, one file per scope. `guard.py sync` writes them into a project's app repositories as their `AGENTS.md`. |
| `.kilo/skills/` | The three skills with their scripts: `board`, `git-worktree`, `qa-review`. |
| `.kilo/worktrees/` | Agent worktrees, one per task. Git-ignored. |
| `.devcontainer/` | Container definition: `Dockerfile`, `devcontainer.json`, the redaction script. |
| `docs/` | The factory's own governance set. Product documentation lives in the project repository. |
| `.kilo/scopes/service.md` | The default scope rules for a work surface with no scope file of its own. A work surface carries a pointer to this file, never a copy of it. |
| `templates/project/` | The blank project skeleton a new project starts from. |
| `project/` | A project repository in this workspace. Its own git repository. Never tracked here. |

## 3. Entry points

| Entry point | What it does |
|---|---|
| `AGENTS.md` | The rule set, read by every agent at the start of a task. |
| `.kilo/command/*.md` | Slash commands that package the workflow. |
| `.kilo/skills/board/scripts/board.py` | The board's only writer. `show`, `add`, `set-status`, `set-field`, `note`, `remove`, `lanes`, `add-column`. |
| `.kilo/skills/board/scripts/board_serve.py` | The read-only board viewer on port 15180. Vertical accordion of collapsible lanes, compact cards that expand to their detail, folds remembered in the browser. |
| `.kilo/skills/git-worktree/scripts/worktree.py` | Creates, lists, verifies and cleans the worktree of a board row. `create`, `resume`, `discard`, `list`, `verify`, `cleanup`. |
| `.kilo/skills/git-worktree/scripts/env.py` | Provisions the local env files of a worktree. `sync`, `status`, `clean`. |
| `.kilo/skills/git-worktree/scripts/guard.py` | The guard rails: `check-git`, `check-policy`, `check-delete`, `check-worktree`, `check-repos`, `sync` (one repo or `--all`). |
| `.kilo/skills/git-worktree/scripts/scope.py` | The generated pointer a work surface carries, and the local exclude rule that keeps it out of every commit. |
| `.kilo/skills/qa-review/scripts/browser-review.mjs` | The only UI evidence capture path. Drives Playwright. |
| `.kilo/skills/qa-review/scripts/check-finding.py` | Validates a QA finding and prints its fingerprint. |
| `.kilo/skills/qa-review/scripts/ledger.py` | Opens, closes and reports the QA↔fix rounds of a row. |

## 4. Modules and functions

| Symbol | File | Responsibility | Kind |
|---|---|---|---|
| `board.py` | `.kilo/skills/board/scripts/board.py` | Deterministic manipulation of the markdown board. Never writes prose. | effectful (file I/O) |
| `board_serve.py` | `.kilo/skills/board/scripts/board_serve.py` | Serves the board and the live worktree state read-only, as a collapsible accordion dashboard with compact cards and persisted folds. | effectful (network, file I/O) |
| `worktree.py` | `.kilo/skills/git-worktree/scripts/worktree.py` | Creates the worktree for a board row, derives its name and branch, records it back on the row. `resume` reuses a live worktree, `discard` removes one. | effectful (git, filesystem) |
| `env.py` | `.kilo/skills/git-worktree/scripts/env.py` | Copies the two local env files from a repository's main checkout into a worktree, excludes them from git, and removes them again. Never prints a value. | effectful (filesystem, git exclude) |
| `test_env.py` | `.kilo/skills/git-worktree/scripts/test_env.py` | Self-test for the env provisioning and the worktree reuse rules, in a throwaway repository under a temp directory. | effectful (filesystem, git) |
| `guard.py` | `.kilo/skills/git-worktree/scripts/guard.py` | The guard rails and the sync that carries them into an app repository. | effectful (git, filesystem) |
| `check-finding.py` | `.kilo/skills/qa-review/scripts/check-finding.py` | Validates a finding and derives its fingerprint. | pure |
| `ledger.py` | `.kilo/skills/qa-review/scripts/ledger.py` | The round ledger of a row. | effectful (file I/O) |
| `browser-review.mjs` | `.kilo/skills/qa-review/scripts/browser-review.mjs` | Captures screenshots, console, page errors and network for a route. | effectful (browser, filesystem) |

## 5. Data

| Artefact | Where | What it holds |
|---|---|---|
| The board | `docs/BOARD.md` | One row per unit of factory work. The only state. |
| The decisions | `docs/DECISIONS.md` | Append-only ADR table, ADR-001 onward. |
| The changelog | `docs/changelog/CHANGELOG.md` | The engineering log, newest first, one section per change. |
| The repo map | `.kilo/repos.json` | Repo id → path, relative to this repository's root. |
| The policy | `.kilo/policies/git-policy.json` | The guard-rail rules. The source of the generated permission map. |

## 6. States and state transitions

The board's lanes are the state machine of the factory:
`Backlog` → `Ready` → `In Progress` → `In Review` → `Pending Merge` → `Merged`, plus `Blocked`
and `Dropped`. A row may not reach `Pending Merge` while a `Fix` row it spawned is open, and the
QA↔fix loop is capped at three rounds. Full rules in `AGENTS.md` §B4.

## 7. Public interfaces

The factory exposes no network API. Its public surface is the file layout above and the CLI of
the scripts. The worktree CLI is `worktree.py` (`create`, `resume`, `discard`, `list`, `verify`,
`cleanup`) and `env.py` (`sync`, `status`, `clean`).

## 8. Configuration and environment

See `docs/ENVIRONMENT.md`. Names only, never values.

## 9. Dependencies

| Dependency | Why |
|---|---|
| Python 3.9+ standard library | Every script. No third-party package. |
| Playwright (global install in the dev container) | The QA capture path. |
| Chromium (`/usr/bin/chromium`) | The QA capture path. |
| Git | Worktrees, branches, the guard rails. |

## 10. Testing

No test suite. The verification of a change is the smallest relevant script run, recorded with
its result and a `file:line` proof (AGENTS.md §B4 "Verification cost rule"). The dev container
ships `.devcontainer/test-kilo-redact.sh`, which checks the redaction startup file.

`python3 .kilo/skills/git-worktree/scripts/test_env.py` is the one script-level test: it builds
a throwaway git repository under a temp directory and proves the env provisioning and the
worktree reuse rules.

## 11. Known issues and risks

- The factory has no remote, so the harness cannot be shared yet. The user decides where it goes.
- A project copies the harness by hand, so a factory change does not reach the project
  automatically (ADR-054). The copy is deliberate: the project owns its copy from then on.

## 12. Open questions

- Where the factory repository is published, and where the project repository is pushed.
- Whether the factory's `.kilo/` changes reach the project by a command the user runs, or by a
  hook. Today it is `guard.py sync --repo project --apply`.

## 13. Document map

- `AGENTS.md` — the rules.
- `docs/PROJECT_STRUCTURE.md` — the layout.
- `docs/BOARD.md` — the factory's live board.
- `docs/DECISIONS.md` — the factory's decisions.
- `docs/STACK.md` — the tools and commands.
- `docs/ENVIRONMENT.md` — the environment variables.
- `docs/PROJECT_STATE.md` — where the work stands.
- `docs/changelog/` — the engineering log.
- `templates/project/` — the blank project skeleton.
