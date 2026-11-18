# <Project name>

Describe the product and its users here.

## Bootstrap

The factory creates this control repository with `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project` from its checkout root (default `project/`; optional `--destination <new-path>`). Use the CLI, not manual copying. It copies blank documents and complete local tooling/devcontainer, initializes Git and creates one initial source commit. Track source, product docs, `.gitignore` and `services.json`. `.kilo/`, `.devcontainer/`, `kilo.jsonc`, generated root `AGENTS.md`, live `docs/BOARD.md`, secrets and outputs are ignored. The factory tracks its template board/harness, not copied live state.

Project CWD must equal the executing source factory root, without fallback; relative destinations use CWD. Default layout is `/path/to/factory/project/apps/`, never a sibling inferred from a display/service name. Custom internal destinations with existing real parents are supported. CWD/source/resolved destination print to stderr before creation; external project targets are refused before any writes or Git mutations by default. ONLY after actual user approval, from the factory root: `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project --destination /path/to/approved-project --allow-outside`. The flag is capability, not consent; traversal/symlinks remain refused. App/restore reject it; restore still accepts explicit external clones without it. Verify resolved control/target roots against the user-chosen workspace before app/worktree writes and stop on mismatch; do not enter siblings or reuse unrelated boards/worktrees without approval. Lifecycle helpers may still run from legitimate app/feature worktrees.

From this initialized control root, create any number of meaningful services, not fixed role slots:

```bash
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app shop-frontend --git separate
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app shop-backend --git separate
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app billing-worker --git project
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app inventory-cron --git project
```

Project Git is mandatory; service ownership is required with no default. Ask ownership and a meaningful product-role name if unclear. Lowercase kebab-case names start with a letter (`control` reserved); arbitrary meaningful roles and backend/frontend variants are supported. Separate mode initializes Git and commits only its initial `.gitignore`. Project mode creates no nested repo/staging/control commit, adding a targeted unignore for `apps/<service-name>`. Both update tracked `services.json` with name/path/git ownership; the ignored generated `.kilo/repos.json` contains only control plus separate services. Control registration changes require a separate authorized commit. No scaffolding/install. Existing paths, unsafe paths, invalid manifests/maps and collisions are refused.

Both modes snapshot project ignores without control-only service-directory rules, explicitly protecting local harness/config/devcontainer/instructions/live board/secrets/outputs while source/docs/`.env.example` stay trackable. Later ignore edits do not automatically refresh snapshots. `services.json` starts as `{"services":[]}`; entries use `{"name":"shop-backend","path":"apps/shop-backend","git":"separate"}` (or `project`). It is the only tracked ownership manifest.

Requires Python 3.9+ and Git; unset `GIT_*` overrides. User approval covers exactly one initial commit only in new project/separate-service repos created by the command. It stages intended initial files, requires an unborn HEAD/empty index, honors Git identity/hooks and hard command-policy denials, and narrowly exempts initial commits from protected-branch/worktree context checks without changing policy. No identity invention or hook skipping. Identity preflight failure creates nothing; later failures retain partial state/index and report failure. Inspect rather than delete/reinitialize. Existing repos and project-owned services are never auto-committed. Feature source implementation still requires an assigned linked worktree.

## Restore A Clone

Use the factory checkout's script, since tooling is intentionally untracked here:

```bash
python3 /path/to/factory/.kilo/skills/git-worktree/scripts/bootstrap.py restore --destination /path/to/project
# Clone separate services yourself into their registered paths, then:
python3 /path/to/factory/.kilo/skills/git-worktree/scripts/bootstrap.py restore --destination /path/to/project/apps/shop-frontend --project /path/to/project
```

Restore control first; missing service checkouts are reported. App restore requires its registered `apps/<name>` location and explicit control context unless safely inferable there. It inherits the control harness with ignored local tooling/config/instructions, no app-local devcontainer or duplicate app map/board. Open this control project's folder in its devcontainer, then work under `apps/<name>`; an app-only mount hides control. Instructions use relative `../../` context and tools discover the ancestor board/map; container `KILO_CONFIG` uses the mounted workspace path. Existing app devcontainers are left untouched and require manual review; use the control container for supported tooling. No network or fabricated remotes. Restore checks all outputs and tracked ancestors first: missing files restored, identical left, tracked paths/ancestors or differing custom/generated files refused without writes. No force option, source/`.gitignore` edits, init/add/commit, config changes, installs or image builds. Clone-local excludes ignore tooling. Symlinks/traversal, factories, linked worktrees, malformed manifests and missing factory source roots are refused. The control-level generated devcontainer keeps supported Dockerfile/features/env/ports with only local shell-guard post-create setup, not the factory's global Git/doctor step. Separate-app bootstrap honors hard init/add/commit denials from both the executing source and this target control's policy; neither can relax the other.

## Delivery

Build the frontend flow for user approval before backend/APIs for new apps and user-facing features, using clearly labeled fixtures. Backend-only maintenance needs no unrelated frontend. Use the working agreement and existing board/lifecycle/capture tools. Record the actual stack, development command, and ports in `docs/STACK.md`; no product stack is selected by this template.

All FEATURE implementation uses an assigned linked worktree, not the primary checkout. Explicitly assigned features may share its worktree/branch via `worktree.py create --board NEW --reuse EXISTING --repo ID`; preserve scope/ownership and never auto-switch branches. Project-tracked apps use control's worktree; separate apps use their mapped repo's worktree. Optional policy remains for non-feature maintenance; do not change saved mode or permissions for feature assignment.

## Documentation

Keep `DOMAIN.md`, `ROADMAP.md`, `services.json` and relevant `docs/` current and concise. `docs/HANDOVER.md` describes current reality; `docs/DECISIONS.md` records material approved choices; `docs/changelog/` records engineering changes. Update the root product `CHANGELOG.md` only when requested. The harness is clone-local; source/product docs and manifest survive a fresh clone.
