# Project Structure

Record actual paths as the project grows; preserve an existing project's layout.

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Root working agreement |
| `DOMAIN.md`, `ROADMAP.md`, `CHANGELOG.md` | Product scope, planned work, and user-requested product changelog |
| `.claude/agents/`, `commands/`, `skills/`, `policies/` | Harness copied from the factory during bootstrap |
| `.claude/repos.json` | Actual repository IDs/paths, initially only `control: .` |
| `.claude/settings.json` | Generated Claude Code settings: static guard rules and the `guard.py hook` PreToolUse hook |
| `apps/` | Initially empty; create real application repositories only when needed |
| `.claude/worktrees/` | Ignored assigned change workspaces |
| `docs/` | Concise current project context, decisions, and engineering history |
| `docs/BOARD.md` | Local live board, ignored after bootstrap |
| `artifacts/` | Ignored QA captures and review reports shared by all services in the primary control checkout |

Git does not preserve empty directories. Initialize Git in a genuinely new app directory immediately when created, then register its ID/path before work. There are no fixed app slots, scope-rule files, or app-level `CLAUDE.md` requirements. See `README.md` for full harness copy and initial-commit authorization.
