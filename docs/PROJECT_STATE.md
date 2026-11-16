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
- **Active task:** BOARD-113, approved shared ignored review storage in
  `.kilo/worktrees/store-reviews-as-ignored-artifacts`, branch `chore/store-reviews-as-ignored-artifacts`.
  Implementation and evidence migration complete; focused verification recorded in the engineering
  log. Independent reviews passed 6 ledger tests and 1 permission test with no blocking source
  findings. Blocked: shared report file-tool write still denied after the user-confirmed task
  configuration reload. The verified checkpoint is not a merge-ready handoff.
- **Previous task:** the human merged configurable shared-workspace lifecycle/authenticated
  review at main `d5ace2f`, including feature commit `44ca90b`. BOARD-103 through BOARD-112 are
  Merged. The old worktree remains for human cleanup; its capped ledger and authorized follow-up
  evidence are preserved in ignored artifacts. Lifecycle/auth source is unchanged by BOARD-113.
- **Previous work:** BOARD-101 (no-production-build rule) and BOARD-102 (accordion board viewer)
  are recorded as Merged on the live factory board. They are not active tasks.
- **Next action:** human activates the narrow `artifacts/reviews/**` permission in the config
  actually loaded by the file tool. One normal report write must succeed before BOARD-113 can
  leave Blocked. Do not bypass the denial, reset review rounds or merge on the agent's initiative.

## Open questions

- The factory repository has no remote. The user decides where it is published.
- Whether the project repository gets its own remote, or stays local alongside the factory.
