# Factory Handover

## Session Notes

BOARD-121 simplifies factory/template instructions and existing sync/worktree mechanics in `.kilo/worktrees/simplify-factory-harness-and-project-bootstrap`, branch `chore/simplify-factory-harness-and-project-bootstrap`. The compact agreement replaces layered architect rules. Sync carries four harness directories without scope/catalog propagation; app/repo/worktree instruction generation is removed. Existing `project/` and application source are untouched. The user authorized continuing from staged preparation to a local commit and human merge handoff; no agent merge or push.

Next action: human reviews the branch and uses the generated lifecycle handoff after clean-worktree verification. Independent combined-diff review found no blocking issue. The template board's obsolete gallery gate was corrected with explicit user authorization, without changing the live board or permissions. Chunk 2's single focused unittest invocation passed all 11 tests in 4.530s, exit 0, in temporary fixtures. The exact command and selected cases are in `changelog/CHANGELOG.md`.

## Current Harness

The factory supplies the root working agreement, seven specialist agents, short commands, and existing board, workspace, QA capture, and unslop tools. `README.md` describes full-copy bootstrap; `PROJECT_STRUCTURE.md` maps the actual layout. Each project owns its copied harness. The factory map retains `control: .` and the existing `project: project`; a new project's template map contains only `control: .`.

For an app with an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Develop reusable components first using Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme; choices are not limited to installed libraries. Reuse suitable components without preserving unwanted styling, then compose screens from them. New applications and user-facing features present the frontend flow for user approval, using labeled fixtures where needed, before backend/APIs and integration. Backend-only maintenance needs no unrelated frontend work. Component galleries are optional. UI critique and a separate general read-only unslop task run in parallel against shared capture evidence; consolidate meaningful findings once. A proven harmless development-only missing favicon is nonblocking, with raw evidence retained.

## Operations

- Board: `board.py` maintains the ignored live board in the main checkout; `board_serve.py --port 15180` serves its offline viewer.
- Workspaces: `worktree.py` and `guard.py` retain lifecycle, policy, and authorization checks; use the assigned workspace and existing procedures.
- QA: `browser-review.mjs` captures shared evidence under ignored `artifacts/`; `check-finding.py` validates actionable findings and `ledger.py` tracks bounded review rounds.
- Bootstrap: copy the full remaining harness, initialize Git immediately, and request explicit authorization before staging or initial commits. Initialize a genuinely new app repository when its directory is created and map it before work. No fixed app slots or app-level rules are required.

## Mechanics Inventory

| Existing function/module | Responsibility |
|---|---|
| `.kilo/skills/git-worktree/scripts/guard.py:56`, `cmd_sync()` at line 934 | Effectful: copy `agent`, `command`, `skills`, `policies` and harness ignore file into mapped project controls; regenerate permissions with existing policy logic. Apps retain inherited config and local exclusions without generated instructions. |
| `.kilo/skills/git-worktree/scripts/worktree.py:693`, `cmd_create(args, cwd)` | Effectful: existing workspace creation, config initialization, env/navigation provisioning and exclusions; no app/repo/worktree instruction generation. |
| `.kilo/skills/git-worktree/scripts/scope.py:8`, `read_existing(path)`; line 16, `exclude_file(repo)`; line 24, `ensure_ignored(repo)` | Effectful: retained filesystem helpers for `.kilo/` and `kilo.jsonc` local exclusions. Pointer templates, generation and scope lookup removed. Existing instruction files and prior local exclusions are not deleted. |

## Testing

One `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v ...` invocation from `.kilo/skills/git-worktree/scripts` passed 11 selected lifecycle cases. Coverage includes control-only template maps with absent/empty apps; arbitrary real app IDs and unregistered-app rejection; four-directory control bootstrap, dry-run immutability and no automatic initial commit; app instruction absence and handwritten-file preservation; inherited permission ordering in both modes; local permission regeneration; env/navigation copy and provisioning exclusions. Tests use existing temporary fixtures, including their isolated Git setup/commits, not real workspace Git mutations. No new helper/tool was added.

## Limitations

Verification is limited to the 11 selected fixture tests and file review; no full suite, build, install, UI capture, real-project sync or live application runtime. No agent merge or push. `docs/RUNNING.md` is absent in this factory; `docs/STACK.md` and existing engineering-log unittest commands informed verification. Improved visual output has not been demonstrated on an actual UI task. Historical ADRs and changelog entries remain unchanged; ADR-080 supersedes the old instruction and gate policies for future factory/project copies, with ADR-082's UI-library/style-choice correction.

## Documents

See `PROJECT_STATE.md` for the active task, `DECISIONS.md` for approvals, `UI-UX.md` for focused UI review, `STACK.md` for commands, and `changelog/CHANGELOG.md` for engineering history. Product rules belong to the independent project, not this factory.
