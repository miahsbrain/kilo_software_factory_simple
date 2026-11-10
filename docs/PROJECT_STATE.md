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
- **In flight:** one branch waits for the user to merge. `feat/provision-env-files-into-worktrees`
  (BOARD-103) adds the env provisioning script, which copies the local env files into a new
  worktree without ever printing them, and the worktree reuse commands `resume` and `discard`, so
  one board row never ends up with two worktrees.
- **Next action:** the user reviews and merges `feat/provision-env-files-into-worktrees`. Then pick
  the first project row from the project's board — `project/docs/RISKS.md` holds the ranked defect
  list, and the top one is the cross-tenant credential bleed in `payment_gateway_ms`.

## Open questions

- The factory repository has no remote. The user decides where it is published.
- Whether the project repository gets its own remote, or stays local alongside the factory.
