# Cleanup and discard set the board lane

**Board:** BOARD-108
**Branch:** `fix/cleanup-and-discard-set-the-board`

## The problem

`worktree.py cleanup --board BOARD-107 --apply` removed the worktree, deleted the branch and
cleared the row's `Branch/Worktree` cell. The row stayed in `Pending Merge`.

The board lane is the source of truth for what is in flight. A row whose branch is merged and
whose worktree is gone must read `Merged`; the row was lying about its own state, and the
orchestrator could not tell a finished task from one still waiting for a merge. The same
confusion came from `discard`, which destroyed the work but left the row in `In Progress` with
no worktree behind it.

## The decision

The teardown command owns the lane for the row it tears down (ADR-071).

| Command | What it does to the row |
|---|---|
| `cleanup --board <ID> --apply` | Status becomes `Merged`, the `Branch/Worktree` cell is cleared |
| `discard --board <ID> --apply` | Status becomes `Ready`, the `Branch/Worktree` cell is cleared |
| `cleanup <slug> --apply` | Nothing — the slug form cannot know the row |

Cleanup only succeeds when the branch is merged into the base and the worktree is clean, so a
successful cleanup means the work is done. A discard destroys the work, so the row is no longer
in progress, but it is still scoped and still on the board: `Ready`.

## The implementation

`clear_row_worktree()` in `.kilo/skills/git-worktree/scripts/worktree.py` took a `status`
argument. It writes the lane cell and the worktree cell in the same `board.write_atomic()`
call, so the two never drift apart. `cmd_cleanup` passes `"Merged"`, `cmd_discard` passes
`"Ready"`.

The board write stays in the control repo's main checkout, exactly like every other board
write in these scripts: the board has one writer, and the script is that writer when the human
runs the teardown in the main checkout. Nothing is written from inside a worktree.

A refused cleanup or discard changes nothing. Both commands return before they touch the
board when the worktree is dirty or the branch holds commits the base does not have, so the
lane stays as it was and the cell keeps pointing at the live worktree.

The slug form of `cleanup` keeps its behaviour exactly: it resolves the worktree from the slug
alone, has no row, and writes nothing to the board.

## The verification

`python3 .kilo/skills/git-worktree/scripts/test_env.py` — the throwaway repository in a temp
directory, never this repository's board. Five checks:

- `cleanup --board` on a merged, clean worktree: worktree gone, branch gone, row reads
  `Merged`, cell empty.
- `cleanup --board` on a branch with a commit the base does not have: refusal, worktree and
  branch in place, row untouched.
- `discard --board` on a clean, merged worktree: row reads `Ready`, cell empty.
- `discard --board` on a dirty worktree: refusal, row untouched.
- `cleanup <slug>`: the row is untouched.
