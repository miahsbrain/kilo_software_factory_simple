# OpenCode Software Factory

BOARD-114 chunk 1 targets integration branch `opencode`; `main` retains Kilo.
Native layout/config is ported. Security plugin and devcontainer migration remain pending.
The existing bootstrap worktree stays unmoved; new worktrees use `.opencode/worktrees/`.

An agentic delivery harness for [OpenCode V2](https://opencode.ai/v2/docs/). It gives an AI team the parts a
small product team needs: a written rule set, a live work board, specialised builder and reviewer
agents, and a loop that carries every task from decision to merged branch.

There is no application runtime here. The factory is rules, agents, commands, and scripts. Point
it at a project and it builds that project.

**The factory is not the project.** This repository holds the harness and nothing else. Every
project lives in its own git repository, copies the harness in, and is never tracked here
(ADR-053). Product documentation — the board, the domain rules, the handover, the changelog —
belongs to the project, not to the factory.

## What is in the box

| Path | What it holds |
|---|---|
| `AGENTS.md` | The rules. Part A governs the architect and orchestrator, Part B binds every agent. Read it first. |
| `.opencode/agents/` | Six agent definitions: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`. |
| `.opencode/commands/` | Eight slash commands that package the workflow. |
| `.opencode/skills/` | Three skills, each with the scripts that enforce the rules: `board`, `git-worktree`, `qa-review`. |
| `.opencode/policies/` | Canonical guard policy; generates ordered native `permissions`. |
| `.opencode/repos.json`, `.opencode/scopes/` | The repo map and the canonical scope rules for a multi-repo setup. |
| `docs/` | The factory's own documentation set: board, handover, structure, decisions, changelog. |
| `templates/project/` | The blank project skeleton a new project starts from. |
| `opencode.jsonc` | OpenCode V2: default architect, Playwright MCP and generated permissions. No model override. |
| `.devcontainer/` | The container this was built in: Node, Python, Rust, chromium, Kilo Code. |
| `project/` | A project repository in this workspace. Its own git repository. Never tracked here. |

## The loop

Every unit of work is a row on the board, and every row moves through the same lanes:

```
decision sheet  ->  build  ->  QA  ->  critique  ->  review  ->  merge
(user approves)   (worktree)  (evidence)  (UI/UX)   (diff)   (you do it)
```

A row is not finished when the builder is finished. It is finished when its acceptance criteria
pass with recorded proof. The QA↔fix loop runs at most three rounds; a finding that repeats
blocks the row instead of opening another one.

## Plug it into a project

A project is its own git repository. It copies the harness in and owns the copy from then on
(ADR-054).

**New project** — copy the skeleton, make it a repository, start the discovery interview:

```bash
cp -r templates/project/. /path/to/project/
cd /path/to/project
git init && git commit -m "chore: start the project"
```

Then open it in OpenCode and run `/decide` to fill `DOMAIN.md`, `/board` to open the first row.

**Existing project** — copy `AGENTS.md` and `.opencode/` into the project root, then add the
documentation set the project needs (`DOMAIN.md`, `docs/BOARD.md`, `docs/STACK.md`) and run
`guard.py sync` for each app repository. Drop the parts that do not apply.

**In this workspace** — `project/` is a project repository that already exists. The factory
never tracks it: it is listed in `.gitignore`, and it is a separate git repository with its own
board and its own documentation.

## Multi-repo

A project is a control repo plus one repository per application.

- **Control repo** — the project repository. It holds `AGENTS.md`, `docs/`, the board, the domain
  rules, the API contracts and the guard-rail policy.
- **App repos** — a git repository at `apps/<name>/`, nested inside the control repo. Each holds one
  application and its own copy of the `.opencode/` slice, so the guard rails are the same wherever the
  work happens.

`.opencode/repos.json` maps a repo id to a path:

    { "control": ".", "api": "apps/api" }

To turn an application into its own repository:

    cd apps/api
    git init
    git commit --allow-empty -m "chore: start the api repository"
    cd ../..
    # the control repo must not track the nested repository
    printf 'apps/api/\n' >> .gitignore
    python3 .opencode/skills/git-worktree/scripts/guard.py sync --repo api --apply

After that, `worktree.py create --board BOARD-00X --repo api` puts the worktree in that
repository, and the board still lives in the control repo. A row names the repos it touches in its
`Repos` cell.

### Where the work happens

Every change lands in a worktree **inside the repository it touches**, and the row that tracks it
lives on the control repo's board:

    board row  →  docs/BOARD.md of the control repo          (one writer: the orchestrator)
    worktree   →  apps/<name>/.opencode/worktrees/<slug>/         (one per row, per repository)

The factory prefers `opencode` when present. Other target repositories retain their own base:
`main` when it exists, otherwise the branch it
names as `origin/HEAD`. Name one with `--base` to override. A row's `Repos` cell lists every
repository it touches, and its `Branch/Worktree` cell records the exact path and branch.

### Carrying the harness across

The harness reaches a repository by copy, and the copy is a command:

    # one repository
    python3 .opencode/skills/git-worktree/scripts/guard.py sync --repo api --apply

    # every repository in the map, except the control repo
    python3 .opencode/skills/git-worktree/scripts/guard.py sync --all --apply

A **control repo** — one that holds a repo map and a board — receives the `.opencode/` slice and a
generated permission map. A **work surface** receives one generated file: `AGENTS.md`, a pointer
that names the project, the canonical scope rules and the unit's documentation. The pointer is
never committed: it is listed in the repository's `.git/info/exclude`, which belongs to the clone,
is shared by every worktree of that repository, and never enters a commit. A work surface's
committed content is its application code alone.

The factory and the project are two repositories, so a change in the factory's `.opencode/` reaches
the project the same way — sync it into the project, then sync from the project into the work
surfaces. The project is registered in the factory's `.opencode/repos.json` for exactly that.

The harness finds the control repo by walking up, so the board, the repo map and the guard rails
work from inside a work surface as well as from the control repo.

## Quick start

1. Open the repo in OpenCode V2. The existing devcontainer port is still pending.
2. `/board` — read the live board. A fresh clone has an empty board, so add the first row:
   ```bash
   python3 .opencode/skills/board/scripts/board.py add --id BOARD-001 --task "What to build" \
     --type Feature --status Ready --priority P1 --risk "🟡 medium — why" --blocked-by "None." \
     --note "- [ ] the criterion someone can check"
   ```
3. `/handover` — read the whole codebase and write the application memory map: one handover per
   application plus the global index in `docs/handover/`.
4. `/decide` — the discovery interview. It fills `DOMAIN.md` and produces the first decisions.
5. `/run BOARD-001` — build the row in a worktree.
6. `/ui` — the QA and UI/UX lane, with OpenCode built-in browser evidence.
7. Inspect the branch and merge it yourself. The agent never merges, never pushes, and never
   opens a pull request.

## Requirements

| Tool | Version | Needed for |
|---|---|---|
| OpenCode | V2 | architect primary, six specialist subagents, commands and five discoverable skills |
| git | 2.30+ | worktrees, branches, commits |
| Node.js | 18+ | retained historical/test tooling; board stylesheet authoring uses the version in `docs/STACK.md` |
| Python | 3.9+ | the board, worktree, and finding scripts |
| chromium | any | retained historical/test tooling, not UI QA |

The devcontainer image carries all of them, including chromium at `/usr/bin/chromium`.

## The board

The live board is clone-local SQLite in the Git common directory. `docs/BOARD.md` is a legacy
import source, not live state. Each project repository has its own board. The orchestrator is the
only writer and edits rows through `board.py`; the Markdown export is generated, never hand-edited.
Each row needs acceptance criteria, a risk line and dependencies before it leaves `Backlog`.

The read-only dashboard shows board lanes, task cards, branches and worktrees. It does not show
OpenCode sessions, dispatch agents or edit tasks:

```bash
python3 .opencode/skills/board/scripts/board_serve.py --port 15180
```

## Rules that are enforced, not only written

| Rule | Enforced by |
|---|---|
| Every change happens in a worktree named after the board row | `.opencode/skills/git-worktree/scripts/worktree.py` |
| Deletes stay inside the worktree | `.opencode/skills/git-worktree/scripts/guard.py` |
| Every board row is edited through the script | `.opencode/skills/board/scripts/board.py` |
| UI evidence uses only OpenCode's built-in browser | `AGENTS.md` §B4.2 and the QA skill; load `browser` first |
| A finding becomes a row only if it names expected, actual, and evidence | `.opencode/skills/qa-review/scripts/check-finding.py` |
| The QA↔fix loop stops after three rounds | `.opencode/skills/qa-review/scripts/ledger.py` |
| Git commands that change history or the remote are classified before they run | `.opencode/skills/git-worktree/scripts/guard.py check-git` |
| The permission map and the policy file cannot drift apart | `.opencode/skills/git-worktree/scripts/guard.py check-policy` |

The permission map in `opencode.jsonc` is the coarse net: it denies the irreversible git commands and
asks before the rest. `guard.py check-git` is the precise layer — it knows the current branch and
whether the shell sits in a worktree, so it refuses a commit on `main` and a branch switch inside a
worktree.

Native read/edit rules match paths. Grep permissions match the expression and glob permissions
match the requested pattern, not the target paths; hidden-path rules cannot protect search
results. Automatic context enforcement and shell/container protection remain later chunks.

Two rules have no script behind them, so they need your attention: no screen is built before the
component gallery is approved, and a failed command is reported to you instead of being routed
around with a new tool.

## Conventions

- **Commits** — `<emoji> [<type>] <scope>: <subject>`, with one bullet on what changed and why.
- **Branches** — `feat|fix|chore|docs/<slug>`, derived from the board row's type and title.
- **Artifacts** — store browser evidence under `artifacts/<scope>/qa/<date>/<task-id>/` with
  route, viewport, theme, steps, expected and observed results. Hold unavailable measurements;
  never assume desktop and server filesystems are shared.
- **Skills** — before every task, read `.opencode/catalog/README.md`, apply all relevant skills
  and required references, and report skills used or that none matched (§A7). Example lists are not limits.
- **QA/UI reports and evidence** live under `artifacts/<scope>/qa/<YYYY-MM-DD>/<task-id>/` in the
  primary checkout (`qa.md`, `ui.md`, and builder evidence under `builder/`). The bounded-loop
  ledger alone remains under `.factory-state/reviews/` and is updated through `ledger.py`.

## Status

The factory board is empty and the harness is complete. `docs/changelog/CHANGELOG.md` is the
engineering log of the factory itself. The Inhouz Cloud AI platform — 75 microservices, each its
own git repository — is the project in `project/`.

## Licence

Not licensed yet. Add the licence you want before you share this repo.
