# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-10-29] Worktree names derive from the board row
**Type:** Chore
**Board:** BOARD-006 | **Branch:** feat/worktree-naming-from-board
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md` (§B4), `.kilo/command/{board,run}.md`, `docs/DECISIONS.md`
**Why:** `create <slug> --type` had `--type` default to `feat` and the slug was free-hand, so a bug fix could easily land on `feat/some-name` and the worktree did not say what it was fixing.
**Impact:** `worktree.py create --board BOARD-00X` is now the only way to create a worktree. The branch type comes from the row's `Type` column and the slug from its task title, and the script writes the worktree path and branch back onto the row in the main checkout. The positional slug and `--type` flags are gone.

## [2026-10-29] Port super-board mechanics into factory scripts
**Type:** Chore
**Board:** BOARD-005 | **Branch:** feat/port-super-board-scripts
**Changed:** `.kilo/skills/git-worktree/scripts/guard.py` (new), `.kilo/skills/git-worktree/scripts/worktree.py` (new), `.kilo/skills/board/scripts/board.py` (new), `.kilo/skills/qa-review/scripts/browser-review.mjs` (new), `.kilo/skills/qa-review/scripts/check-finding.py` (new), `.kilo/skills/git-worktree/SKILL.md`, `.kilo/skills/board/SKILL.md` (new), `.kilo/skills/qa-review/SKILL.md` (new), `AGENTS.md`, `.kilo/agent/qa-reviewer.md`, `.kilo/command/{board,run,ui}.md`, `docs/{DECISIONS,README,UI-UX,PROJECT_STRUCTURE}.md`
**Why:** Rules that an agent is asked to follow by hand are not enforced. Upstream super-board splits every mechanical operation into a script and lets the agent supply judgment. Ported that split, with the delete guard made stricter than upstream.
**Impact:** Worktree creation, verification, and cleanup, board row edits, QA evidence capture, and finding validation are now deterministic commands. Deletion is refused outside the current linked worktree and inside the main checkout. The board is edited by script, not by hand.
