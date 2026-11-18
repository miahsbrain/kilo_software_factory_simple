# Project Structure

This is the factory repository. Product work belongs to a separate project repository; the existing ignored `project/` and its apps are not changed by BOARD-122.

| Path | Purpose |
|---|---|
| `AGENTS.md` | Compact root working agreement |
| `.kilo/agent/` | Seven short specialist prompts with preserved execution frontmatter |
| `.kilo/command/` | Short workflow shortcuts |
| `.kilo/skills/git-worktree/scripts/bootstrap.py` | Deterministic project copy/Git initialization and explicit separate/project Git ownership for `apps/<name>`; `/bootstrap` shortcut |
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

The specialist catalogue and `.kilo/scopes/` instruction layer are removed. The template has no API/web/mobile boilerplate directories or app-level rules. `bootstrap.py project` from the factory checkout root creates `project/` by default, or a new `--destination` whose parent exists. It copies the blank template and four-directory harness from the executing checkout, plus exact harness ignore/config, creates empty `apps/`, then initializes Git without staging/commits. The template does not duplicate the harness. The blank template board remains tracked; its static ignore rules make the copied board local/ignored.

`bootstrap.py app <name> --git separate|project` from an initialized project control root requires explicit app Git ownership; ask the user unless already specified. Project Git remains mandatory. Both modes create only `apps/<name>` with a safe app-local ignore snapshot. `separate` initializes Git and maps its real ID/path; `project` creates no nested repo/map entry and adds a targeted control-repo unignore, preserving secret/runtime rules. Empty `apps/` may be absent after checkout. Existing paths/symlinks, invalid names/maps and collisions are refused. No scaffolding, instructions, installs or arbitrary destination. Partial state is retained. Local QA navigation is optional runtime input, not bootstrapped. All feature implementation uses assigned linked worktrees after an authorized initial commit, with explicitly assigned features allowed to share a branch/worktree via `--reuse`; project-tracked apps use control, separate apps their mapped repo. No permission/mode changes.

BOARD-121 chunk 2 aligns the existing scripts: `guard.py` syncs the four supported harness directories into project controls, `worktree.py` no longer generates app/repo/worktree instructions, and `scope.py` retains only inherited-harness exclude helpers. No application source is changed.
