# HANDOVER — software factory

> **Session Notes** (keep at the very top, updated every session)
> - **Last session:** 2026-11-10 — the 67 upstream specialist skills were ported as a
>   read-on-demand catalogue at `.kilo/catalog/`, with an index at `.kilo/catalog/README.md`.
>   The catalogue sits outside the auto-discovered skills folder, so the loader never sees it.
>   BOARD-107, branch `feat/port-the-specialist-skill-catalog`.
> - **In flight:** that branch waits for the user to merge it. The plan skill branch
>   (2026-11-10, BOARD-106) also still waits for a merge, and so does the live board viewer
>   change (2026-11-04, BOARD-102).
> - **Next action:** the user reviews and merges `feat/port-the-specialist-skill-catalog`.
> - **Before:** 2026-11-10 — the upstream `feature-forge` and `architecture-designer` skills
>   were merged into one plan skill at `.kilo/skills/plan/`, with their references carried over
>   intact and every phase mapped onto a document this repository already has. BOARD-106, branch
>   `feat/port-a-merged-plan-skill`.
> - **In flight:** that branch waits for the user to merge it. The live board viewer change
>   (2026-11-04, BOARD-102) also still waits for a merge.
> - **Next action:** the user reviews and merges `feat/port-a-merged-plan-skill`.
> - **Before:** 2026-11-04 — the live board viewer became a vertical accordion: collapsible
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
| `.kilo/skills/` | The five skills with their scripts: `board`, `git-worktree`, `qa-review`, `unslop`, `plan`. |
| `.kilo/skills/plan/` | The merged plan skill (MIT, © 2025 Jeffallan — upstream `feature-forge` and `architecture-designer`). `SKILL.md` plus `references/`: the interview bank, the specification template, EARS syntax, acceptance criteria, pre-discovery subagents, system design, architecture patterns, database selection, ADR template, NFR checklist, and the two superpowers research documents. |
| `.kilo/catalog/` | The specialist skill catalogue: 67 upstream skills (MIT, © 2025 Jeffallan, from https://github.com/Jeffallan/claude-skills), each a `SKILL.md` plus `references/`, byte-for-byte upstream apart from a three-line header that maps the Claude Code tool names onto this harness. It lives outside `.kilo/skills/` on purpose — the loader only scans directories named `skill`/`skills`, so the catalogue is read as a file when the task needs it and never enters the system prompt. |
| `.kilo/catalog/README.md` | The catalogue index: one row per skill — what it covers and when to read it — plus the path pattern and the MIT attribution. The agent reads this first, then one `SKILL.md`. |
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
| `.kilo/skills/git-worktree/scripts/worktree.py` | Creates, lists, verifies and cleans the worktree of a board row. `create`, `resume`, `discard` (`--force`, `--yes`), `handoff`, `list`, `verify`, `cleanup` (by slug or by `--board`). The teardown commands set the row's lane: `cleanup --board` sets `Merged`, `discard --board` sets `Ready`. |
| `.kilo/skills/git-worktree/scripts/env.py` | Provisions the local env files of a worktree. `sync`, `status`, `clean`. |
| `.kilo/skills/git-worktree/scripts/guard.py` | The guard rails: `check-git`, `check-policy`, `check-delete`, `check-worktree`, `check-repos`, `sync` (one repo or `--all`). |
| `.kilo/skills/git-worktree/scripts/scope.py` | The generated pointer a work surface carries, and the local exclude rule that keeps it out of every commit. |
| `.kilo/skills/qa-review/scripts/browser-review.mjs` | The only UI evidence capture path. Drives Playwright. |
| `.kilo/skills/qa-review/scripts/check-finding.py` | Validates a QA finding and prints its fingerprint. |
| `.kilo/skills/qa-review/scripts/ledger.py` | Opens, closes and reports the QA↔fix rounds of a row. |
| `.kilo/skills/unslop/scripts/snapshot.mjs` | Saves a page as a standalone HTML file with its assets inlined, plus a screenshot. The one capture path the QA script does not cover: a live URL, or a page with no local source. |

## 4. Modules and functions

| Symbol | File | Responsibility | Kind |
|---|---|---|---|
| `board.py` | `.kilo/skills/board/scripts/board.py` | Deterministic manipulation of the markdown board. Never writes prose. | effectful (file I/O) |
| `board_serve.py` | `.kilo/skills/board/scripts/board_serve.py` | Serves the board and the live worktree state read-only, as a collapsible accordion dashboard with compact cards and persisted folds. | effectful (network, file I/O) |
| `worktree.py` | `.kilo/skills/git-worktree/scripts/worktree.py` | Creates the worktree for a board row, derives its name and branch, records it back on the row. `resume` reuses a live worktree, `discard` removes one, `discard --force --yes` destroys one after writing a recovery copy, `handoff` prints the hand-off block, `cleanup` removes a merged worktree by slug or by the row that owns it. A teardown by row sets that row's lane: `cleanup` sets `Merged`, `discard` sets `Ready`. | effectful (git, filesystem) |
| `env.py` | `.kilo/skills/git-worktree/scripts/env.py` | Copies the two local env files from a repository's main checkout into a worktree, excludes them from git, and removes them again. Never prints a value. | effectful (filesystem, git exclude) |
| `test_env.py` | `.kilo/skills/git-worktree/scripts/test_env.py` | Self-test for the env provisioning and the worktree reuse rules, in a throwaway repository under a temp directory. | effectful (filesystem, git) |
| `guard.py` | `.kilo/skills/git-worktree/scripts/guard.py` | The guard rails and the sync that carries them into an app repository. | effectful (git, filesystem) |
| `check-finding.py` | `.kilo/skills/qa-review/scripts/check-finding.py` | Validates a finding and derives its fingerprint. | pure |
| `ledger.py` | `.kilo/skills/qa-review/scripts/ledger.py` | The round ledger of a row. | effectful (file I/O) |
| `browser-review.mjs` | `.kilo/skills/qa-review/scripts/browser-review.mjs` | Captures screenshots, console, page errors and network for a route. | effectful (browser, filesystem) |
| `snapshot.mjs` | `.kilo/skills/unslop/scripts/snapshot.mjs` | Saves a live page or a local file as one standalone HTML file with its assets inlined, and saves a screenshot next to it. Resolves Playwright and chromium the same way the QA script does. | effectful (browser, filesystem) |

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
the scripts. The worktree CLI is `worktree.py` (`create`, `resume`, `discard`, `handoff`, `list`,
`verify`, `cleanup`) and `env.py` (`sync`, `status`, `clean`). `discard` takes `--apply`, `--force`
and `--yes`: `--force` alone prints the destruction plan, and `--force --yes` acts after writing a
recovery copy under the repository's `cleanup-wt/` folder. `handoff --board <ID>` prints the
hand-off block — the diff command, then the merge command, then the teardown command — and
changes nothing. `cleanup` takes the worktree either as a slug or as `--board <ID>`, which
resolves the row's `Branch/Worktree` cell and clears it when the worktree is gone; giving both or
neither is a usage error. The lane each command sets: `create` and `resume` put the row in
`In Progress`, `cleanup --board` puts it in `Merged`, `discard --board` puts it back in `Ready`,
and the slug form of `cleanup` touches nothing on the board.

## 8. Configuration and environment

See `docs/ENVIRONMENT.md`. Names only, never values.

## 9. Dependencies

| Dependency | Why |
|---|---|
| Python 3.9+ standard library | Every script. No third-party package. |
| Playwright (global install in the dev container) | The QA capture path. |
| Chromium (`/usr/bin/chromium`) | The QA capture path. |
| The unslop skill | CC BY 4.0 — Damir Sokolovsky ([@heydamir](https://x.com/heydamir)). The credit line must survive in every copied file of `.kilo/skills/unslop/`. |
| The plan skill | MIT — © 2025 Jeffallan (https://github.com/Jeffallan), upstream skills `feature-forge` and `architecture-designer`. The credit line must survive in every copied file of `.kilo/skills/plan/`. |
| The superpowers research documents | MIT — © Jesse Vincent (obra/superpowers), copied into `.kilo/skills/plan/references/`. The credit line must survive in both files. |
| Git | Worktrees, branches, the guard rails. |

## 10. Testing

No test suite. The verification of a change is the smallest relevant script run, recorded with
its result and a `file:line` proof (AGENTS.md §B4 "Verification cost rule"). The dev container
ships `.devcontainer/test-kilo-redact.sh`, which checks the redaction startup file.

`python3 .kilo/skills/git-worktree/scripts/test_env.py` is the one script-level test: it builds
a throwaway git repository under a temp directory and proves the env provisioning, the
worktree reuse rules, the hand-off block and the teardown named by a board row.

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
- `docs/UI-UX.md` — the visual language, the anti-slop rules and the QA evidence spec.
- `docs/BOARD.md` — the factory's live board.
- `docs/DECISIONS.md` — the factory's decisions.
- `docs/STACK.md` — the tools and commands.
- `docs/ENVIRONMENT.md` — the environment variables.
- `docs/PROJECT_STATE.md` — where the work stands.
- `docs/changelog/` — the engineering log.
- `templates/project/` — the blank project skeleton.
