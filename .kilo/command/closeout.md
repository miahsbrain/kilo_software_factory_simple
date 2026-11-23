---
description: Update essential docs and report a change for human review
---

In the assigned workspace, update the affected essential docs and engineering changelog. Run proportionate checks, report actual results and limitations, and send the coordinator the true lane status. Stage or commit only with applicable user authorization. Use `python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <ID>` for review/lifecycle commands when ready; do not execute merge or push without authorization.
Distinguish the user's scoped manual review decision (`board.py show <ID>`) from verified checks, unresolved blockers, and actual Git state. A recorded approval alone is not `Pending Merge` or `Merged`.
