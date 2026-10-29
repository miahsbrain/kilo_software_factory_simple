# CLI-only worktree skill

**Date:** 2026-10-29
**Branch:** `feat/cli-worktree-skill`
**Board:** BOARD-004

## What changed

The factory no longer depends on the VS Code Agent Manager extension or on `gh`. Everything runs
through the CLI with plain `git`.

1. **New skill** `.kilo/skills/git-worktree/SKILL.md` — the executable procedure: preconditions,
   creating a worktree with `git worktree add`, working inside it, committing locally, verifying
   before handoff, handing off for human approval, cleanup, and a failure-mode table.
2. **`AGENTS.md` §B4** — the worktree workflow now states the enforced rules as a table with the
   consequence of breaking each one, and the `git worktree add` command verbatim.
3. **`AGENTS.md` §B11** — git policy rewritten for CLI-only: never commit on `main`/`master`/`base`,
   never commit to a branch that already has a worktree, never merge, never push, never open a PR.
4. **New gate: the human approval gate.** `Pending Merge` explicitly means *waiting for human
   approval to merge*, into `main` or a feature branch. The agent prepares and reports; the human
   decides and merges.
5. **Commands updated** — `/board`, `/run`, `/closeout` create and hand off worktrees with `git`
   instead of the extension.

## Why

Two things were wrong before:

- The Agent Manager extension was unreachable from the CLI container, so worktree creation silently
  did nothing and the flow looked broken.
- The rules described the intent but not the enforcement. "Always use a worktree" was a sentence in
  a document; it is now a table of rules with consequences, a skill that can be followed step by
  step, and a commit policy that leaves no room for the base branch to be touched.

## Consequence

An agent can no longer produce a mergeable change by accident. The path to `main` is always:

    worktree → local commits → review → Pending Merge → human merges

and the merge target is the human's choice.
