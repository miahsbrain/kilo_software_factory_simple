# Worktree names derive from the board row

**Date:** 2026-10-29
**Branch:** `feat/worktree-naming-from-board`
**Board:** BOARD-006

## Problem

`worktree.py create <slug> --type <type>` had two ways to get a worktree named wrong:

- `--type` defaulted to `feat`, so a bug fix needed no effort at all to land on `feat/…`
- the slug was typed by hand, so it drifted from the task it was fixing — `feat/some-name`,
  `feat/temp`, `feat/update`

The name of the worktree is the thing a human scans when deciding what to merge. It has to be
right by construction, not by care.

## Change

`create` now takes the **board row** as its input:

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board BOARD-00X --base main
```

- **Branch type** comes from the row's `Type` column: `Feature` → `feat`, `Fix` → `fix`,
  `Chore` → `chore`, `Docs` → `docs`, `Research` → `chore`.
- **Slug** comes from the row's task title, kebab-cased, trimmed to the first 6 words when longer
  than 48 characters. `--slug` overrides it, but only with valid kebab-case.
- The positional slug and `--type` flag are **removed**. There is no path that produces a
  hand-typed branch type.
- After creating the worktree, the script writes the row's `Branch/Worktree` and `Status` cells.
  It writes them in the **main checkout** — resolved through `git worktree list --porcelain` — so
  a worktree branch never carries a board edit and the live board always points at the running
  worktree.

## Result

| Board row | Worktree | Branch |
|---|---|---|
| `Feature` — Build the first application | `.kilo/worktrees/build-the-first-application` | `feat/build-the-first-application` |
| `Fix` — Export button stays enabled during request | `.kilo/worktrees/export-button-stays-enabled-during-request` | `fix/export-button-stays-enabled-during-request` |

Both verified live: the second row produced `fix/…`, and the board edit appeared only in the main
checkout while the feature worktree's copy stayed untouched.
