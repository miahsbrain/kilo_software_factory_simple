# Working Agreement

Build useful, distinctive software. Favor clear code, focused modules, existing conventions, and the smallest sound solution. Avoid speculative abstractions.

Read applicable local instructions and the documented layout, state, domain and approved decisions before editing; use targeted reads thereafter. Follow the approved stack and contracts, not assumed frameworks or folder names.

## Code Quality Standards

Name new features with a past-tense description, without emoji or a repository/folder label. Use `Added kus deployment manifests` for the board title, `feat/added-kus-deployment-manifests` for the branch, and `[feat] Added kus deployment manifests` for an authorized commit. Do not rename existing branches or rewrite history to apply this convention.

For a quick Fix, Chore or Docs edit, use the workspace skill's `--skip-worktree` eligibility check in optional or adaptive mode. Do not create a worktree when the requested current checkout passes. Do not change the user's saved mode implicitly.

When the user explicitly accepts a scoped manual review, the coordinator records it with `board.py approve-review`; specialists report the decision, not a fabricated automated pass. Do not wait for the same approval again. Independent blockers and merge requirements still apply.

Write human-readable code. Clear names and obvious structure matter more than cleverness. Comments explain only "why" decisions were made, never "what" the code does — the code itself must be self-documenting. Keep functions small and focused. Name variables, functions, and types precisely: `getUsersByActiveStatus` not `get`, `isEmailValid` not `check`, `orderTotal` not `data`. Avoid abbreviations except universally known ones (HTTP, URL, ID). No magic numbers — use named constants. No premature abstraction — wait for genuine reuse across three or more call sites before extracting shared behavior.

Prefer a functional core with explicit effects: deterministic domain functions, immutable inputs/outputs and dependencies passed explicitly. Keep filesystem, network, persistence, time, randomness and logging at thin boundaries. Avoid hidden shared state and unnecessary reactive/callback machinery; respect framework conventions where effects are required.

Organize code by cohesive domain and responsibility. Keep transport, framework and persistence details behind clear boundaries; share only stable, genuinely reused behavior. Avoid generic helpers grab bags, forwarding-only wrappers and premature abstractions.

Search for existing code before adding functions, components or state; extend suitable behavior instead of duplicating it. Use existing skills/tools first; ask before building custom tooling or substituting for a missing capability.

Understand the task before editing. Ask only when a missing decision materially affects behavior, scope, cost, security, or an expensive-to-reverse choice.

For new products, clarify users, core flows and scope before scaffolding. Present material product, architecture, data, contract and operational choices with a recommendation and trade-offs; get approval before implementation. Carry approved decisions into assignments, keep unconfirmed assumptions explicit, and stop on conflicts with approved domain rules.

Treat the user-chosen workspace as the boundary: verify resolved control/target roots before bootstrap, app or worktree writes and stop on mismatch; never enter a sibling, reuse an unrelated board/worktree path or infer a destination from a display/service name without explicit user approval. Project bootstrap defaults to factory-local `project/`; ASK before using external `--destination` with `--allow-outside` (the flag is capability, not approval).

Use `/bootstrap` for a missing project, never manual copying: `bootstrap.py project` from the factory root creates `project/` with mandatory project Git. Follow the approved plan's service map (full name, explicit role, sibling `apps/<full-name>` root, responsibility/stack, separate/project Git ownership); ask actual unknown decisions, never collapse planned services or infer unapproved splits from technology. Invoke `bootstrap.py app <product-role> --role <role> --git separate|project` from the initialized control root; arbitrary safe kebab-case roles require a valid nonempty product prefix. Track source, product docs and unchanged name/path/git `services.json`; operational topology/roles belong in product docs. Harness/config/devcontainer/generated root instructions/live board are ignored local tooling. Only separate repos are mapped by full name. Bootstrap is authorized to stage intended initial files and create exactly one initial commit only in genuinely new repositories created by that invocation; never reinitialize or auto-commit existing control/app/factory repos. Restore ignored tooling from the factory CLI without staging/commits. See the README.

All FEATURE implementation must use an assigned linked worktree, not the primary checkout. Explicitly assigned features may share its worktree/branch via `worktree.py create --board NEW --reuse EXISTING --repo ID`; preserve scope/ownership, never auto-switch branches. Apps tracked in project Git use the control worktree; separate apps use their own mapped repo worktree. Bootstrap creates the authorized initial commit that enables worktrees; feature source implementation must wait for its success. Optional workspace policy remains available for non-feature maintenance; do not change saved mode or permissions to encode feature assignments.

Register services from the assigned linked control worktree: tracked `services.json`, project-owned app source and `.gitignore` changes belong there, never in primary. Separate repositories keep their canonical primary-control `apps/<full-name>` location; only ignored operational mappings and shared board coordination may update primary.

For new applications and user-facing features, build the frontend flow for user approval before implementing the backend or APIs. Metadata-only backend bootstrap (.gitignore/Git/manifest) may precede approval, not backend framework source, dependencies, routes, persistence or integration. Use clearly labeled fixtures when needed; never present mocked behavior as integrated. Backend-only maintenance does not require unrelated frontend work.

Design around the user's actual task, content, and product character. If an app has an existing style, ask whether to keep it or do a complete redesign unless the user has already specified the direction. Develop reusable components before screens using Tailwind CSS or a supported UI library such as shadcn/ui, compatible with the app's stack and styled to the chosen visual language and theme. Library choices are not limited to those already installed. Reuse suitable components without preserving unwanted styling. Avoid generic dashboard templates; preserve accessibility and responsive behavior.

Present the initial reusable-component gallery. Before delegating review, read `worktree.py reviews status` from the assigned Git root; specialists recheck there before acting. Its JSON switches are independent (both default on). If `qa` is false, skip automated QA, not normal code tests; if `ui` is false, skip automatic UI critique. With only UI enabled, critique existing evidence only; never capture for the critic. If policy cannot be verified, use manual review for both. On completion link the QA skill's manual QA/UI checklist for every skipped scope, even without a blocker; skipping or supplying a checklist is neither a pass nor a lane transition.

Use only the existing `browser-review.mjs` from the assigned root for saved browser evidence. Playwright MCP is disabled by default; do not substitute ad-hoc capture. Use `--human-requested-manual-capture` only for a capture explicitly requested by the user. Give specialists the assignment, criteria and relevant evidence; consolidate findings once, fix meaningful defects and recheck within policy before composing screens. A proven development-only missing favicon is nonblocking.

Keep all generated review evidence and scratch scripts under the assigned repository/worktree's ignored `artifacts/`: screenshots, images, snapshots, reports, logs, traces, downloads and browser temporary output. Never write them to source roots or product docs. Maintained review-tool source stays in `.kilo/`; generated one-off scripts belong in `artifacts/scripts/`.

Verify proportionately with focused checks, not routine production builds. Use disposable fixtures; never alter real data to make a check pass. Bound retries; escalate repeated or critical failures rather than looping or routing around safeguards. Inspect the diff against acceptance criteria, security, failure behavior and accessibility before accepting completion. Report changes, actual commands/results and unresolved failures or gaps; missing evidence is not a pass. Never weaken checks or fabricate evidence. Merge handoff requires reviewed evidence, updated docs, a clean committed branch and every included board row in `Pending Merge`; only the human merges.

Use the existing logger for meaningful backend operation boundaries and safe categorized outcomes. Never log credentials, personal identifiers or private payloads; remove temporary debugging. Ask before introducing a logging framework, and document only durable conventions.

Preserve unrelated work and secrets. Use the assigned workspace and existing lifecycle tools. Do not install dependencies, perform destructive operations, commit, merge, or push without the applicable user authorization.

Reuse the same task's assigned worktree. Missing board linkage can mean incomplete initialization: use `resume --board ID --repo ID`, selecting `--worktree PATH` explicitly if ambiguous; preserve other candidates. Never retry another slug. For a new task with managed workspaces, explicitly share with `--reuse ID` or ASK before `--new` (capability, not consent); it cannot bypass same-task recovery. Truly gone assignments with leftover directories/branches require inspection, not deletion or reinitialization.

Keep the board and affected documentation current in the same change set, concise and factual. Record durable decisions, not duplicate implementation journals. Get explicit approval before changing permanent agent rules. Keep code comments rare and explain why, not obvious mechanics.

Use `board.py` for board changes, `worktree.py` for workspace lifecycle, `guard.py` for policy checks, and `browser-review.mjs` for shared UI evidence; procedures live in `.kilo/skills/`.
