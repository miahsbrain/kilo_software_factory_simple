# Project Structure

This is the factory repository. Product work belongs to a separate project repository; the existing ignored `project/` is not changed by BOARD-121.

| Path | Purpose |
|---|---|
| `AGENTS.md` | Compact root working agreement |
| `.kilo/agent/` | Seven short specialist prompts with preserved execution frontmatter |
| `.kilo/command/` | Short workflow shortcuts |
| `.kilo/skills/` | Planning, board, lifecycle, QA, and unslop procedures and existing tools |
| `.kilo/policies/`, `kilo.jsonc` | Guard policy and generated permissions/configuration |
| `.kilo/repos.json` | Factory map: `control` at `.`, existing `project` at `project` |
| `.kilo/worktrees/` | Ignored assigned change workspaces |
| `.devcontainer/` | Development environment and output protections |
| `docs/` | Factory handover, state, structure, architecture, decisions, run/stack notes, and engineering history |
| `docs/BOARD.md` | Local ignored live board in the main checkout |
| `artifacts/` | Ignored shared captures and review reports in the control main checkout |
| `templates/project/` | Blank product documents, compact agreement, ignore rules, and control-only repo map |
| `project/` | Existing independent ignored project repository; not migrated |

The specialist catalogue and `.kilo/scopes/` instruction layer are removed. The template has no API/web/mobile boilerplate directories or app-level rules. `apps/` starts empty (Git does not preserve empty directories); actual application directories and repository mappings are added only when needed. A new project copies the remaining complete harness from the factory as described in `README.md`; the template does not duplicate it.

BOARD-121 chunk 2 aligns the existing scripts: `guard.py` syncs the four supported harness directories into project controls, `worktree.py` no longer generates app/repo/worktree instructions, and `scope.py` retains only inherited-harness exclude helpers. No application source is changed.
