# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-10-29] Port super-board mechanics into factory scripts
**Type:** Chore
**Board:** BOARD-005 | **Branch:** feat/port-super-board-scripts
**Changed:** `.kilo/skills/git-worktree/scripts/guard.py` (new), `.kilo/skills/git-worktree/scripts/worktree.py` (new), `.kilo/skills/board/scripts/board.py` (new), `.kilo/skills/qa-review/scripts/browser-review.mjs` (new), `.kilo/skills/qa-review/scripts/check-finding.py` (new), `.kilo/skills/git-worktree/SKILL.md`, `.kilo/skills/board/SKILL.md` (new), `.kilo/skills/qa-review/SKILL.md` (new), `AGENTS.md`, `.kilo/agent/qa-reviewer.md`, `.kilo/command/{board,run,ui}.md`, `docs/{DECISIONS,README,UI-UX,PROJECT_STRUCTURE}.md`
**Why:** Rules that an agent is asked to follow by hand are not enforced. Upstream super-board splits every mechanical operation into a script and lets the agent supply judgment. Ported that split, with the delete guard made stricter than upstream.
**Impact:** Worktree creation, verification, and cleanup, board row edits, QA evidence capture, and finding validation are now deterministic commands. Deletion is refused outside the current linked worktree and inside the main checkout. The board is edited by script, not by hand.

## [2026-10-29] CLI-only worktree skill and branch protection
**Type:** Chore
**Board:** BOARD-004 | **Branch:** feat/cli-worktree-skill
**Changed:** `.kilo/skills/git-worktree/SKILL.md` (new), `AGENTS.md` (§B4, §B11), `.kilo/command/board.md`, `.kilo/command/run.md`, `.kilo/command/closeout.md`, `docs/DECISIONS.md`, `docs/RISKS.md`, `docs/PROJECT_STRUCTURE.md`
**Why:** The factory must run on the CLI alone — no VS Code extension, no `gh`, no pull requests — and the worktree rule must be enforced, not just described.
**Impact:** Agents never commit to `main`/`master`/`base`, never commit to a branch that already has a worktree, and never merge. `Pending Merge` now means waiting for human approval to merge into `main` or a feature branch. The worktree procedure lives in a skill so it can be followed step by step.
