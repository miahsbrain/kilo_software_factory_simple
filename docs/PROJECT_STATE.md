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
- **In flight:** one branch waits for the user to merge. `fix/cleanup-and-discard-set-the-board`
  (BOARD-108) makes the teardown command own the lane for the row it tears down: `cleanup
  --board` sets `Merged`, `discard --board` sets `Ready`, and both clear the row's
  `Branch/Worktree` cell in the same atomic board write. The specialist skill catalogue branch
  (`feat/port-the-specialist-skill-catalog`, BOARD-107) adds the specialist skill catalogue at
  `.kilo/catalog/` — the 67 upstream skills
  (MIT, © 2025 Jeffillan) kept as files to read on demand, outside the auto-discovered skills
  folder, with an index at `.kilo/catalog/README.md`, a Specialist skills section in `AGENTS.md`
  §A7, the specialists named in each builder agent file, and `catalog` added to the `guard.py
  sync` slice. The plan skill branch (`feat/port-a-merged-plan-skill`, BOARD-106) and the live
  board viewer change (`feat/compact-accordion-redesign-of-the-live`, BOARD-102) also wait.
- **Next action:** the user reviews and merges `fix/cleanup-and-discard-set-the-board`. Then
  merge the other waiting branches, and pick the first project row from the project's board —
  `project/docs/RISKS.md` holds the ranked defect list, and the top one is the cross-tenant
  credential bleed in `payment_gateway_ms`.

## Open questions

- The factory repository has no remote. The user decides where it is published.
- Whether the project repository gets its own remote, or stays local alongside the factory.
