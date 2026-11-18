# <Project name>

Describe the product and its users here.

## Bootstrap

The factory creates this control repository with `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project` from its checkout root (default `project/`; optional `--destination <new-path>`). Agents must use the CLI, not manual copying. It retains the template agreement/control-only map, copies the four harness directories plus exact `.kilo/.gitignore` and `kilo.jsonc`, creates empty `apps/`, then initializes Git. There is no second maintained harness tree in the template. The copied blank board is ignored by the template's static rules; factory live boards, local runtime inputs, secrets and generated outputs are not copied.

From this initialized project control root, create real apps only when needed:

```bash
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app customer-portal --git separate
python3 .kilo/skills/git-worktree/scripts/bootstrap.py app billing-worker --git project
```

Project Git is mandatory; individual app Git is optional. `/bootstrap` must ASK separate app Git versus tracking app source in project Git unless already specified. The CLI requires `--git separate|project`; no default, omission fails before mutation. Both modes create only `apps/<name>`. `separate` snapshots the project `.gitignore` minus only `apps/*/`, initializes Git and maps the real repo ID/path. Secrets/local outputs remain ignored and source/`.env.example` trackable; later project ignore edits do not update that snapshot. `project` creates no nested Git or independent map entry, adding only `!/apps/<name>/` to project ignores so control Git tracks source while prior secret/runtime patterns remain. Other apps stay ignored. Missing/nonregular/symlink ignore sources fail before creation. Names are lowercase kebab-case starting with a letter; `control` is reserved. No scaffolding, installs, app instructions or duplicate harness. `apps/` may be absent after checkout; the command creates it.

Both modes receive the app-local ignore snapshot, protecting integrated app runtime paths too; later project ignore edits do not automatically refresh it.

Requires Python 3.9+ and Git; unset `GIT_*` overrides. Authorized bootstrap includes scoped initialization consent where init occurs under the unchanged guard's `ask` rule; hard denials/errors still stop project bootstrap and separate mode. Project-tracked app mode performs no init check. Both modes refuse existing paths (including empty directories/symlinks), invalid names/maps and collisions. Failures retain partial state; inspect rather than delete or manually copy. No staging or commits. Initial scaffolding/bootstrap needs no worktree; request authorization for the initial commit before feature implementation. Existing projects need an agreed migration, not rebootstrap.

## Delivery

Build the frontend flow for user approval before backend/APIs for new apps and user-facing features, using clearly labeled fixtures. Backend-only maintenance needs no unrelated frontend. Use the working agreement and existing board/lifecycle/capture tools. Record the actual stack, development command, and ports in `docs/STACK.md`; no product stack is selected by this template.

All FEATURE implementation uses an assigned linked worktree, not the primary checkout. Explicitly assigned features may share its worktree/branch via `worktree.py create --board NEW --reuse EXISTING --repo ID`; preserve scope/ownership and never auto-switch branches. Project-tracked apps use control's worktree; separate apps use their mapped repo's worktree. Optional policy remains for non-feature maintenance; do not change saved mode or permissions for feature assignment.

## Documentation

Keep `DOMAIN.md`, `ROADMAP.md`, and relevant `docs/` current and concise. `docs/HANDOVER.md` describes current reality; `docs/DECISIONS.md` records material approved choices; `docs/changelog/` records engineering changes. Update the root product `CHANGELOG.md` only when requested. The project owns its copied harness independently of the factory.
