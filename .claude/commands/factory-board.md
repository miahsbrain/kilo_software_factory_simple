---
description: Show the live board and the next actionable task
argument-hint: [board-id]
---

Use the board skill and `board.py show $ARGUMENTS` to summarize active work, blockers, and the next ready task. Start work only when requested, reuse its assigned workspace, and keep status factual. The coordinator writes the live board through the script in the main checkout; builders report status rather than editing it.

Match the row's `[user-approved:<scope>]` note and evidence to the revision under review. Do not ask again for an accepted revision or carry its approval forward after material changes. Use `approve-review` as documented in the board skill only for an explicit user decision on the matching revision. Report remaining blockers separately; approval does not authorize new work.
