---
name: git-worktree
description: Manage project-local workspace mode, original workspace reuse, verification and human lifecycle handoff. The script owns mechanics; the agent supplies intent and judgment.
---

# Git Worktree

Anchor writes to the user-approved workspace: verify resolved control and target repo/worktree/app roots against the assignment before mutation; stop on mismatch. Never enter siblings, infer destinations from display/service names or reuse unrelated board/worktree paths without explicit approval. Lifecycle helpers may still run from app/feature worktrees and restore from the factory. Project creation alone requires source factory-root CWD, defaults to local `project/`, and requires actual user approval before external `--destination` plus project-only `--allow-outside` (capability, not consent).

Use the assigned workspace for implementation, docs, fixes, and review. All FEATURE implementation requires an assigned linked worktree, not the primary checkout. Explicitly assigned features may share that worktree and branch; preserve scope/ownership and never auto-switch branches. Inspect existing links before creating anything. Tracked `services.json` records service names/paths/Git ownership; ignored `.kilo/repos.json` maps control plus actual separate repos. Project Git is mandatory; service Git is optional: ASK ownership and a meaningful product-role name if unclear, then use `bootstrap.py app <service-name> --git separate|project` from the initialized control root. Any number of arbitrary meaningful lowercase kebab-case roles are supported, e.g. `shop-frontend`, `shop-backend`, `billing-worker`, `inventory-cron`. Separate mode initializes/initial-commits/maps; project mode has no nested Git/staging/control commit and adds a targeted source unignore. Both register ownership in the manifest. Project-tracked services use control's worktree; separate services their mapped worktree.

Use the existing scripts from the control root:

Both modes write safe app-local project-ignore snapshots without control service-directory rules. Source/docs remain trackable; harness/config/devcontainer/generated root instructions/live board/secrets/outputs stay local ignored. Later ignore changes do not automatically refresh snapshots.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py mode status
python3 .kilo/skills/git-worktree/scripts/worktree.py list
python3 .kilo/skills/git-worktree/scripts/worktree.py resume --board <ID>
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <ID> --repo <repo-id> --base <branch>
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <NEW-ID> --reuse <EXISTING-ID> --repo <repo-id>
```

Create only an authorized workspace. `--reuse` supports Feature rows as well as Fix rows, retaining the existing branch/base and recording the new assignment; it does not require one worktree per feature. Required mode uses linked `.kilo/worktrees/`; optional mode permits an assigned nonprotected current checkout for non-feature maintenance only. Do not change saved mode or permissions to encode feature assignment. Changing mode regenerates permissions and requires a Kilo restart. Bootstrap creates the user-authorized initial source commit only in genuinely new repositories created by that invocation, before linked worktrees become usable; feature implementation waits for successful initialization and assignment.

New worktrees provision local ignored env files and QA navigation once without overwriting; `env.py status --board <ID>` reports provisioning and `env.py sync --board <ID>` uses the same copier. Never print secrets or commit local files.

Before a mutating Git command or destructive shell operation, use `guard.py check-git -- "<command>"` or `guard.py check-delete -- "<command>"`. A denial stops the operation; a guard pass does not grant missing user authorization. `guard.py check-repos` checks mapping and `guard.py check-policy` checks generated permissions. Do not bypass failures or hand-edit the generated permission block.

Verify proportionately, update essential docs, and report actual results. Stage and commit only with applicable user authorization, on the assigned nonprotected branch, preserving unrelated work. Existing merge conflicts are resolved in place; do not start or complete a merge as part of conflict resolution.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py verify <slug>
python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <ID>
```

Handoff prints root-relative review and lifecycle commands; the human runs them from the control root. `verify` requires a clean tree and commits ahead of base for merge readiness. Report an intentionally uncommitted task as such, not ready to merge. Human merge preview/apply uses `merge --board <ID>` and `merge --board <ID> --apply`; full completion records outcomes and cleans up, while conflicts/partial multi-repo progress are preserved. Cleanup uses `cleanup --board <ID> --apply` only after merged/clean checks. Discard is a separate human-only permanent-loss decision with preview and explicit `--apply --discard`; never execute it unasked. Do not auto-create another workspace after merge.

`guard.py sync --repo <ID>` previews the supported harness copy; add `--apply` only with authorization. Project control repositories receive `agent`, `command`, `skills`, `policies`, the harness ignore file, and generated permissions. Apps inherit local config without receiving another harness or generated `AGENTS.md`; existing handwritten instructions remain untouched. Sync does not copy scope/catalog layers.

For a missing project, use `/bootstrap` or `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project` from the factory root; default `project/`, optional factory-local `--destination <new-path>`. External destinations require explicit user approval first and `--allow-outside`. Never manually copy. It copies blank docs/manifest and ignored complete local tooling/devcontainer, initializes Git and stages only intended initial source/docs/manifest/ignore files for exactly one initial commit. Only the new-repo protected-branch/worktree context exception applies; hard command denials, hooks and local identity remain enforced without global policy/config changes. Existing repos/control registration edits are not auto-committed. Prerequisites/existing paths/symlinks/collisions are refused; failures retain partial state, never delete/reinitialize.

After cloning, run the factory checkout's script: `python3 /path/to/factory/.kilo/skills/git-worktree/scripts/bootstrap.py restore --destination /path/to/project`. It rebuilds the ignored map from tracked `services.json` and restores harness/config/generated instructions/blank board/devcontainer. Clone separate services yourself at registered paths, then use `restore --destination /path/to/project/apps/shop-frontend --project /path/to/project`. Control must be restored first; canonical placement preserves existing control-root discovery. App restore inherits control tooling with ignored local instructions/config/harness, no app-local devcontainer or app map/board. Open the control folder in its devcontainer and work under `apps/<name>` so the whole control context is mounted. Relative `../../` instructions and ancestor board/map discovery survive different mount prefixes; control `KILO_CONFIG` is workspace-relative. Existing app devcontainers are untouched and need manual review. Conflicting files and tracked outputs/ancestors cause refusal before tooling/exclude writes; identical files stay, missing files return. No force, network, init/add/commit, source/index/HEAD/config changes or install/build. Clone-local excludes protect tooling without source-ignore edits. Separate-app bootstrap enforces hard init/add/commit denials from both executing source and target control, retaining narrow initial-commit context exceptions and identity/hooks. Never run restore on the factory or a linked worktree. See README constraints. Existing projects/apps are not migrated.
