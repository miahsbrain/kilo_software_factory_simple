---
description: Update essential docs and report a change for human review
argument-hint: <board-id>
---

Close out $ARGUMENTS. Consult `engineering-practices` for code review or documentation guidance relevant to the diff; Claude Code's built-in `/code-review` and `/security-review` can supplement it. None of these authorize deployment, commits or merge.

For planned features, compare the result against every phase and final integration check in the board-linked implementation plan. Report evidence or open items to its coordinator. Do not infer completion from a checked implementation task alone.

In the assigned workspace, update the affected essential docs and engineering changelog. Run proportionate checks, report actual results and limitations, and send the coordinator the true lane status. Stage or commit only with applicable user authorization. Use `python3 .claude/skills/git-worktree/scripts/worktree.py handoff --board <ID>` for review/lifecycle commands when ready; do not execute merge or push.

Distinguish the user's scoped manual review decision (`board.py show <ID>`) from verified checks, unresolved blockers and actual Git state. A recorded approval alone is not `Pending Merge` or `Merged`. Apply the qa-review skill's **Review switches** to the actual review record: report skipped work separately from verified tests, and link the validated manual checklist for every skipped scope.

When a commit is authorized, use `[type] Past-tense description`, for example `[feat] Added kus deployment manifests`. Do not include emoji or prefix the description with a repository or folder name.
