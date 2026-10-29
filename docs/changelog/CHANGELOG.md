# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-10-29] Close the build loop
**Type:** Chore
**Board:** BOARD-007 | **Branch:** chore/close-the-build-loop-iteration-rule
**Changed:** `AGENTS.md` (§B4 lane rules, §B6), `docs/UI-UX.md` (§3, renumbered §4–§6), `.kilo/agent/{qa-reviewer,ui-critic,frontend-dev,backend-dev,mobile-dev}.md`, `.kilo/skills/{board,qa-review}/SKILL.md`, `.kilo/command/decide.md`, `docs/DECISIONS.md`
**Why:** The factory had the lanes but not the loop, had the anti-slop rules but no user-centred standard, and had "reuse before creation" as an unverifiable instruction.
**Impact:** A row cannot reach `Pending Merge` while a Fix row it spawned is open; every Fix row runs the same lanes; the original row is re-verified after fixes merge; a finding that repeats three times blocks the row instead of retrying. `docs/UI-UX.md` §3 defines U1–U8 (user-centred) and M1–M10 (modern), enforced by both the QA lane and the critique. Builders must report the existing code they found before creating anything.

## [2026-10-29] Worktree names derive from the board row
**Type:** Chore
**Board:** BOARD-006 | **Branch:** feat/worktree-naming-from-board
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md` (§B4), `.kilo/command/{board,run}.md`, `docs/DECISIONS.md`
**Why:** `create <slug> --type` had `--type` default to `feat` and the slug was free-hand, so a bug fix could easily land on `feat/some-name` and the worktree did not say what it was fixing.
**Impact:** `worktree.py create --board BOARD-00X` is now the only way to create a worktree. The branch type comes from the row's `Type` column and the slug from its task title, and the script writes the worktree path and branch back onto the row in the main checkout. The positional slug and `--type` flags are gone.
