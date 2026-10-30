# Multi-repo support in the board and the git tools

**Board:** BOARD-003 | **Branch:** feat/multi-repo-support-in-the-board
**Date:** 2026-10-30

## The problem

The factory assumed one repository. The board, the worktrees, the guard rails and the scope rules
all lived in the control repo. An application that keeps its own git repository under `apps/`
could not be worked in: there was no way to say "this row belongs to the API repo", and no way to
give that repo the same agents, policy and skills the control repo has.

## The model

- The repo the agent works in is the **control repo**. It owns the board, the documentation, the
  policy and the agents.
- An application may live in its own git repository at `apps/<name>/`, nested inside the control
  repo. That app repo is a **work surface**: it gets the same `.kilo/` slice and the same guard
  rails, synced from the control repo.
- A repo is addressed by an **id** from `.kilo/repos.json`, never by a raw path on the command
  line. The map is the only way in.

## What changed

| Piece | What it does |
|---|---|
| `.kilo/repos.json` | The map: `control`, `web`, `mobile`, `api` → paths relative to the control repo root. |
| `.kilo/scopes/<id>.md` | The canonical copy of a scope's rules, taken from `apps/<id>/AGENTS.md` plus a marker line. `apps/<id>/AGENTS.md` stays as the monorepo copy. |
| `board.py` | A `Repos` column between `Blocked by` and `Branch/Worktree`. `add-column` migrates a table without a hand edit. `add --repos` and `set-field --field repos` write the cell. A row whose cell count differs from the header is refused, never silently misaligned. |
| `worktree.py` | `create --repo <id>` creates the worktree in that repo, under that repo's own `.kilo/worktrees/`, keeps the board in the control repo, and records the path relative to the control repo root plus the repo id on the row. `cleanup` and `verify` find the worktree from the row's cell. `list` covers every repo in the map. |
| `guard.py` | `sync --repo <id>` copies the `.kilo/` slice, the scope rules and the generated permission map into the target repo, dry run by default. `check-repos` proves the map and the `apps/` layout agree. |
| `git-policy.json` | `.kilo/scopes/*.md` joins the rules files that need the user's approval. |

## Decisions inside the decisions

- **The board never moves.** It stays in the control repo, because the orchestrator is its only
  writer and it is the user's view of the work.
- **The sync source is the control repo's main checkout.** The guard rails that are distributed
  are the merged, reviewed content. A branch's own changes are distributed after the merge.
- **A dry run never refuses to plan.** `sync --repo <id>` prints the plan even when the target is
  not a git repository yet; `--apply` refuses to write into a non-repository. `check-repos`
  reports a registered plain folder as a note, not a failure, so the map can be written before the
  app folders become repositories.
- **The map is read from the control repo, with the running tree as the fallback.** A branch that
  adds the map works before it is merged, and the paths it names still resolve against the control
  repo root.

## What a real multi-repo setup still needs

- The app folders under `apps/` become git repositories. `git init` in each, one commit, and the
  map already names them.
- Each app repo needs a base branch (`main`) with a first commit, because `worktree.py create`
  needs the base branch to exist in the target repo.
- `guard.py sync --repo <id> --apply` per app repo, once, to give it the `.kilo/` slice, its
  `AGENTS.md` and its permission map.
- A remote per app repo, if the app is pushed anywhere. The guard still denies `git push` to the
  agent.
