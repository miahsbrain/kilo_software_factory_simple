# STACK — software factory

The tools the factory needs and the commands they run. This is the first source for any command
an agent needs. Do not guess commands.

## What the factory is made of

No application runtime, no database. The factory is Markdown rules, agent definitions, and
Python scripts that run on the standard library alone. The one build step is the board UI's
Tailwind stylesheet, and it produces a committed file — the viewer itself needs no Node.

| Piece | Version | Where |
|---|---|---|
| Python | 3.9+ | every script under `.opencode/skills/*/scripts/` |
| OpenCode | V2 | `opencode.jsonc`, `.opencode/agents/`, `.opencode/commands/`, five discoverable skills |
| Node.js | 22 | the dev container, the Playwright MCP, the Tailwind build |
| Playwright | the global install in the dev container | the QA capture script |
| Chromium | `/usr/bin/chromium` in the dev container | the QA capture script |
| Tailwind CSS | 4.3.5 (`@tailwindcss/cli`) | `.opencode/skills/board/ui/`, builds the board stylesheet |
| Geist Sans / Geist Mono | variable woff2, SIL OFL | `.opencode/skills/board/static/fonts/` |

## Commands

```bash
# Board viewer (read-only dashboard on port 15180)
python3 .opencode/skills/board/scripts/board_serve.py --port 15180

# Rebuild the board stylesheet after a class change (needs Node 22, not needed at runtime)
npm --prefix .opencode/skills/board/ui run build
# output: .opencode/skills/board/static/board.css (committed)

# Show the board
python3 .opencode/skills/board/scripts/board.py show

# Board refresh regressions (temporary fixture trees, no live server)
python3 .opencode/skills/board/scripts/test_board_serve.py

# Create the worktree for a board row
python3 .opencode/skills/git-worktree/scripts/worktree.py create --board BOARD-00X

# Existing lifecycle/env suite (scratch repositories only)
python3 .opencode/skills/git-worktree/scripts/test_env.py

# Security adapter boundary tests (temporary dummy repositories only)
node --test .opencode/plugins/factory-guard/guard.test.mjs

# Guard rails
python3 .opencode/skills/git-worktree/scripts/guard.py check-git -- "git merge feat/x"
python3 .opencode/skills/git-worktree/scripts/guard.py check-policy
python3 .opencode/skills/git-worktree/scripts/guard.py check-repos
```

## Ports

| Port | What | Notes |
|---|---|---|
| 15180 | Board viewer | Read-only. `board_serve.py`. Forwarded by the dev container. |
| 8080 | Gateway | Forwarded by the dev container for project work. |
| 10350 | Tilt UI | Forwarded by the dev container for project work. |

## Environment

The devcontainer is still the legacy Kilo container; its OpenCode port is pending.
`KILO_CONFIG` is not used by OpenCode. Native config reloads automatically.
The factory selects `opencode` as base when present; app repository base selection is unchanged.
Security enforcement for grep/glob target paths and automatic guards is pending.
See `docs/ENVIRONMENT.md`.

## What a project adds

The factory has no application stack. A project's own runtime, package managers, database and
ports live in that project's `docs/STACK.md`. Never read a project's stack from this file.
