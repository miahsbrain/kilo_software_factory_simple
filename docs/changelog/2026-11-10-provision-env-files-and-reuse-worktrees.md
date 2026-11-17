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

## The forced discard (ADR-065)

`discard` refuses a dirty worktree or a branch with commits the base does not have. That is
the right default, but it left a human with no way to destroy that work through the tool: the
only route was a hand `git worktree remove --force`, which leaves nothing behind to recover
from.

`--force` adds that route, in two confirmed steps.

**`discard --force` alone never acts.** It prints the destruction plan — the worktree path, the
branch, how many commits the base does not have, how many files are dirty, and exactly what
will be lost — and then refuses with the command that acts. No file is written and nothing is
deleted.

**`discard --force --yes` acts.** Before it destroys anything it writes a recovery copy under
the repository's common git dir, in the `cleanup-wt/` folder the recovery TSV already uses:

- `<timestamp>.patch` — the uncommitted changes, produced with `git diff HEAD`. Untracked files
  are added with intent-to-add first, so their content lands in the same patch. No patch is
  written when the worktree is clean.
- `<timestamp>.tsv` — one row per action, plus one row per commit the base does not have,
  carrying its sha and the command that restores it.

Both paths are printed, so the human knows where the recovery copy is. Restoring is:

    git apply <git-common-dir>/cleanup-wt/<timestamp>.patch     # the uncommitted changes
    git branch <branch> <sha>                                    # the commits, from the TSV

`--force` only relaxes the refusal. It never changes the dry-run default: `--apply` still
governs acting on the normal path, `--force` without `--yes` never acts, and `--yes` without
`--force` is a usage error. The row's `Branch/Worktree` cell is cleared on a successful forced
discard, exactly as on a normal one; the row's lane is not touched.

## The hand-off block (ADR-066)

Every work session had to hand the human the merge command. The diff command — the one that
shows what is about to be merged — was usually forgotten, so the human had to reconstruct it
before reviewing the work.

`worktree.py handoff --board <ID>` prints the block instead. It prints the worktree path, the
branch, the base, the diff command, the log command, the merge command and the teardown
command. Commands and paths only: it never runs a git command that changes anything, never
merges, never pushes and never deletes.

The block always carries the diff command before the merge command, so the two always reach
the human together. When the branch is already merged into the base, the block prints a
`git show --stat <base>..<branch>` line instead of the merge command, so nobody is handed a
merge that would fail.

`AGENTS.md` §B5 now says what every session report for work in a worktree ends with: this
block, diff command first, then the merge command.

## The teardown, named by the row (ADR-067)

The block printed the cleanup command by slug and then listed the worktree removal and the
branch deletion as loose lines under it. The human was handed a teardown spread over three
lines, with no indication of which one was the step, and the slug had to be read back out of
the path above.

The teardown is now one named step. `worktree.py cleanup --board <ID> --apply` takes the
worktree from the row's `Branch/Worktree` cell — the same cell `resume` and `discard` use —
and runs the existing cleanup logic unchanged: it removes the worktree, deletes the branch,
writes the recovery TSV, and refuses when the branch holds commits the base does not have or
when the worktree is dirty. A successful teardown also clears the cell, so the row stops
pointing at a worktree that is gone.

The row is the thing the human already holds, so it is what names the worktree. Giving a slug
and `--board` together, or neither, is a usage error; the slug form keeps working.

The hand-off block ends with this section:

```text
after the merge, remove the worktree and delete the branch:
  python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup --board BOARD-00X --apply
or, by hand:
  git worktree remove <path>/.kilo/worktrees/<slug>
  git branch -d <type>/<slug>
```

The manual pair stays, for the human who wants the plain git commands; the block no longer
prints the cleanup twice.

## The verification

`.kilo/skills/git-worktree/scripts/test_env.py` builds a throwaway git repository under a temp
directory, copies the scripts into it, and drives them as an agent would. It proves the copy
lands with mode `0600` and byte-identical content, that the copy is listed in the exclude
file, that a destination outside `.kilo/worktrees/` is refused, that `status` and `clean`
behave, that `create` refuses for a row that already has a live worktree, that `resume`
reuses it, that `discard` refuses a dirty worktree and succeeds on a clean merged one, that
the hand-off block ends with the teardown section, that `cleanup --board` removes a merged,
clean worktree and clears the row's cell, that it refuses a branch with an unmerged commit and
leaves the worktree and the branch in place, and that the secret value never appears in any
script output. It never touches this repository's board, worktrees or branches.

## What did not change

- `.kilo/policies/git-policy.json` and `kilo.jsonc` are untouched. The agent's read policy on
  env files stays denied.
- The existing `create`, `list`, `verify` and `cleanup` commands keep their behaviour, apart
  from the new refusal with the three options, the env provisioning, and the new
  `cleanup --board` form.
- The board is still written only by `board.py`, in the main checkout.
