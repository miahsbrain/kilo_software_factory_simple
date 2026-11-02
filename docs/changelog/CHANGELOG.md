# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-11-02] Give a work surface a pointer instead of a copy of the rules
**Type:** Chore
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `.kilo/skills/git-worktree/scripts/{scope.py,guard.py,worktree.py}`, `.kilo/skills/board/scripts/board.py`, `.kilo/skills/git-worktree/SKILL.md`, `.kilo/scopes/service.md`, `AGENTS.md`, `docs/{DECISIONS,HANDOVER,PROJECT_STRUCTURE}.md`, `docs/changelog/CHANGELOG.md`
**Why:** The harness was copied into every work surface, so a factory change had to be re-applied in every application repository and the factory could not grow without touching them all. The board was also unreachable from inside a work surface, because the harness looked for `apps/<repo>/docs/BOARD.md`.
**Impact:** The harness stays in the control repo. A work surface receives one generated file, `AGENTS.md`, that names the project, the canonical scope rules and the unit's documentation; it is listed in the repository's `.git/info/exclude`, so it is never committed. `guard.py sync --all` refreshes every pointer in one command. The harness now finds the control repo by walking up, so the board, the repo map and the guard rails work from inside any work surface. ADR-058, ADR-059 and ADR-060 record the decisions. No application behaviour changes.

## [2026-11-02] Split the factory from the project
**Type:** Chore
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `AGENTS.md` (§A1 "The factory and the project", §A2 boot sequence), `README.md`, `.gitignore` (ignores `/project/`), `.kilo/repos.json` (the control repo only), `docs/{BOARD,DECISIONS,ENVIRONMENT,HANDOVER,PROJECT_STATE,PROJECT_STRUCTURE,README,STACK}.md` (rewritten for the factory), `docs/changelog/CHANGELOG.md`, `templates/project/**` (new: the blank project skeleton)
**Why:** The factory and the product shared one repository, so 79 project handover files, the platform architecture and the product's risk register were committed to the software factory, and the factory's board carried product rows.
**Impact:** The factory holds the harness only — rules, agents, commands, skills, policies, scope rules and the blank project skeleton. The Inhouz Cloud AI platform is its own git repository in `project/`, with its own board, documentation set, domain rules and 75 application repositories. `guard.py check-repos` exits 0 in both. The decision log is split: ADR-001 to ADR-099 are the factory's, the project's own decisions start at ADR-100. A project copies the harness in and owns the copy, so a factory change does not reach a project automatically. No behaviour changes.

## [2026-10-30] Deny every tool read access to git config, credential and .env files
**Type:** Security
**Board:** - | **Branch:** main (uncommitted)
**Changed:** `.kilo/policies/git-policy.json` (expanded `hidden_paths`, added `allow` list and edit denials), `.kilo/skills/git-worktree/scripts/guard.py` (expands `hidden_paths` into `read`/`grep`/`glob`/`list` deny rules and honours the allow list; `check-policy` compares every generated tool key), `kilo.jsonc` (generated), `.devcontainer/kilo-redact.sh` (new protected-file guard in the `$BASH_ENV` startup file), `.devcontainer/test-kilo-redact.sh` (10 guard checks), `.devcontainer/devcontainer.json` (`KILO_CONFIG` points at the root `kilo.jsonc`, so no subfolder copy is needed), `.kilo/skills/git-worktree/SKILL.md` (§3), `docs/DECISIONS.md` (ADR-052), `docs/HANDOVER.md`
**Why:** A git config or credential file can hold a token in a URL, a credential helper or an extra HTTP header, and a `.env` file holds application secrets. The agent never needs to read any of them, but only the `read` tool was blocked before, and a nested app repository did not load the root config.
**Impact:** `read`, `grep`, `glob` and `list` deny `.env`, `.env.*` (except `.env.example`), `.git/config`, `*.git/config`, submodule configs, `.git-credentials`, `~/.gitconfig`, the XDG git config and credential stores, `.npmrc`, `*.pem`, `*.key`, `*.p12` and `id_rsa*`. `edit` denies the same secret files. The `$BASH_ENV` guard refuses any `bash -c` command whose text names a protected file, in every subfolder and every repository; `.env.example` and `process.env` stay allowed. `KILO_CONFIG` points at the root config so nested repositories inherit it without a copy. No application behaviour changes. A Kilo restart is needed for the new permission block; the shell guard is active as soon as the file is installed. Shell commands that merely mention `.env` (for example a commit message) are also refused by the guard.

## [2026-10-30] Redact credentials from every shell command's output
**Type:** Security
**Board:** BOARD-002 | **Branch:** chore/redact-credentials-from-every-shell-command
**Changed:** `AGENTS.md` (§B11 — a credential never reaches a transcript through a URL), `.devcontainer/kilo-redact.sh` (new), `.devcontainer/test-kilo-redact.sh` (new), `.devcontainer/devcontainer.json` (`remoteEnv.BASH_ENV`, install step in `postCreateCommand`), `docs/{ENVIRONMENT,STACK,RISKS,DECISIONS,PROJECT_STATE}.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-redact-credentials-from-shell-output.md`
**Why:** The machine's global git config carried a `url.https://<token>@github.com/.insteadOf` rewrite, so `git remote -v` printed the credential in plaintext and it reached an agent transcript. The rewrite is removed — the token now lives in `/home/node/.git-credentials` (mode `600`) behind git's credential helper — and a `sed` filter installed as the container's `$BASH_ENV` startup file now scrubs both output streams of every shell command.
**Impact:** No URL carries a credential, so no routine git command can disclose one. `$BASH_ENV` is used because Kilo Code runs shell tools as `/bin/bash -c` and Debian's `~/.bashrc` returns immediately for a non-interactive shell. Output with no credential is byte-identical, including binary output; the exit code, the stdout/stderr split and the output order are preserved. The filter needs a container rebuild or window reopen to activate. The token itself was printed once and must be rotated at GitHub.

## [2026-10-30] Multi-repo support in the board and the git tools
**Type:** Feature
**Board:** BOARD-003, BOARD-004 | **Branch:** feat/multi-repo-support-in-the-board, docs/multi-repo-rules-agent-and-documentation
**Changed:** `.kilo/repos.json` (new), `.kilo/scopes/{web,mobile,api}.md` (new), `.kilo/skills/board/scripts/board.py` (`Repos` column, `add-column`, `add --repos`, `set-field --field repos`, strict row parsing), `.kilo/skills/board/scripts/board_serve.py` (column list), `.kilo/skills/git-worktree/scripts/worktree.py` (`create --repo`, board-driven `cleanup`/`verify`, repo-wide `list`), `.kilo/skills/git-worktree/scripts/guard.py` (`sync`, `check-repos`, policy root follows the shell, sync writes into the shell's tree), `.kilo/policies/git-policy.json` (`.kilo/scopes/*.md` asks), `kilo.jsonc` (generated), `.kilo/skills/{board,git-worktree}/SKILL.md`, `AGENTS.md` (§A1 multi-repo, §A7 script table, §B1, §B3 `Repos` column, §B4 repo-aware worktrees, the control-repo subsection), `.kilo/agent/docs-writer.md` (repository-aware units), `README.md` (multi-repo section), `apps/{web,mobile,api}/AGENTS.md` (synced copies), `docs/{PROJECT_STRUCTURE,HANDOVER,DECISIONS,README}.md`, `docs/handover/{README,web,mobile,api}.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-multi-repo-support-in-the-board.md`
**Why:** An application that keeps its own git repository under `apps/` could not be worked in: nothing could name the repo a row belonged to, nothing could give that repo the same guard rails, and the rules and the documentation still described a single repository.
**Impact:** The board gains a `Repos` column, migrated by `board.py add-column` instead of a hand edit. `worktree.py create --repo <id>` creates the worktree in that repo and keeps the board in the control repo. `guard.py sync --repo <id>` copies the `.kilo/` slice, the scope rules and the permission map into the target repo; `guard.py check-repos` proves the map and the `apps/` layout agree. `guard.py check-policy` now reads and writes the policy and config of the tree the shell is in, so a builder in a worktree no longer rewrites the main checkout; `guard.py sync` does the same and no longer fails when the target is the control repo itself. `AGENTS.md` and the `docs-writer` agent describe the control repo, the work surfaces and the repo map, and the scope rules are canonical in `.kilo/scopes/<id>.md` with `apps/<id>/AGENTS.md` as their synced copies.

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
