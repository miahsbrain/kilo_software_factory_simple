# BOARD

**The board is the only state.** Re-read it at the start of every session and every task.
One row per unit of work. Never run two orchestrators against this board.

> **This is the live board, and it lives in the main checkout.**
> Only the orchestrator session (working in the repo root) edits this file.
> Worktree branches never edit it — they update the scope docs and report; the orchestrator
> writes the board. That keeps the board conflict-free and lets you see in-flight work here
> before it is merged.

Type: `Feature` `Fix` `Chore` `Docs` `Research`
Lanes: `Backlog` → `Ready` → `In Progress` → `In Review` → `Pending Merge` → `Merged`
(plus `Blocked` for parked work and `Dropped` for abandoned work)

| ID | Task | Type | Status | Priority | Risk | Blocked by | Repos | Branch/Worktree | Notes |
|---|---|---|---|---|---|---|---|---|---|

## Rules

- **Add a row before starting work.** Work not on the board is not sanctioned work.
- **Acceptance criteria (2–5, checkable) are required before a row leaves `Backlog`.**
  Write them in Notes as `- [ ]` checkboxes with the proof to record
  (`test: path:line`, or the exact manual step).
- **Risk** is a level plus one line of reasoning.
- **Blocked by** lists board IDs, or exactly `- None.`
- **Record the original workspace set for the change.** Build, fixes, QA, critique and docs
  reuse its branches and paths. Never create a worktree just for a finding or review.
- **Project-local mode controls the worktree requirement:**
  `python3 .kilo/skills/git-worktree/scripts/worktree.py mode required|optional|status`.
  Required is the default; optional permits the assigned checkout. Restart Kilo after changing
  mode. Protected branches, secrets and assigned scopes remain protected in either mode.
- Create a new workspace only on explicit user request or for the next approved task after
  the previous change merged. Record every mapped repository, path and branch here.
- Move the row the moment the status changes. `In Progress` → `In Review` → `Pending Merge`.
- `Pending Merge` means verified, reviewed, documented and clean, waiting for the human to
  choose the merge target. The agent never merges, pushes, or opens a PR.
- Use `worktree.py handoff --board <ID>` for every repository's diff and the batch merge command.
  The human previews `worktree.py merge --board <ID>` and explicitly applies it with `--apply`.
  The CLI preflights clean workspaces, updates the board and removes merged source worktrees.
  Multi-repository merges are not atomic: stop on conflict and preserve partial outcomes.
- **Frontend rows** must clear the UI gate first (component factory + user-approved gallery) and
  the QA + UI/UX critique lane (`/ui`, Playwright evidence) before they can reach
  `Pending Merge`.
- `Merged` means the human lifecycle command completed all required repositories. Partial
  outcomes stay recorded; never mark the parent merged while a required surface is unfinished.
- Destructive abandonment is human-only: preview `worktree.py discard --board <ID> --repo <ID>`,
  then use `--apply --discard` only for explicitly selected worktrees, even dirty or unmerged.
  Never discard protected or main checkouts. Fully abandoned linked rows become `Dropped`.
- `Blocked` = parked for a human. Record the one-line reason and what unblocks it.
- `Dropped` = abandoned. Record why.
