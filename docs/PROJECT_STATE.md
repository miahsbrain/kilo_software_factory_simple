# PROJECT STATE — software factory

- **Phase:** Setup — the factory holds the harness only. One project repository lives in
  `project/` in this workspace and owns all product documentation.
- **Progress:** The harness is complete: the rules (`AGENTS.md`), the agent team
  (`.kilo/agent/`), the command surface (`.kilo/command/`), the skills with their scripts
  (`.kilo/skills/`), the guard-rail policy (`.kilo/policies/git-policy.json`) that feeds both the
  generated `permission` map in `kilo.jsonc` and `guard.py check-git`, the blank project skeleton
  (`templates/project/`), and the QA capture path that drives Playwright only.
- **Layout:** The factory repository is harness-only (ADR-053). A project is a separate git
  repository that copies the harness in and owns it (ADR-054). The factory board
  (`docs/BOARD.md`) carries factory work only; project work is tracked on the project's own
  board (ADR-055).
- **Active task:** BOARD-116, documentation reconciliation for the approved human-only discard
  policy in `.kilo/worktrees/synchronize-factory-worktree-lifecycle-and-policy`, branch
  `chore/synchronize-factory-worktree-lifecycle-and-policy`. Discard requires `--apply --discard`,
  permanently removes the selected linked worktree and branch without a recovery backup, and
  marks the final linked row `Dropped`; normal cleanup remains separate. Application logic, tests,
  policy and `docs/BOARD.md` were not changed. The focused documentation correction is pending
  human review and merge.
- **Previous task:** the human merged configurable shared-workspace lifecycle/authenticated
  review at main `d5ace2f`, including feature commit `44ca90b`. BOARD-103 through BOARD-112 are
  Merged. The old worktree remains for human cleanup; its capped ledger and authorized follow-up
  evidence are preserved in ignored artifacts. Lifecycle/auth source is unchanged by BOARD-113.
- **Previous work:** BOARD-101 (no-production-build rule) and BOARD-102 (accordion board viewer)
  are recorded as Merged on the live factory board. They are not active tasks.
- **Next action:** human review and merge of BOARD-116. No merge, push, or worktree cleanup was
  performed.
- **Historical in-flight notes:** `fix/cleanup-and-discard-set-the-board` (BOARD-108) and the
  other branches listed below are historical records. Their earlier `discard` → `Ready` behavior
  is superseded by the current BOARD-116 human-only discard policy. The specialist skill catalogue branch
  (`feat/port-the-specialist-skill-catalog`, BOARD-107) adds the specialist skill catalogue at
  `.kilo/catalog/` — the 67 upstream skills
  (MIT, © 2025 Jeffillan) kept as files to read on demand, outside the auto-discovered skills
  folder, with an index at `.kilo/catalog/README.md`, a Specialist skills section in `AGENTS.md`
  §A7, the specialists named in each builder agent file, and `catalog` added to the `guard.py
  sync` slice. The plan skill branch (`feat/port-a-merged-plan-skill`, BOARD-106) and the live
  board viewer change (`feat/compact-accordion-redesign-of-the-live`, BOARD-102) also wait.
- **Historical next action:** the user reviews and merges `fix/cleanup-and-discard-set-the-board`. Then
  merge the other waiting branches, and pick the first project row from the project's board —
  `project/docs/RISKS.md` holds the ranked defect list, and the top one is the cross-tenant
  credential bleed in `payment_gateway_ms`.

## Open questions

- The factory repository has no remote. The user decides where it is published.
- Whether the project repository gets its own remote, or stays local alongside the factory.
