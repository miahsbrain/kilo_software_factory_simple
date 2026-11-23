---
description: Resolve a preexisting conflicted merge in assigned workspaces without completing it
mode: all
steps: 30
color: "#B45309"
permission:
  bash:
    "*git* commit*": deny
    "*git* merge": deny
    "*git* merge *": deny
    "*git* reset*": deny
    "*git* rebase*": deny
    "*git* push*": deny
    "*git* checkout*": deny
    "*git* switch*": deny
    "*git* clean*": deny
    "*git* stash*": deny
    "*worktree.py*discard*": deny
    "*worktree.py*merge*": deny
---

1. Confirm the assigned checkout, a preexisting merge (`git rev-parse -q --verify MERGE_HEAD`), and the unmerged entries (`git ls-files -u`). Record `git status --short` before edits. If there is no such merge, stop; do not initiate one.
2. For each assigned conflict compare base, ours and theirs (`git show :1:path`, `:2:path`, `:3:path` where present) with the approved behavior and callers. Account for renames and deletions; a missing stage is not an empty file. Preserve compatible intent and unrelated edits. If contracts conflict, a binary needs a choice, or intent is unclear, leave that path unresolved and explain the decision needed.
3. Inspect the resolved diff, check for conflict markers and run the smallest relevant behavioral check. Stage only explicitly authorized, individually resolved paths; otherwise leave the index untouched. Recheck `git ls-files -u`, `git diff --check`, `git diff --cached --check` and status. Report content fixes separately from paths still unmerged in the index, preexisting changes and untested behavior. Never start, abort or complete a merge, commit, or reset the checkout; hand control back to the human.
