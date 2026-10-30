# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-10-30] A documentation agent owns the application memory map
**Type:** Feature
**Board:** BOARD-002 | **Branch:** feat/add-a-documentation-agent-that-writes
**Changed:** `.kilo/agent/docs-writer.md` (new), `.kilo/command/handover.md` (rewritten, now routed to `docs-writer`), `docs/handover/{README,web,mobile,api}.md` (new), `AGENTS.md` (§A7 agent table, §A10 doc table, §B1 doc table, §B2), `docs/{README,PROJECT_STRUCTURE,HANDOVER,DECISIONS}.md`, `README.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-docs-writer-and-application-memory-map.md`
**Why:** The handover was one file written from memory of a system, and a reader could not tell which parts of the code were pure and which touched the outside world.
**Impact:** `/handover` now runs the `docs-writer` agent, which reads the whole codebase on its first run in a session and writes one memory map per application under `docs/handover/` plus a global index. Every module is marked pure, reactive or effectful, and every claim carries a `file:line`. `docs/HANDOVER.md` stays as the factory's own handover. No behaviour change to the build, QA or merge lanes.

## [2026-10-30] One guard-rail policy, two enforcement layers
**Type:** Feature
**Board:** BOARD-001 | **Branch:** feat/add-a-permission-file-and-git
**Changed:** `.kilo/policies/git-policy.json` (new), `.kilo/skills/git-worktree/scripts/guard.py` (`check-git`, `check-policy`, `policy`), `kilo.jsonc` (generated `permission` map), `.kilo/skills/git-worktree/SKILL.md` (§3), `AGENTS.md` (§A7 table, §B9, §B11), `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `.kilo/command/{run,closeout}.md`, `docs/{PROJECT_STRUCTURE,HANDOVER,DECISIONS,PROJECT_STATE}.md`, `README.md`, `docs/changelog/CHANGELOG.md`
**Why:** The guard rails were prose in `AGENTS.md` and nothing stopped an agent from running `git push`, committing on `main`, or switching branches inside a worktree.
**Impact:** One policy file is the source of truth for the guard rails. The generated `permission` map in `kilo.jsonc` now denies the irreversible git commands (`git push`, `git reset --hard`, `git clean`, `git checkout --`, `git branch -D`, a raw `git worktree remove`, `git filter-branch`, `git filter-repo`, `git reflog expire`, `git gc`, `git update-ref -d`) and asks before the rest that changes history or the remote. `guard.py check-git` adds the three context checks a keyword list cannot make: no commit on `main`/`master`/`base`, no branch switch inside a worktree, and no raw `git worktree remove`. Edits to the rules files ask first; the real `.env` and key files are denied. `guard.py check-policy` proves the two layers still match.

## [2026-10-29] Starter: front page, no test residue, empty board
**Type:** Chore
**Board:** BOARD-013 | **Branch:** chore/starter-repo-prep
**Changed:** `README.md` (new), `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, removed `artifacts/factory/qa/2026-10-29/BOARD-012/notes.md`, emptied `docs/BOARD.md`
**Why:** The repo is going public as a starter to plug into any project, so it needs a front page, no test residue, and a board that starts empty.
**Impact:** No behaviour change. A fresh clone has an empty board; the first row is added with `board.py add`. The handover and project state describe the starter, not a running project.

## [2026-10-29] One driver for the capture path, failures reported not routed around
**Type:** Chore
**Board:** BOARD-012 | **Branch:** chore/remove-cdp-and-report-failures
**Changed:** `.kilo/skills/qa-review/scripts/browser-review.mjs`, `AGENTS.md`, `.kilo/skills/qa-review/SKILL.md`, `.kilo/command/{ui,run}.md`, `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `docs/{UI-UX,STACK,HANDOVER,DECISIONS}.md`, `docs/changelog/CHANGELOG.md`
**Why:** The capture script advertised a CDP fallback it never had, and the incident behind the "ask before building a tool" rule was described with a protocol name instead of what actually happened.
**Impact:** The capture path drives Playwright only. `--chromium <path>` is a plain binary path handed to Playwright's launch, the resolution order is flag → env var → downloaded → system, and a missing chromium exits 2 with the searched list instead of being installed or replaced. A new rule makes an agent report a failed command, capture, or test instead of routing around it.

## [2026-10-29] One canonical artifacts folder, ask before building a tool
**Type:** Chore
**Board:** BOARD-010 | **Branch:** chore/one-artifacts-folder-and-ask-before
**Changed:** `.kilo/skills/qa-review/scripts/browser-review.mjs`, `.gitignore`, `AGENTS.md`, `docs/{UI-UX,HANDOVER,DECISIONS,PROJECT_STRUCTURE}.md`, `docs/changelog/CHANGELOG.md`, `.kilo/skills/qa-review/SKILL.md`, `.kilo/command/{ui,run}.md`, `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `apps/{web,mobile}/AGENTS.md`
**Why:** UI evidence was scattered across app folders, `docs/`, and `/tmp`, and an agent built a browser driver instead of asking, while Playwright was already installed globally.
**Impact:** All UI evidence lands under `artifacts/<scope>/qa/<date>/<task-id>/` in the main checkout; the capture script computes the path itself and writes `notes.md`. Review reports and ledgers stay in `docs/reviews/` — documents, not artifacts. A new rule makes an agent check for existing tooling and ask before building any.

## [2026-10-29] Live board viewer, bounded UI loop, gated UI tooling
**Type:** Feature
**Board:** BOARD-008, BOARD-009 | **Branch:** feat/live-board-viewer-html-dashboard-with
**Changed:** `.kilo/skills/board/scripts/board_serve.py` (new), `.kilo/skills/qa-review/scripts/{browser-review.mjs,check-finding.py,ledger.py}`, `.kilo/skills/board/scripts/board.py`, `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/{board,qa-review}/SKILL.md`, `.kilo/command/{board-view,run,ui}.md`, `.kilo/agent/{qa-reviewer,ui-critic}.md`, `kilo.jsonc` (Playwright MCP), `.devcontainer/devcontainer.json` (port 15180), `AGENTS.md`, `docs/{STACK,DECISIONS}.md`
**Why:** The markdown board is hard to scan, the UI critique → fix loop could run forever, and Playwright was installed but unreachable — so the agent built a browser driver by hand and looped proving it worked.
**Impact:** A read-only dashboard on port 15180 shows the lanes and the live worktrees. The QA loop is capped at 3 rounds with fingerprint dedupe and a ledger. The Playwright MCP is configured and the capture script resolves the global Playwright, so no hand-rolled browser client remains.
