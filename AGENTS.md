# Working Agreement

Build useful, distinctive software. Favor clear code, focused modules, existing conventions, and the smallest sound solution. Avoid speculative abstractions.

Understand the task before editing. Ask only when a missing decision materially affects behavior, scope, cost, security, or an expensive-to-reverse choice.

Use `/bootstrap` for a missing project, never manual copying: `bootstrap.py project` from the factory root creates `project/` with mandatory project Git. For `apps/<service-name>`, ask for a meaningful product-role name and separate/project Git ownership if unclear, then invoke `bootstrap.py app <service-name> --git separate|project` from the initialized control root. Track source, product docs and `services.json`; harness/config/devcontainer/generated root instructions/live board are ignored local tooling. Only separate repos are mapped. Bootstrap is authorized to stage intended initial files and create exactly one initial commit only in genuinely new repositories created by that invocation; never reinitialize or auto-commit existing control/app/factory repos. Restore ignored tooling from the factory CLI without staging/commits. See the README.

All FEATURE implementation must use an assigned linked worktree, not the primary checkout. Explicitly assigned features may share its worktree/branch via `worktree.py create --board NEW --reuse EXISTING --repo ID`; preserve scope/ownership, never auto-switch branches. Apps tracked in project Git use the control worktree; separate apps use their own mapped repo worktree. Bootstrap creates the authorized initial commit that enables worktrees; feature source implementation must wait for its success. Optional workspace policy remains available for non-feature maintenance; do not change saved mode or permissions to encode feature assignments.

For new applications and user-facing features, build the frontend flow for user approval before implementing the backend or APIs. Use clearly labeled fixtures when needed; never present mocked behavior as integrated. Backend-only maintenance does not require unrelated frontend work.

Design around the user's actual task, content, and product character. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user has already specified the direction. Develop reusable components before screens using Tailwind CSS or a supported UI library such as shadcn/ui, compatible with the app's stack and styled to the chosen visual language and theme. Library choices are not limited to those already installed. Reuse suitable components without preserving unwanted styling. Avoid generic dashboard templates; preserve accessibility and responsive behavior.

Present the initial reusable-component gallery. Run focused QA, fix meaningful issues and recheck before composing screens. Use short specialist assignments; run UI critique against shared evidence, then consolidate findings once. A proven development-only missing favicon is nonblocking.

Verify proportionately with focused checks. Report what changed, what passed, and what remains unverified. Never fabricate evidence.

Preserve unrelated work and secrets. Use the assigned workspace and existing lifecycle tools. Do not install dependencies, perform destructive operations, commit, merge, or push without the applicable user authorization.

Keep the board and essential documentation current, concise, and factual.

Use `board.py` for board changes, `worktree.py` for workspace lifecycle, `guard.py` for policy checks, and `browser-review.mjs` for shared UI evidence; procedures live in `.kilo/skills/`.
