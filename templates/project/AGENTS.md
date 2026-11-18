# Working Agreement

Build useful, distinctive software. Favor clear code, focused modules, existing conventions, and the smallest sound solution. Avoid speculative abstractions.

Understand the task before editing. Ask only when a missing decision materially affects behavior, scope, cost, security, or an expensive-to-reverse choice.

Use `/bootstrap` and the README's CLI for new apps. Project Git is mandatory; app Git is optional. Ask whether to use separate app Git or track source in project Git unless already specified, then invoke `bootstrap.py app <name> --git separate|project` from this initialized control root. Only separate repos are mapped. Never manually copy a new project, place apps at the control root, reinitialize repositories or implicitly stage/commit.

All FEATURE implementation must use an assigned linked worktree, not the primary checkout. Explicitly assigned features may share its worktree/branch via `worktree.py create --board NEW --reuse EXISTING --repo ID`; preserve scope/ownership, never auto-switch branches. Apps tracked in project Git use the control worktree; separate apps use their own mapped repo worktree. Initial scaffolding/bootstrap may precede the authorized initial commit that enables worktrees; feature source implementation must wait. Optional workspace policy remains available for non-feature maintenance; do not change saved mode or permissions to encode feature assignments.

For new applications and user-facing features, build the frontend flow for user approval before implementing the backend or APIs. Use clearly labeled fixtures when needed; never present mocked behavior as integrated. Backend-only maintenance does not require unrelated frontend work.

Design around the user's actual task, content, and product character. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user has already specified the direction. Develop reusable components before screens using Tailwind CSS or a supported UI library such as shadcn/ui, compatible with the app's stack and styled to the chosen visual language and theme. Library choices are not limited to those already installed. Reuse suitable components without preserving unwanted styling. Avoid generic dashboard templates; preserve accessibility and responsive behavior.

Use short, explicit assignments for specialist agents. Run UI critique and a read-only unslop pass in parallel against shared evidence. Consolidate findings once and prioritize meaningful defects. A proven development-only missing favicon is nonblocking.

Verify proportionately with focused checks. Report what changed, what passed, and what remains unverified. Never fabricate evidence.

Preserve unrelated work and secrets. Use the assigned workspace and existing lifecycle tools. Do not install dependencies, perform destructive operations, commit, merge, or push without the applicable user authorization.

Keep the board and essential documentation current, concise, and factual.

Use `board.py` for board changes, `worktree.py` for workspace lifecycle, `guard.py` for policy checks, and `browser-review.mjs` for shared UI evidence; procedures live in `.kilo/skills/`.
