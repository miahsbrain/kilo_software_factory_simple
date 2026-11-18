# Factory Handover

## Session Notes

BOARD-122 adds deterministic bootstrap in `.kilo/worktrees/add-deterministic-project-and-app-bootstrap`, branch `chore/add-deterministic-project-and-app-bootstrap`. New stdlib `bootstrap.py` and `/bootstrap` replace manual copying, preserve the four-directory harness and flat repository map, and initialize Git without automatic staging/commits. Existing `/projects/kilo_inhouz_ai/project` and its apps are untouched. The user authorized committing this factory change and preparing its human merge handoff; no agent merge, push or install. The coordinator owns live-board updates.

BOARD-123 fixes independent-app ignores and now incorporates user clarification (ADR-084): app Git is optional, project Git mandatory. Ask separate app Git versus project tracking unless already specified; require `app <name> --git separate|project`. Both modes snapshot current project ignores minus only `apps/*/`. Separate mode initializes/maps; project mode adds only `!/apps/<name>/` to control ignores, without nested Git/map entry or irrelevant init guard check. The local snapshot protects root-relative runtime paths inside integrated apps too. Missing/nonregular/symlink ignore sources fail before creation. No app instructions/harness. Later project ignore changes do not automatically refresh snapshots.

Next action: human reviews the committed branch and generated lifecycle handoff for BOARD-122 and BOARD-123 together. The clarification's focused bootstrap suite passed 16 tests in 6.253s, exit 0; independent re-review found no blocker. Exact command/run history is in `changelog/CHANGELOG.md`. Lifecycle readiness is verified after the authorized commit and recorded on the live board before Pending Merge.

Staging caveat: the pre-existing shared `.git/info/exclude` ignores `.kilo/`, hiding the three new files (`bootstrap.py`, `test_bootstrap.py`, `.kilo/command/bootstrap.md`) from ordinary status until tracked. Explicitly include only those new source files in the authorized commit; do not change the shared exclude.

## Current Harness

The factory supplies the root working agreement, seven specialist agents, short commands, and board, workspace, bootstrap, QA capture, and unslop tools. `README.md` describes canonical CLI bootstrap; `PROJECT_STRUCTURE.md` maps the actual layout. Each project owns its copied harness. The factory map retains `control: .` and the existing `project: project`; a new project's template map contains only `control: .`.

For an app with an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Develop reusable components first using Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme; choices are not limited to installed libraries. Reuse suitable components without preserving unwanted styling, then compose screens from them. New applications and user-facing features present the frontend flow for user approval, using labeled fixtures where needed, before backend/APIs and integration. Backend-only maintenance needs no unrelated frontend work. Component galleries are optional. UI critique and a separate general read-only unslop task run in parallel against shared capture evidence; consolidate meaningful findings once. A proven harmless development-only missing favicon is nonblocking, with raw evidence retained.

## Operations

- Board: `board.py` maintains the ignored live board in the main checkout; `board_serve.py --port 15180` serves its offline viewer.
- Workspaces: All FEATURE implementation uses an assigned linked worktree, not primary checkout. Explicitly assigned features may share its branch/worktree using `create --board NEW --reuse EXISTING --repo ID`; existing reuse code accepts Feature rows, preserving branch/base and assignment ownership. No auto branch switching or permissions/saved-mode edits. Project-tracked apps use control's worktree; separate apps their mapped repo's worktree. Initial scaffolding/bootstrap needs no prior commit/worktree; feature implementation waits for an authorized initial commit and linked worktree. Optional mode remains for non-feature maintenance.
- QA: `browser-review.mjs` captures shared evidence under ignored `artifacts/`; `check-finding.py` validates actionable findings and `ledger.py` tracks bounded review rounds.
- Bootstrap: from the factory checkout root, `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project` defaults to `project/`; optional `--destination <new-path>` requires an existing parent. From the initialized project control root, `python3 .kilo/skills/git-worktree/scripts/bootstrap.py app <name> --git separate|project` creates only `apps/<name>` with explicit Git ownership, mapping only separate repos. No manual copy, scaffolding, app instructions, installs or implicit initial commit. Both modes refuse existing paths/symlinks and invalid maps. Failures retain partial state. Only the template blank board is copied and ignored; the factory template board stays tracked. Local QA navigation is optional runtime input, not copied source config.

## Mechanics Inventory

| Existing function/module | Responsibility |
|---|---|
| `.kilo/skills/git-worktree/scripts/bootstrap.py`, `project(source, destination)` and `app(source, root, name, git_mode)` | Effectful: validated project copy then init; or app-local ignores then separate repo init/atomic map replacement, or project tracking via targeted directory unignore. Source is the executing checkout. Init guard checks run only where init occurs; hard denials/errors stop those paths, scoped consent handles `ask`. Partial failures are reported/retained, never deleted. |
| `.kilo/skills/git-worktree/scripts/guard.py:56`, `cmd_sync()` at line 934 | Effectful: copy `agent`, `command`, `skills`, `policies` and harness ignore file into mapped project controls; regenerate permissions with existing policy logic. Apps retain inherited config and local exclusions without generated instructions. |
| `.kilo/skills/git-worktree/scripts/worktree.py:693`, `cmd_create(args, cwd)` | Effectful: existing workspace creation, config initialization, env/navigation provisioning and exclusions; no app/repo/worktree instruction generation. |
| `.kilo/skills/git-worktree/scripts/scope.py:8`, `read_existing(path)`; line 16, `exclude_file(repo)`; line 24, `ensure_ignored(repo)` | Effectful: retained filesystem helpers for `.kilo/` and `kilo.jsonc` local exclusions. Pointer templates, generation and scope lookup removed. Existing instruction files and prior local exclusions are not deleted. |

## Testing

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_bootstrap` from `.kilo/skills/git-worktree/scripts` passed 16 tests in 6.253s, exit 0. Initial clarification run had one failure in 5.843s: project-root-relative runtime ignores did not reach integrated app paths; both modes now receive the same safe local snapshot. Coverage retains project copy/prerequisites/static ignores/init fault injection, adds required-choice refusal without mutation, explicit separate/project behavior, integrated source listed by control Git without nested Git or mapping, preserved prior patterns and secrets/runtime outputs, and both-mode unsafe path/map refusals. Project-tracked mode succeeds under an init deny while separate mode still refuses. No staged files/commits. Historical BOARD-122/123 results remain in the engineering log. Existing lifecycle scripts are unchanged; Feature reuse support was verified by code inspection, not a new regression or lifecycle run.

## Limitations

Verification is limited to focused bootstrap fixtures and file review; no full suite, build, install, UI capture, real-project initialization/sync or live application runtime. No UI was implemented. Git-init failure evidence is fault injection, not filesystem/disk-failure simulation. No concurrent writers/hostile filesystem race guarantee; preflight and map replacement are not a cross-process transaction. Historical ADRs/changelog entries remain unchanged; ADR-084 supersedes automatic app Git and clarifies feature worktree assignment. Permissions, saved mode and existing lifecycle scripts are unchanged.

## Documents

See `PROJECT_STATE.md` for the active task, `DECISIONS.md` for approvals, `UI-UX.md` for focused UI review, `STACK.md` for commands, and `changelog/CHANGELOG.md` for engineering history. Product rules belong to the independent project, not this factory.
