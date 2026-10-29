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

| ID | Task | Type | Status | Priority | Risk | Blocked by | Branch/Worktree | Notes |
|---|---|---|---|---|---|---|---|---|
| BOARD-001 | Establish factory documentation and orchestration rules | Chore | Merged | P1 | 🟢 low — docs only | - None. | `main` | Root `AGENTS.md`, `docs/` set, builder `AGENTS.md` files, agent team. Merged in `13b8953` |
| BOARD-002 | Describe the factory in `docs/HANDOVER.md` | Docs | Merged | P2 | 🟢 low — docs only | - None. | `docs/factory-handover` | Replace the generic template with the real factory: entry points, agent/command units marked pure or effectful, the board lane state machine, and the real risks. Merged in `3a4ca25` |
| BOARD-003 | Build the first application | Feature | Backlog | P1 | 🟡 medium — new code, unknown blast radius | - None. | - | Which application this factory builds first is still an open question. Run the discovery interview (`/decide`) before any scaffolding |
| BOARD-005 | Port super-board mechanics into deterministic scripts | Chore | Merged | P1 | 🟡 medium — five scripts enforce the rules the agents were told to follow | - None. | `feat/port-super-board-scripts` | Adds `guard.py` (blocks deletes outside the current worktree and inside the main checkout), `worktree.py` (create/verify/cleanup), `board.py` (every board row edit), `browser-review.mjs` (Playwright evidence), `check-finding.py` (refuses a weak finding). Merged in `e0f0dc4` |
| BOARD-004 | CLI-only git worktree skill and branch protection | Chore | Merged | P1 | 🟢 low — rules and docs only | - None. | `feat/cli-worktree-skill` | Adds `.kilo/skills/git-worktree`, removes the extension dependency, forbids commits on `main`/`master`/`base` and on branches that already have a worktree, and makes `Pending Merge` the human approval gate. Merged in `83b4b2c` |
| BOARD-006 | Derive worktree name and branch type from the board row | Chore | Merged | P2 | 🟢 low — naming only, no behaviour change beyond create | None. | feat/worktree-naming-from-board | create --board BOARD-00X derives feat/fix/chore/docs from the row Type and the slug from the task title; the script writes the row back in the main checkout. Merged in 962cc17 |
| BOARD-007 | Close the build loop: iteration rule, user-centered review, reuse verification | Chore | Merged | P1 | 🟢 low — rules and review criteria only, no runtime change | None. | chore/close-the-build-loop-iteration-rule | Adds the iteration loop (row waits for its fix rows, fixes run the same lanes, row re-verified, 3x repeat blocks) and docs/UI-UX.md §3 with U1-U8 user-centred and M1-M10 modern criteria enforced by QA and the critique. Merged in fdd6521 |

## Rules

- **Add a row before starting work.** Work not on the board is not sanctioned work.
- **Acceptance criteria (2–5, checkable) are required before a row leaves `Backlog`.**
  Write them in Notes as `- [ ]` checkboxes with the proof to record
  (`test: path:line`, or the exact manual step).
- **Risk** is a level plus one line of reasoning.
- **Blocked by** lists board IDs, or exactly `- None.`
- **Every change happens in a worktree named after the feature:**
  `.kilo/worktrees/<feature-slug>/` on branch `feat|fix|chore|docs/<feature-slug>`.
  Record the exact worktree path and branch here.
- Move the row the moment the status changes. `In Progress` → `In Review` → `Pending Merge`.
- `Pending Merge` means green and waiting for the user to inspect and merge into `main`.
  The agent never merges, pushes, or opens a PR.
- **Frontend rows** must clear the UI gate first (component factory + user-approved gallery) and
  the QA + UI/UX critique lane (`/ui`, Playwright evidence) before they can reach
  `Pending Merge`.
- `Merged` means the user actually merged it. The orchestrator sets this on `main` after the
  merge; that board edit is the only change left uncommitted for the user.
- `Blocked` = parked for a human. Record the one-line reason and what unblocks it.
- `Dropped` = abandoned. Record why.
