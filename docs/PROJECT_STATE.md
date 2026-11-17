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
- **Active task:** BOARD-114, provisioning/auth and permission-order cleanup in
  `.kilo/worktrees/provision-local-env-and-secure-qa`, branch
  `feat/provision-local-env-and-secure-qa`. The policy and generated permission map are in sync;
  lifecycle suite passed 36 tests. Documentation and the approved policy cleanup are committed
  on this branch, pending human merge. The separate dirty root-main `kilo.jsonc` was not touched.
- **Previous task:** the human merged configurable shared-workspace lifecycle/authenticated
  review at main `d5ace2f`, including feature commit `44ca90b`. BOARD-103 through BOARD-112 are
  Merged. The old worktree remains for human cleanup; its capped ledger and authorized follow-up
  evidence are preserved in ignored artifacts. Lifecycle/auth source is unchanged by BOARD-113.
- **Previous work:** BOARD-101 (no-production-build rule) and BOARD-102 (accordion board viewer)
  are recorded as Merged on the live factory board. They are not active tasks.
- **Next action:** human review and merge of BOARD-114. No merge, push, or worktree cleanup was
  performed.

## Open questions

- The factory repository has no remote. The user decides where it is published.
- Whether the project repository gets its own remote, or stays local alongside the factory.
