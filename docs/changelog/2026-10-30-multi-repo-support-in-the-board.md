# Multi-repo support in the board and the git tools

**Board:** BOARD-003, BOARD-004 | **Branch:** feat/multi-repo-support-in-the-board,
docs/multi-repo-rules-agent-and-documentation
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

## The rules and the documentation half

BOARD-004 added the half that tells an agent what the model means.

| Piece | What it does |
|---|---|
| `AGENTS.md` | §A1 names the control repo and the work surfaces. §A7 lists `guard.py sync` and `guard.py check-repos` as the scripts that own the guard-rail rules. §B1 sends a change in another repo to the same handover files. §B3 gives the board a `Repos` column and says what it holds. §B4 rule 5 creates the worktree in the repo the row names, and a new subsection, "The control repo and the work surfaces", states the split: board, docs and memory map in the control repo, code and scope in the app repo. |
| `.kilo/agent/docs-writer.md` | A unit's repository comes from `.kilo/repos.json`. The unit file names the repository it was read from, and the index's units table carries the repository id and path. |
| `README.md` | A "Multi-repo" section: what the control repo and the app repos are, the map, and the four commands that turn an application into its own repository. |
| `docs/PROJECT_STRUCTURE.md` | The repo map and the scope rules in the layout tree and the path → purpose map, and the rule that the map is the only way into a repository. |
| `docs/README.md` | The same map and scope rules in one line, under the skills table. |
| `docs/handover/{README,web,mobile,api}.md` | The index names the repository of every unit, the index and the unit files name the repository they were read from, and every `file:line` citation that moved was fixed. |
| `docs/DECISIONS.md` | ADR-042 now covers the whole change: the map, the `Repos` column, the sync, the scope rules as the canonical copy and the control-repo split. |

The scope rules changed too: `.kilo/scopes/<id>.md` is now the source of truth for its scope, and
`apps/<id>/AGENTS.md` is the copy `guard.py sync` keeps in step. The three copies were synced and
now match their canonical files byte for byte.

## Two fixes the sync needed

`guard.py sync --repo control` failed, so the sync could not be run from a worktree at all.

- **It wrote to the main checkout.** The sync now resolves the control repo to the tree the shell
  is in, the same rule `guard.py check-policy` already follows, so a sync run in a worktree writes
  that worktree's copies and never the main checkout's.
- **It crashed on the control repo itself.** Copying the `.kilo/` slice onto itself raised
  `SameFileError`. A file that is already its own destination is now skipped.

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
