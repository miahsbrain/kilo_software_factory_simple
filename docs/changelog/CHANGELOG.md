# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-10-29] CLI-only worktree skill and branch protection
**Type:** Chore
**Board:** BOARD-004 | **Branch:** feat/cli-worktree-skill
**Changed:** `.kilo/skills/git-worktree/SKILL.md` (new), `AGENTS.md` (§B4, §B11), `.kilo/command/board.md`, `.kilo/command/run.md`, `.kilo/command/closeout.md`, `docs/DECISIONS.md`, `docs/RISKS.md`, `docs/PROJECT_STRUCTURE.md`
**Why:** The factory must run on the CLI alone — no VS Code extension, no `gh`, no pull requests — and the worktree rule must be enforced, not just described.
**Impact:** Agents never commit to `main`/`master`/`base`, never commit to a branch that already has a worktree, and never merge. `Pending Merge` now means waiting for human approval to merge into `main` or a feature branch. The worktree procedure lives in a skill so it can be followed step by step.
