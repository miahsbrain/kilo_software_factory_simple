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
  Final review found inherited permission-map equality ignores rule order. The parent ledger
  remains stopped at three rounds. The user subsequently authorized a focused BOARD-107
  follow-up in this same workspace; it now passes 33 tests independently and current-source
  review finds no blocking issue. The approved template edit succeeded after the latest reload;
  final documentation alignment closes the remaining hold. Shared rows await human review/merge.
- **Previous work:** BOARD-101 (no-production-build rule) and BOARD-102 (accordion board viewer)
  are recorded as Merged on the live factory board. They are not active tasks.
- **Permission hold resolved:** `templates/project/docs/BOARD.md` now matches approved workspace
  and human lifecycle rules. No denied operation was bypassed. Source lifecycle/auth code is unchanged.
- **Next action:** human review of BOARD-103 through BOARD-112 together, using the feature script's
  `handoff --board BOARD-103` and human merge command. The approved temporary policy edits were
  restored; main `kilo.jsonc` restoration was tool-denied and remains human cleanup. Preserve all
  checkpoints and the capped parent ledger; no fourth parent review round was opened. Follow-up
  proof supersedes earlier zero-test discovery: 33 passed in 14.190s, exit 0; auth passed 19
  independently. No actual merge, discard or mode change has run.

## Open questions

- The factory repository has no remote. The user decides where it is published.
- Whether the project repository gets its own remote, or stays local alongside the factory.
