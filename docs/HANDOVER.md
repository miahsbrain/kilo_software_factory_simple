# HANDOVER — software factory

> **Session Notes — BOARD-117 build complete, 2026-11-11**
> Branch: `fix/refresh-project-board-discovery-every-minute`; worktree:
> `.opencode/worktrees/refresh-project-board-discovery-every-minute`.
> JSON and HTML rediscover boards on every request; ignored projects can appear or disappear
> without restarting. Default refresh is 60 seconds; explicit `--file`, `--refresh`, Pause and
> Refresh now remain. Four temporary-fixture regression tests passed (exit 0).
> The first patch was refused while session context was the factory root; after the orchestrator
> moved the session into this worktree, the authorized relative-path retry succeeded. No guard changed.
> Next: parent reviews the diff and arranges browser QA/critique; no live server was restarted.
> Browser interaction, timers and visual QA are not verified by the Python tests.

> **Session Notes — BOARD-116 documentation review passed, 2026-11-11**
> Added the approved built-in interactive browser policy to root/template §B4.2 and aligned the
> reviewer agents, QA skill, `/ui` and UI-UX guidance. Canonical captures remain script-only;
> QA and unslop gates are unchanged. Branch: `docs/use-opencode-browser-for-interactive-ui-reviews`;
> worktree: `.kilo/worktrees/use-opencode-browser-for-interactive-ui-reviews`, based on migration
> checkpoint `ec7501f` on `feat/port-factory-harness-to-opencode-v2`.
> Parent reviewed all 12 file diffs: PASS. Reviewed docs change prepared for human review;
> local task commit authorized through the existing Kilo bootstrap guard. Next: human reviews the task commit.
> Verification limited to file review because this was a low-risk visual/static change.
> No browser/runtime checks, builds or tests ran. BOARD-114 remains blocked on the security fixture
> `EACCES`; migration work was not resumed and is not merge-ready. Earlier notes are historical.

> **Session Notes — BOARD-115 documentation review, 2026-11-11**
> Added the approved §B11 committed-handoff policy to root/template rules and aligned B5,
> closeout, handover and git-worktree instructions. Branch:
> `docs/require-committed-worktree-handoff-checkpoints`; worktree:
> `.kilo/worktrees/require-committed-worktree-handoff-checkpoints`, based on the user-created
> migration checkpoint `bc3ca6c` on `feat/port-factory-harness-to-opencode-v2`.
> Parent's docs-only review passed; local task commit prepared for human review through the
> authorized existing Kilo bootstrap guard. Next: human reviews the BOARD-115 task commit.
> BOARD-114 remains blocked on the security test's `/tmp/opencode` fixture `EACCES`; no migration
> work or verification was resumed. The migration is not merge-ready; this is not approval to merge it.
> Earlier notes below describe that prior session, not current status.
> Verification limited to file review because this was a low-risk visual/static change.

> **Session Notes — BOARD-114 blocked, 2026-11-11**
> Security adapter and policy/sync changes are implemented but unverified. The command
> `node --test .opencode/plugins/factory-guard/guard.test.mjs` exited 1: two tests could not
> create fixture directories under `/tmp/opencode` (`EACCES`); policy/runtime merge test passed.
> No retry or alternate path attempted. Next: user authorizes a writable fixture location or
> repairs access. Container migration, native runtime checks and independent review remain open.
>
> **Chunk 1 evidence**
> Native OpenCode layout/config and existing harness mechanics are ported on
> `feat/port-factory-harness-to-opencode-v2`, based on `opencode`; no commit yet.
> Bootstrap worktree remains `.kilo/worktrees/port-factory-harness-to-opencode-v2`.
> Parent reviews the diff and the migrated test result next. Security/plugin and container
> chunks remain open; do not treat this work as migration-complete or ready for merge.
> Verification: `python3 .opencode/skills/git-worktree/scripts/test_env.py` exited 0,
> `all checks passed` (lifecycle/env plus native permissions, preservation and base checks).
>
> The older session notes below are retained as context, not current lane status.

> **Session Notes** (keep at the very top, updated every session)
> - **Last session:** 2026-11-10 — the 67 upstream specialist skills were ported as a
>   read-on-demand catalogue at `.opencode/catalog/`, with an index at `.opencode/catalog/README.md`.
>   The catalogue sits outside the auto-discovered skills folder, so the loader never sees it.
>   BOARD-107, branch `feat/port-the-specialist-skill-catalog`.
> - **In flight:** that branch waits for the user to merge it. The plan skill branch
>   (2026-11-10, BOARD-106) also still waits for a merge, and so does the live board viewer
>   change (2026-11-04, BOARD-102).
> - **Next action:** the user reviews and merges `feat/port-the-specialist-skill-catalog`.
> - **Before:** 2026-11-10 — the upstream `feature-forge` and `architecture-designer` skills
>   were merged into one plan skill at `.opencode/skills/plan/`, with their references carried over
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
- **Who uses it:** one human owner and the OpenCode agents that act for them. The owner approves
  decisions and merges branches; the agents build and review inside worktrees.
- **Tech stack:** Markdown rules plus the OpenCode V2 agent and command system (`.opencode/agents/`,
  `.opencode/commands/`) running on git worktrees. Python 3.9+ standard library for the scripts.
  Details in `docs/STACK.md`.
- **How to use it:** open the factory in OpenCode with the `architect` primary agent. Read `AGENTS.md` at the root. Run `/board` to
  see the live board, `/decide` to approve a decision, `/run` to build a row in a worktree, `/ui`
  for the QA lane, `/closeout` to refresh docs, `/handover` to refresh the application memory map.

## 2. Directory map

| Path | Contents |
|---|---|
| `AGENTS.md` | Root rules for the architect, orchestrator, and every builder (Part A, Part B). |
| `README.md` | The front page: what the factory is, how to point it at a project, quick start. |
| `.opencode/agents/` | `architect` primary and six specialist subagents: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`. No model overrides. |
| `.opencode/commands/` | The eight slash commands: `decide`, `board`, `board-view`, `run`, `components`, `ui`, `handover`, `closeout`. |
| `.opencode/policies/` | The canonical guard-rail policy: `git-policy.json`. |
| `.opencode/repos.json` | The repo map of this repository. The only way into a repository. |
| `.opencode/scopes/` | The canonical scope rules, one file per scope. `guard.py sync` writes them into a project's app repositories as their `AGENTS.md`. |
| `.opencode/skills/` | The five skills with their scripts: `board`, `git-worktree`, `qa-review`, `unslop`, `plan`. |
| `.opencode/skills/plan/` | The merged plan skill (MIT, © 2025 Jeffallan — upstream `feature-forge` and `architecture-designer`). `SKILL.md` plus `references/`: the interview bank, the specification template, EARS syntax, acceptance criteria, pre-discovery subagents, system design, architecture patterns, database selection, ADR template, NFR checklist, and the two superpowers research documents. |
| `.opencode/catalog/` | 67 upstream specialists (MIT, © 2025 Jeffallan, https://github.com/Jeffallan/claude-skills), with preserved upstream content/licences and OpenCode tool adaptation headers. Outside `.opencode/skills/` discovery; not configured as an extra skill source, so read only on demand. |
| `.opencode/catalog/README.md` | The catalogue index: one row per skill — what it covers and when to read it — plus the path pattern and the MIT attribution. The agent reads this first, then one `SKILL.md`. |
| `.opencode/worktrees/` | Agent worktrees, one per task. Git-ignored. |
| `.devcontainer/` | Container definition: `Dockerfile`, `devcontainer.json`, the redaction script. |
| `docs/` | The factory's own governance set. Product documentation lives in the project repository. |
| `.opencode/scopes/service.md` | The default scope rules for a work surface with no scope file of its own. A work surface carries a pointer to this file, never a copy of it. |
| `templates/project/` | The blank project skeleton a new project starts from. |
| `project/` | A project repository in this workspace. Its own git repository. Never tracked here. |

## 3. Entry points

| Entry point | What it does |
|---|---|
| `AGENTS.md` | The rule set, read by every agent at the start of a task. |
| `.opencode/commands/*.md` | Slash commands that package the workflow. |
| `.opencode/skills/board/scripts/board.py` | The board's only writer. `show`, `add`, `set-status`, `set-field`, `note`, `remove`, `lanes`, `add-column`. |
| `.opencode/skills/board/scripts/board_serve.py` | The read-only factory board console on port 15180. Server-rendered, offline, standard library at runtime: a three-column dashboard shell (lane/filter sidebar, KPI strip, segmented flow meter, dense lane panel, sticky worktrees rail), search and status/type/priority filters with URL state, parsed Notes checklists, branch copy, and `j`/`k`/`/`/`Enter`/`Esc` keyboard control. Serves `/static/board.css` and the two self-hosted Geist fonts. `/api/board` and `/api/worktrees` are unchanged JSON. |
| `.opencode/skills/board/ui/` | The Tailwind v4 source for the console (`package.json`, `src/app.css`); `npm --prefix .opencode/skills/board/ui run build` writes the committed `static/board.css`. |
| `.opencode/skills/board/static/` | The committed stylesheet and the Geist Sans/Mono variable fonts with their SIL OFL licence. |
| `.opencode/skills/git-worktree/scripts/worktree.py` | Creates, lists, verifies and cleans the worktree of a board row. `create`, `resume`, `discard` (`--force`, `--yes`), `handoff`, `list`, `verify`, `cleanup` (by slug or by `--board`). The teardown commands set the row's lane: `cleanup --board` sets `Merged`, `discard --board` sets `Ready`. |
| `.opencode/skills/git-worktree/scripts/env.py` | Provisions the local env files of a worktree. `sync`, `status`, `clean`. |
| `.opencode/skills/git-worktree/scripts/guard.py` | The guard rails: `check-git`, `check-policy`, `check-delete`, `check-worktree`, `check-repos`, `sync` (one repo or `--all`). |
| `.opencode/skills/git-worktree/scripts/scope.py` | The generated pointer a work surface carries, and the local exclude rule that keeps it out of every commit. |
| `.opencode/skills/qa-review/scripts/browser-review.mjs` | The only UI evidence capture path. Drives Playwright. |
| `.opencode/skills/qa-review/scripts/check-finding.py` | Validates a QA finding and prints its fingerprint. |
| `.opencode/skills/qa-review/scripts/ledger.py` | Opens, closes and reports the QA↔fix rounds of a row. |
| `.opencode/skills/unslop/scripts/snapshot.mjs` | Saves a page as a standalone HTML file with its assets inlined, plus a screenshot. The one capture path the QA script does not cover: a live URL, or a page with no local source. |

## 4. Modules and functions

Chunk 1 reuses these existing boundaries:
- `guard.generated_permission()` (pure) emits native ordered `{action, resource, effect}` rules;
  `write_permission_map()` (effectful) preserves unrelated config keys while replacing that array.
- `worktree.default_base()` (effectful git inspection) prefers `opencode` only for a factory;
  project/app defaults stay unchanged. `repo_root()` (effectful) uses Git's main checkout.
- `board_serve.worktree_state()` (effectful git inspection) uses the existing base selector for ahead/behind counts.
- Native read/edit path rules remain; grep/glob target-path and automatic context enforcement
  are pending the limited guard plugin. Legacy bootstrap is not accepted by steady-state guards.

| Symbol | File | Responsibility | Kind |
|---|---|---|---|
| `board.py` | `.opencode/skills/board/scripts/board.py` | Deterministic manipulation of the markdown board. Never writes prose. | effectful (file I/O) |
| `board_serve.py` | `.opencode/skills/board/scripts/board_serve.py` | Serves the board and the live worktree state read-only, as a server-rendered factory console with a segmented flow meter, keyboard-first filtering, parsed Notes checklists, a sticky worktrees rail, and the static Tailwind CSS and font files. | effectful (network, file I/O) |
| `discover_boards()` / `build_payloads()` | `.opencode/skills/board/scripts/board_serve.py:124`, `:1691` | Discovery checks filesystem paths, including ignored `project/docs/BOARD.md`; payload callbacks rediscover on every HTML/board-JSON request unless explicit paths were supplied. Existing parser and pure renderer stay shared. Default refresh: 60 seconds; CLI override and manual controls retained. | effectful (filesystem, git, clock); HTML rendering is pure |
| `worktree.py` | `.opencode/skills/git-worktree/scripts/worktree.py` | Creates the worktree for a board row, derives its name and branch, records it back on the row. `resume` reuses a live worktree, `discard` removes one, `discard --force --yes` destroys one after writing a recovery copy, `handoff` prints the hand-off block, `cleanup` removes a merged worktree by slug or by the row that owns it. A teardown by row sets that row's lane: `cleanup` sets `Merged`, `discard` sets `Ready`. | effectful (git, filesystem) |
| `env.py` | `.opencode/skills/git-worktree/scripts/env.py` | Copies the two local env files from a repository's main checkout into a worktree, excludes them from git, and removes them again. Never prints a value. | effectful (filesystem, git exclude) |
| `test_env.py` | `.opencode/skills/git-worktree/scripts/test_env.py` | Self-test for the env provisioning and the worktree reuse rules, in a throwaway repository under a temp directory. | effectful (filesystem, git) |
| `guard.py` | `.opencode/skills/git-worktree/scripts/guard.py` | The guard rails and the sync that carries them into an app repository. | effectful (git, filesystem) |
| `check-finding.py` | `.opencode/skills/qa-review/scripts/check-finding.py` | Validates a finding and derives its fingerprint. | pure |
| `ledger.py` | `.opencode/skills/qa-review/scripts/ledger.py` | The round ledger of a row. | effectful (file I/O) |
| `browser-review.mjs` | `.opencode/skills/qa-review/scripts/browser-review.mjs` | Captures screenshots, console, page errors and network for a route. | effectful (browser, filesystem) |
| `snapshot.mjs` | `.opencode/skills/unslop/scripts/snapshot.mjs` | Saves a live page or a local file as one standalone HTML file with its assets inlined, and saves a screenshot next to it. Resolves Playwright and chromium the same way the QA script does. | effectful (browser, filesystem) |

## 5. Data

| Artefact | Where | What it holds |
|---|---|---|
| The board | `docs/BOARD.md` | One row per unit of factory work. The only state. |
| The decisions | `docs/DECISIONS.md` | Append-only ADR table, ADR-001 onward. |
| The changelog | `docs/changelog/CHANGELOG.md` | The engineering log, newest first, one section per change. |
| The repo map | `.opencode/repos.json` | Repo id → path, relative to this repository's root. |
| The policy | `.opencode/policies/git-policy.json` | The guard-rail rules. The source of the generated permission map. |

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
| The unslop skill | CC BY 4.0 — Damir Sokolovsky ([@heydamir](https://x.com/heydamir)). The credit line must survive in every copied file of `.opencode/skills/unslop/`. |
| The plan skill | MIT — © 2025 Jeffallan (https://github.com/Jeffallan), upstream skills `feature-forge` and `architecture-designer`. The credit line must survive in every copied file of `.opencode/skills/plan/`. |
| The superpowers research documents | MIT — © Jesse Vincent (obra/superpowers), copied into `.opencode/skills/plan/references/`. The credit line must survive in both files. |
| Git | Worktrees, branches, the guard rails. |

## 10. Testing

Verification uses focused script tests. The verification of a change is the smallest relevant script run, recorded with
its result and a `file:line` proof (AGENTS.md §B4 "Verification cost rule"). The dev container
ships `.devcontainer/test-kilo-redact.sh`, which checks the redaction startup file.

`python3 .opencode/skills/git-worktree/scripts/test_env.py` builds
a throwaway git repository under a temp directory and proves the env provisioning, the
worktree reuse rules, the hand-off block and the teardown named by a board row.

`python3 .opencode/skills/board/scripts/test_board_serve.py` uses standard-library unittest,
temporary fixture boards and a mocked server. Four tests pass for BOARD-117: new/removed project
discovery in HTML and JSON, separate tasks even with identical IDs, fixed explicit file selection
with fresh reads, default 60 seconds, CLI override and existing control source. No sockets, live
project reads, server restarts or external dependencies. Control-source assertions are not browser
interaction or timer evidence.

## 11. Known issues and risks

- BOARD-114 is partial. OpenCode runtime discovery, plugin security and container integration
  are not verified by the Python lifecycle test. Do not claim legacy grep/glob path denies work.
- The native edit path patterns alone are not a proof of worktree confinement for Location-relative
  paths; automatic context enforcement belongs to the next chunk.

- The factory has no remote, so the harness cannot be shared yet. The user decides where it goes.
- A project copies the harness by hand, so a factory change does not reach the project
  automatically (ADR-054). The copy is deliberate: the project owns its copy from then on.

## 12. Open questions

- Where the factory repository is published, and where the project repository is pushed.
- Whether the factory's `.opencode/` changes reach the project by a command the user runs, or by a
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
