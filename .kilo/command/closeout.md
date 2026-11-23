---
description: Update essential docs and report a change for human review
---

For planned features, compare the result against every phase and final integration check in the board-linked implementation plan. Report evidence or open items to its coordinator. Do not infer completion from a checked implementation task alone.

In the assigned workspace, update the affected essential docs and engineering changelog. Run proportionate checks, report actual results and limitations, and send the coordinator the true lane status. Stage or commit only with applicable user authorization. Use `python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <ID>` for review/lifecycle commands when ready; do not execute merge or push without authorization.
Distinguish the user's scoped manual review decision (`board.py show <ID>`) from verified checks, unresolved blockers, and actual Git state. A recorded approval alone is not `Pending Merge` or `Merged`.

Check `worktree.py reviews status` and the actual review record. Link the QA skill's manual QA/UI checklist for all scopes skipped by policy or unavailable evidence, even with no blocker. Report skipped work separately from verified tests. Neither the settings nor checklist delivery authorizes a pass or lane transition.
Before returning an absolute workspace link to a guide in the resolved primary control artifacts root, require the QA skill's `--manual-guide` format check to pass.

When a commit is authorized, use `[type] Past-tense description`, for example `[feat] Added kus deployment manifests`. Do not include emoji or prefix the description with a repository or folder name.
