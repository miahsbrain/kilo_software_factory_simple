# PROJECT STATE — software factory

- **Phase:** Setup — the factory holds the harness only. One project repository lives in
  `project/` in this workspace and owns all product documentation.
- **Progress:** The harness is complete: the rules (`AGENTS.md`), the agent team
  (`.kilo/agent/`), the command surface (`.kilo/command/`), the three skills with their scripts
  (`.kilo/skills/`), the guard-rail policy (`.kilo/policies/git-policy.json`) that feeds both the
  generated `permission` map in `kilo.jsonc` and `guard.py check-git`, the blank project skeleton
  (`templates/project/`), and the QA capture path that drives Playwright only.
- **Layout:** The factory repository is harness-only (ADR-053). A project is a separate git
  repository that copies the harness in and owns it (ADR-054). The factory board
  (`docs/BOARD.md`) carries factory work only; project work is tracked on the project's own
  board (ADR-055).
- **Active task:** configurable shared-workspace lifecycle/authenticated review in
  `.kilo/worktrees/configurable-shared-workspace-lifecycle-and-authenticated` (BOARD-103).
  Seven agents include the conflict specialist. Independent review produced BOARD-104 through
  BOARD-112; corrections and focused regression checks reuse this same workspace. Round 2
  auth/rules review passed; two lifecycle fingerprints repeated. The user approved their
  focused corrections and a third/final review after the rows were escalated to Blocked.
  Final review found inherited permission-map equality ignores rule order; BOARD-107 and
  parent BOARD-103 are Blocked at the three-round cap. The feature is not safe to enable.
- **Previous work:** BOARD-101 (no-production-build rule) and BOARD-102 (accordion board viewer)
  are recorded as Merged on the live factory board. They are not active tasks.
- **Permission blocker:** the session still denies `templates/project/docs/BOARD.md` after the
  user approved enabling its edit. Do not bypass the denial or claim its old instructions aligned.
- **Next action:** human follow-up decision for order-sensitive inherited-map validation and
  task-worktree permission reload for the template. Preserve local checkpoint commits; no
  fourth correction/review round. Builder lifecycle tests passed 31; final independent discovery
  ran zero tests. Auth passed 19 independently. No real merge, discard or mode change has run.

## Open questions

- The factory repository has no remote. The user decides where it is published.
- Whether the project repository gets its own remote, or stays local alongside the factory.
