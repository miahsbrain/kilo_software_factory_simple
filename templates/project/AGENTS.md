# Working Agreement

Build useful, distinctive software. Favor clear code, focused modules, existing conventions, and the smallest sound solution. Avoid speculative abstractions.

Understand the task before editing. Ask only when a missing decision materially affects behavior, scope, cost, security, or an expensive-to-reverse choice.

Treat the user-chosen workspace as the boundary: verify resolved control/target roots before bootstrap, app or worktree writes and stop on mismatch; never enter a sibling, reuse an unrelated board/worktree path or infer a destination from a display/service name without explicit user approval. Project bootstrap defaults to factory-local `project/`; ASK before using external `--destination` with `--allow-outside` (the flag is capability, not approval).

Use `/bootstrap` and the README's CLI for new services under `apps/<service-name>`. Ask for a meaningful product-role name and separate/project Git ownership if unclear; invoke `bootstrap.py app <service-name> --git separate|project` from this control root. Project Git is mandatory; only separate repos are mapped. Track source, product docs and `services.json`, not local harness/config/devcontainer/generated root instructions/live board. Bootstrap is authorized to stage intended initial files and create exactly one initial commit only in genuinely new repos created by that invocation. Never manually copy, reinitialize, or auto-commit existing control/app/factory repos. Restore ignored tooling using the factory CLI without staging/commits.

All FEATURE implementation must use an assigned linked worktree, not the primary checkout. Explicitly assigned features may share its worktree/branch via `worktree.py create --board NEW --reuse EXISTING --repo ID`; preserve scope/ownership, never auto-switch branches. Apps tracked in project Git use the control worktree; separate apps use their own mapped repo worktree. Bootstrap creates the authorized initial commit that enables worktrees; feature source implementation must wait for its success. Optional workspace policy remains available for non-feature maintenance; do not change saved mode or permissions to encode feature assignments.

For new applications and user-facing features, build the frontend flow for user approval before implementing the backend or APIs. Use clearly labeled fixtures when needed; never present mocked behavior as integrated. Backend-only maintenance does not require unrelated frontend work.

Design around the user's actual task, content, and product character. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user has already specified the direction. Develop reusable components before screens using Tailwind CSS or a supported UI library such as shadcn/ui, compatible with the app's stack and styled to the chosen visual language and theme. Library choices are not limited to those already installed. Reuse suitable components without preserving unwanted styling. Avoid generic dashboard templates; preserve accessibility and responsive behavior.

Present the initial reusable-component gallery. Run focused QA, fix meaningful issues and recheck before composing screens. Use short specialist assignments; run UI critique against shared evidence, then consolidate findings once. A proven development-only missing favicon is nonblocking.

Verify proportionately with focused checks. Report what changed, what passed, and what remains unverified. Never fabricate evidence.

Preserve unrelated work and secrets. Use the assigned workspace and existing lifecycle tools. Do not install dependencies, perform destructive operations, commit, merge, or push without the applicable user authorization.

Reuse the same task's assigned worktree. Missing board linkage can mean incomplete initialization: use `resume --board ID --repo ID`, selecting `--worktree PATH` explicitly if ambiguous; preserve other candidates. Never retry another slug. For a new task with managed workspaces, explicitly share with `--reuse ID` or ASK before `--new` (capability, not consent); it cannot bypass same-task recovery. Truly gone assignments with leftover directories/branches require inspection, not deletion or reinitialization.

Keep the board and essential documentation current, concise, and factual.

Use `board.py` for board changes, `worktree.py` for workspace lifecycle, `guard.py` for policy checks, and `browser-review.mjs` for shared UI evidence; procedures live in `.kilo/skills/`.
