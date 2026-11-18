# Project Structure

Record actual paths as the project grows; preserve an existing project's layout.

| Path | Purpose |
|---|---|
| `AGENTS.md` | Root working agreement |
| `DOMAIN.md`, `ROADMAP.md`, `CHANGELOG.md` | Product scope, planned work, and user-requested product changelog |
| `.kilo/agent/`, `command/`, `skills/`, `policies/` | Harness copied from the factory during bootstrap |
| `.kilo/repos.json` | Actual repository IDs/paths, initially only `control: .` |
| `kilo.jsonc` | Copied Kilo configuration and generated permissions |
| `apps/` | Initially empty; create real application repositories only when needed |
| `.kilo/worktrees/` | Ignored assigned change workspaces |
| `docs/` | Concise current project context, decisions, and engineering history |
| `docs/BOARD.md` | Local live board, ignored after bootstrap |
| `artifacts/` | Ignored shared QA captures and review reports |

Git does not preserve empty directories. Initialize Git in a genuinely new app directory immediately when created, then register its ID/path before work. There are no fixed app slots, scope-rule files, or app-level `AGENTS.md` requirements. See `README.md` for full harness copy and initial-commit authorization.
