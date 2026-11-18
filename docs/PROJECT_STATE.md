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
- **Active task:** BOARD-120, five approved frontend rule clarifications in
  `.kilo/worktrees/clarify-frontend-design-direction-and-composition`, branch
  `docs/clarify-frontend-design-direction-and-composition`. Existing factory/template sections
  now distinguish builder role, approved design direction, gallery primitives from composition,
  approved redesign scope, and chrome from accessible content colors (ADR-079).
  Approval, gallery-before-screens, reuse, accessibility, auth/API preservation, no-production-build
  and QA/critique/unslop gates remain. Documentation-only; no existing project copies change.
  `git diff --check` passed (exit 0); orchestrator scoped diff review found no blocking inconsistency.
  Verification is documentation-only, not proof of visual results. User authorized committing
  and preparing BOARD-120 for human merge; Pending Merge requires a committed clean worktree.
- **Prior task (separate workspace):** BOARD-117, project bootstrap and template drift correction in
  `.kilo/worktrees/fix-project-bootstrap-and-template-drift`. Initial setup now copies the complete
  approved harness slice and generated config before the first commit, preserving template rules
  and repo map. Template ignores and live-board tracking wording are aligned. Generated handoff
  review/lifecycle commands and workspace paths are now relative to the resolved control root,
  without machine-specific paths or `cd` prefixes (ADR-077 supersedes ADR-075). The human runs
  from that root; executing script selection and board discovery are unchanged. The user has
  authorized committing the reviewed shared changes and preparing both rows for human merge.
  The approved follow-up changes only the policy's first
  workspace-default edit fallback from `deny` to `ask` and its reason; board, index, existing
  project, main checkout and generated config are untouched.
- **Shared review correction:** BOARD-118 uses the same assigned BOARD-117 workspace. Two
  stale wildcard assertions now expect approved required-mode `ask`, not `deny`; protected-file
  and secret assertions remain intact. No production behavior changed.
- **Previous task:** the human merged configurable shared-workspace lifecycle/authenticated
  review at main `d5ace2f`, including feature commit `44ca90b`. BOARD-103 through BOARD-112 are
  Merged. The old worktree remains for human cleanup; its capped ledger and authorized follow-up
  evidence are preserved in ignored artifacts. Lifecycle/auth source is unchanged by BOARD-113.
- **Previous work:** BOARD-101 (no-production-build rule) and BOARD-102 (accordion board viewer)
  are recorded as Merged on the live factory board. They are not active tasks.
- **Verification:** approved isolated bootstrap invocation passed, exit 0, in
  `.tmp/board-117.jsHiWB`. `diff -qr`/`cmp` confirmed all six slices, copied ignore/config and
  retained rules/map; eight project ignore checks passed. Template board and board.py are tracked,
  the factory template board is not ignored, and factory/project live boards are ignored.
  Index listings were empty and `git diff --check` passed. Bootstrap adds the live-board rule
  only to the destination, resolving the earlier child-ignore failure.
- **Handoff verification:** replacement root-relative regression passed in the single approved
  invocation. It covers both repos, spaces/apostrophes in the root, primary/worktree script
  selection, batch arguments, exact review/lifecycle output, execution from root and preview
  immutability. Prior policy alignment and fixture correction are preserved; no real merge.
- **BOARD-118 verification:** one explicit-name unittest invocation covering required-mode
  regeneration, optional-mode creation from the required base map, and handoff passed:
  3 tests, 2.007s, exit 0, after the root-relative revision. No full suite, production build or
  real merge was run.
- **Next action:** human review and merge of BOARD-120 after commit and clean-tree verification.
  No merge, push, or cleanup by the agent.
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
