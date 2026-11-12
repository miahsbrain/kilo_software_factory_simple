---
description: Close out a change — update docs and changelog, then hand the worktree to the user for merge
---

Run the documentation rule from `AGENTS.md` §B1 for the work just completed, inside the worktree:

1. Update `docs/HANDOVER.md` so it matches reality (inventory, pure/effectful markers, data,
   state transitions, API, config).
2. Update `docs/BUSINESS-LOGIC.md` for any changed business rule (question→answer format).
3. Update `docs/ARCHITECTURE.md` if the design, boundaries, or decisions changed.
4. Add a changelog entry at the top of `docs/changelog/CHANGELOG.md`, and a
   `docs/changelog/YYYY-MM-DD-<slug>.md` file if the change needs longer reasoning.
5. Run the project's lint / typecheck / tests and attach the evidence.

Do **not** edit the SQLite board from a builder worktree — the orchestrator owns its rows (§B3).
Apply the handoff checkpoint policy in `AGENTS.md` §B11: commit task changes locally, using a
`wip` checkpoint for unfinished or blocked work, and report the commit SHA and diff command.
Use the message format in §B11. A checkpoint does not bypass verification or human-merge gates.
Run `python3 .opencode/skills/git-worktree/scripts/guard.py check-git -- "<command>"` before any git
command that changes history or the remote. A denied command is not run; a command that needs
approval waits for the user. Never push, merge, invoke `finalize` or open a PR.

Report your lane status and evidence to the orchestrator. Blocked work stays `Blocked`; only
work that passes the existing review and merge gates moves through `In Review` to `Pending Merge`,
the state that waits for human approval to merge.
Recheck the live worktree and board before presenting merge guidance (§B11). Run
`python3 .opencode/skills/git-worktree/scripts/worktree.py handoff --board <ID>` for the final
block. Only finished, verified, reviewed, committed, clean `Pending Merge` work gets a merge
command. Otherwise provide only review/diff commands and blockers; never manually append merge
or teardown commands to a refused handoff.
