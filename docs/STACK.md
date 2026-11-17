# STACK — software factory

The tools the factory needs and the commands they run. This is the first source for any command
an agent needs. Do not guess commands.

## What the factory is made of

No application runtime, no database. The factory is Markdown rules, agent definitions, and
Python scripts that run on the standard library alone. The one build step is the board UI's
Tailwind stylesheet, and it produces a committed file — the viewer itself needs no Node.

| Piece | Version | Where |
|---|---|---|
| Python | 3.9+ | every script under `.kilo/skills/*/scripts/` |
| Node.js | 22 | the dev container, the Playwright MCP, the Tailwind build |
| Playwright | the global install in the dev container | the QA capture script |
| Chromium | `/usr/bin/chromium` in the dev container | the QA capture script |
| Tailwind CSS | 4.3.5 (`@tailwindcss/cli`) | `.kilo/skills/board/ui/`, builds the board stylesheet |
| Geist Sans / Geist Mono | variable woff2, SIL OFL | `.kilo/skills/board/static/fonts/` |

## Commands

```bash
# Board viewer (read-only dashboard on port 15180)
python3 .kilo/skills/board/scripts/board_serve.py --port 15180

# Rebuild the board stylesheet after a class change (needs Node 22, not needed at runtime)
npm --prefix .kilo/skills/board/ui run build
# output: .kilo/skills/board/static/board.css (committed)

# Show the board
python3 .kilo/skills/board/scripts/board.py show

# Create the worktree for a board row
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board BOARD-00X --base main

# Project-local mode (required default); restart Kilo after a change
python3 .kilo/skills/git-worktree/scripts/worktree.py mode status
python3 .kilo/skills/git-worktree/scripts/worktree.py mode optional
python3 .kilo/skills/git-worktree/scripts/worktree.py mode required
# Link a finding to the original repo-specific workspace
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board BOARD-FIX --reuse BOARD-PARENT --repo ID
# All-repository handoff; human previews/applies lifecycle actions
python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board BOARD-ID
python3 .kilo/skills/git-worktree/scripts/worktree.py merge --board BOARD-ID --apply
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board BOARD-ID --repo ID
# Explicit human loss approval only:
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board BOARD-ID --repo ID --apply --discard

# Guard rails
python3 .kilo/skills/git-worktree/scripts/guard.py check-git -- "git merge feat/x"
python3 .kilo/skills/git-worktree/scripts/guard.py check-policy
python3 .kilo/skills/git-worktree/scripts/guard.py check-repos
```

## Ports

Lifecycle `--board`/`--repo` may repeat; `--target` overrides the saved base. Merge preflights all
clean sources/targets except live board metadata, readiness and commits; non-atomic failures
preserve progress. Human completes conflicts in existing checkouts, then retries. No agent merges.
QA capture uses the existing `browser-review.mjs` flags `--storage-state <ignored-local.json>` and
`--navigation <ignored-local.json>`; schema and destructive-approval rules are in the QA skill.
Storage-state or login also requires ignored navigation config with an app-specific
`authenticatedSelector`, for example `"authenticatedSelector": "[data-testid='signed-in-shell']"`.
Check the signed-in marker is visible after navigation settles, before capture; route-only proof
can accept a same-URL MFA/SSO gate. Do not use password-input heuristics. Page-changing navigation
declares the final destination via an existing step, e.g. `{"action":"waitForURL","path":"/app"}`.

| Port | What | Notes |
|---|---|---|
| 15180 | Board viewer | Read-only. `board_serve.py`. Forwarded by the dev container. |
| 8080 | Gateway | Forwarded by the dev container for project work. |
| 10350 | Tilt UI | Forwarded by the dev container for project work. |

## Environment

`BASH_ENV` and `KILO_CONFIG` are set by `.devcontainer/devcontainer.json`. See
`docs/ENVIRONMENT.md`.

## What a project adds

The factory has no application stack. A project's own runtime, package managers, database and
ports live in that project's `docs/STACK.md`. Never read a project's stack from this file.
