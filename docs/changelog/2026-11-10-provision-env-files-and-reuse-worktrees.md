# Provision env files into worktrees and reuse an existing worktree

**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Date:** 2026-11-10

## The problem

Two separate failures, both about the agent's starting point.

**The application could not start in a new worktree.** A worktree is a fresh checkout of a
branch: it has the committed files and nothing else. The local env files are not committed, so
the new worktree had none, and the application failed to boot there.

The obvious fix — have the agent copy the env files — is not available. The policy denies
reading `.env` and `.env.*` (except `.env.example`) to every file tool, and the shell startup
file refuses any command whose text names one. That rule is deliberate: a credential must never
reach an agent's context. So the agent could not copy the files even if copying them were the
right answer.

**Duplicate worktrees piled up for one board row.** `worktree.py create` derived a branch from
the row's slug and refused when the branch existed, but it did not look at the board row
itself. A row whose worktree was already on disk and recorded on the row could still be
"created" again under another slug, and the agent then worked in a second directory while the
first one still held work.

## The decisions

### The script copies the files, not the agent (ADR-063)

A new script, `.kilo/skills/git-worktree/scripts/env.py`, copies the two local env files from a
repository's main checkout into a worktree. The agent never sees a value: the script reports
the file name and the byte count and nothing else. The read policy is unchanged — the app
reads the file, the agent runs the app.

The rules that make this safe:

- Only `.env` and `.env.local` travel. Not `.env.production`, not `.env.example`, nothing else.
- The destination must resolve under `<repo>/.kilo/worktrees/`. Any other destination is
  refused. The check is realpath-based, so a symlink cannot point the copy somewhere else.
- The copy is written with mode `0600`.
- The copy is listed in the repository's `.git/info/exclude` — the common git dir's exclude
  file, shared by every worktree of that repository and never committed — under a marker
  comment, so the rule is written once and is idempotent.

`worktree.py create` provisions the files after the worktree exists and prints what it
provisioned. `cleanup` and `discard` remove the copies.

### One row, one worktree (ADR-064)

`create` now looks for a live worktree for the same board row, and for the same slug in the
target repository. When it finds one it refuses, with a message that matches the situation:

- The worktree **is this row's own** — found through the row's `Branch/Worktree` cell. The
  refusal names it and prints the three ways forward:

      resume:  worktree.py resume --board BOARD-00X
      discard: worktree.py discard --board BOARD-00X --apply
      new slug: worktree.py create --board BOARD-00X --slug <other-slug>

- The worktree **belongs to another row** — the slug directory is already taken in that
  repository, because another row has the same task title or a different `Type` with the same
  slug. A `resume` or a `discard` for the new row would both fail with "no live worktree", so
  the refusal names the slug directory, names the owning row when the board records one, and
  offers only the ways that work: `--slug <other-slug>`, or
  `worktree.py discard --board <owning-row> --apply` for that other row.

`resume` reuses the live worktree, puts the row back in `In Progress`, and re-provisions the
env files. `discard` removes it, under exactly the checks `cleanup` uses: a dirty tree and a
branch with commits the base does not have both refuse, so unmerged work is never deleted.
With `--apply` it removes the worktree, deletes the branch, removes the env copies, clears the
row's `Branch/Worktree` cell, and writes a recovery TSV.

The copy is written through `os.open` with `O_NOFOLLOW`, so a symlink planted at the
destination inside a worktree is replaced by the copy instead of being written through: the
link target is never touched and the copy lands as a regular file with mode `0600`.

`list` gained a `state` column so a leftover is visible: `active`, `merged`, `stale` (the row
says `Merged` or `Dropped` but the worktree is still there), or `unknown` (no row records it).

## The verification

`.kilo/skills/git-worktree/scripts/test_env.py` builds a throwaway git repository under a temp
directory, copies the scripts into it, and drives them as an agent would. It proves the copy
lands with mode `0600` and byte-identical content, that the copy is listed in the exclude
file, that a destination outside `.kilo/worktrees/` is refused, that `status` and `clean`
behave, that `create` refuses for a row that already has a live worktree, that `resume`
reuses it, that `discard` refuses a dirty worktree and succeeds on a clean merged one, and
that the secret value never appears in any script output. It never touches this repository's
board, worktrees or branches.

## What did not change

- `.kilo/policies/git-policy.json` and `kilo.jsonc` are untouched. The agent's read policy on
  env files stays denied.
- The existing `create`, `list`, `verify` and `cleanup` commands keep their behaviour, apart
  from the new refusal with the three options and the env provisioning.
- The board is still written only by `board.py`, in the main checkout.
