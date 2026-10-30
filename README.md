# Kilo Software Factory

An agentic delivery harness for [Kilo Code](https://kilo.ai). It gives an AI team the parts a
small product team needs: a written rule set, a live work board, specialised builder and reviewer
agents, and a loop that carries every task from decision to merged branch.

There is no application runtime here. The factory is rules, agents, commands, and scripts. Point
it at a project and it builds that project.

## What is in the box

| Path | What it holds |
|---|---|
| `AGENTS.md` | The rules. Part A governs the architect and orchestrator, Part B binds every agent. Read it first. |
| `.kilo/agent/` | Five agent definitions: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`. |
| `.kilo/command/` | Eight slash commands that package the workflow. |
| `.kilo/skills/` | Three skills, each with the scripts that enforce the rules: `board`, `git-worktree`, `qa-review`. |
| `.kilo/policies/` | The canonical guard-rail policy. The `permission` map in `kilo.jsonc` is generated from it. |
| `docs/` | The documentation set: board, handover, business logic, UI/UX standard, decisions, changelog. |
| `DOMAIN.md` | Product scope and business rules. The discovery interview fills it in. |
| `apps/` | Scope folders (`web`, `mobile`, `api`), each with its own `AGENTS.md`. |
| `kilo.jsonc` | Project settings, including the Playwright MCP server. |
| `.devcontainer/` | The container this was built in: Node, Python, Rust, chromium, Kilo Code. |

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

**As its own repo** — the usual way for a new project. Clone it, run the discovery interview, and
the factory builds the project in this checkout.

**As the harness inside an existing project** — copy `AGENTS.md`, `.kilo/`, `docs/`, and
`DOMAIN.md` into the project root, drop the parts that do not apply, and start with `/board`.

## Quick start

1. Open the repo in Kilo Code, or open the devcontainer: `code .`
2. `/board` — read the live board. A fresh clone has an empty board, so add the first row:
   ```bash
   python3 .kilo/skills/board/scripts/board.py add --id BOARD-001 --task "What to build" \
     --type Feature --status Ready --priority P1 --risk "🟡 medium — why" --blocked-by "None." \
     --note "- [ ] the criterion someone can check"
   ```
3. `/decide` — the discovery interview. It fills `DOMAIN.md` and produces the first decisions.
4. `/run BOARD-001` — build the row in a worktree.
5. `/ui` — the QA and UI/UX lane, with Playwright evidence.
6. Inspect the branch and merge it yourself. The agent never merges, never pushes, and never
   opens a pull request.

## Requirements

| Tool | Version | Needed for |
|---|---|---|
| Kilo Code CLI | current | the agents and commands |
| git | 2.30+ | worktrees, branches, commits |
| Node.js | 18+ | the Playwright capture script |
| Python | 3.9+ | the board, worktree, and finding scripts |
| chromium | any | the QA capture lane only |

The devcontainer image carries all of them, including chromium at `/usr/bin/chromium`.

## The board

`docs/BOARD.md` is the only state. One row per unit of work, and a row needs acceptance
criteria, a risk line, and a `Blocked by` before it leaves `Backlog`. It is edited by `board.py`
in the main checkout — never by hand, and never from a worktree.

The read-only dashboard shows the lanes, the cards, and the running worktrees:

```bash
python3 .kilo/skills/board/scripts/board_serve.py --port 15180
```

## Rules that are enforced, not only written

| Rule | Enforced by |
|---|---|
| Every change happens in a worktree named after the board row | `.kilo/skills/git-worktree/scripts/worktree.py` |
| Deletes stay inside the worktree | `.kilo/skills/git-worktree/scripts/guard.py` |
| Every board row is edited through the script | `.kilo/skills/board/scripts/board.py` |
| UI evidence comes from one capture script | `.kilo/skills/qa-review/scripts/browser-review.mjs` |
| A finding becomes a row only if it names expected, actual, and evidence | `.kilo/skills/qa-review/scripts/check-finding.py` |
| The QA↔fix loop stops after three rounds | `.kilo/skills/qa-review/scripts/ledger.py` |
| Git commands that change history or the remote are classified before they run | `.kilo/skills/git-worktree/scripts/guard.py check-git` |
| The permission map and the policy file cannot drift apart | `.kilo/skills/git-worktree/scripts/guard.py check-policy` |

The permission map in `kilo.jsonc` is the coarse net: it denies the irreversible git commands and
asks before the rest. `guard.py check-git` is the precise layer — it knows the current branch and
whether the shell sits in a worktree, so it refuses a commit on `main` and a branch switch inside a
worktree.

Two rules have no script behind them, so they need your attention: no screen is built before the
component gallery is approved, and a failed command is reported to you instead of being routed
around with a new tool.

## Conventions

- **Commits** — `<emoji> [<type>] <scope>: <subject>`, with one bullet on what changed and why.
- **Branches** — `feat|fix|chore|docs/<slug>`, derived from the board row's type and title.
- **Artifacts** — `artifacts/<scope>/qa/<date>/<task-id>/`; the capture script computes the path.
- **Review reports and ledgers** are documents, not artifacts: `docs/reviews/<task-id>-{qa,ui,ledger}.md`.

## Status

The board is empty and no application has been built yet. `docs/changelog/CHANGELOG.md` is the
engineering log of the factory itself.

## Licence

Not licensed yet. Add the licence you want before you share this repo.
