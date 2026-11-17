## Summary

The required unslop procedure document `docs/reviews/BOARD-110-unslop.md` does not exist, so the "full unslop procedure is recorded" acceptance criterion has no artifact.

## Repro steps

1. Open the worktree `/workspaces/yt/.kilo/worktrees/fix-the-unslop-signs-in-the-board-console` at commit `6c3eeb8`.
2. List `docs/reviews/` — the newest review files are `BOARD-109-qa.md` and `BOARD-109-ui.md`.
3. Run `git log --all --oneline -- docs/reviews/BOARD-110-unslop.md` — no commit has ever added the file.

## Expected behavior

BOARD-110 criterion 5: the full unslop procedure is recorded in `docs/reviews/BOARD-110-unslop.md` with the five-line direction (product, character, world, moments, signature), every sign group from `.kilo/skills/unslop/references/signs.md`, and the nine passes.

## Actual behavior

The file is absent from the branch and from all history. The changelog entry `docs/changelog/2026-11-11-unslop-board-console.md` summarises four findings and the change, but it carries no five-line direction, no per-sign-group audit and no pass-by-pass record, so it does not satisfy the criterion.

## Evidence

- Missing file: `ls docs/reviews/` in the worktree → `BOARD-102-ledger.md BOARD-102-qa.md BOARD-109-qa.md BOARD-109-ui.md`
- History: `git log --all --oneline -- docs/reviews/BOARD-110-unslop.md` → empty
- Diff: `git diff main --stat` → only `board_serve.py`, `docs/UI-UX.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-11-unslop-board-console.md`

- Console: not applicable, no runtime output for this defect
- Network: 0 failures, see artifacts/factory/qa/2026-11-11/BOARD-110/qa/root/1440x900/light/network.json
- Spec: docs/UI-UX.md §5 and the BOARD-110 acceptance criteria

- Screenshot: none, this is a documentation defect

## Acceptance criteria

- [ ] `docs/reviews/BOARD-110-unslop.md` exists on the reviewed branch
- [ ] it contains the five-line direction
- [ ] it covers every sign group in `.kilo/skills/unslop/references/signs.md`
- [ ] it records the nine passes

## Risk

🟡 medium — the row cannot be accepted as an unslop pass without the audit trail, and the next reviewer cannot tell which signs were resolved versus justified.
Reversibility: two-way. Blast radius: the BOARD-110 row and any later console change that relies on the recorded audit.
