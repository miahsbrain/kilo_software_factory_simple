---
name: git-worktree
description: Manage project-local workspace mode, original workspace reuse, verification and human lifecycle handoff. The script owns mechanics; the agent supplies intent and judgment.
---

# Git Worktree

Use the assigned workspace for implementation, docs, fixes, and review. All FEATURE implementation requires an assigned linked worktree, not the primary checkout. Explicitly assigned features may share that worktree and branch; preserve scope/ownership and never auto-switch branches. Inspect existing links before creating anything. `.kilo/repos.json` maps actual repositories, starting with `control: .`. Project Git is mandatory; app Git is optional: ASK the user unless already specified, then use `bootstrap.py app <name> --git separate|project` from the initialized control root. `separate` initializes/maps the app with local safe ignores; `project` creates no nested Git/map entry and adds a targeted source unignore while preserving secret/runtime rules. No app-level instructions are generated. Project-tracked apps use the control worktree; separate apps use their mapped repo worktree.

Use the existing scripts from the control root:

Both app modes write a safe app-local project-ignore snapshot (minus `apps/*/`), protecting integrated app runtime paths as well; later project ignore changes do not automatically refresh snapshots.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py mode status
python3 .kilo/skills/git-worktree/scripts/worktree.py list
python3 .kilo/skills/git-worktree/scripts/worktree.py resume --board <ID>
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <ID> --repo <repo-id> --base <branch>
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <NEW-ID> --reuse <EXISTING-ID> --repo <repo-id>
```

Create only an authorized workspace. `--reuse` supports Feature rows as well as Fix rows, retaining the existing branch/base and recording the new assignment; it does not require one worktree per feature. Required mode uses linked `.kilo/worktrees/`; optional mode permits an assigned nonprotected current checkout for non-feature maintenance only. Do not change saved mode or permissions to encode feature assignment. Changing mode regenerates permissions and requires a Kilo restart. Initial scaffolding/bootstrap of an uncommitted repository needs no worktree; request authorization for its initial commit before feature source implementation begins in a linked worktree.

New worktrees provision local ignored env files and QA navigation once without overwriting; `env.py status --board <ID>` reports provisioning and `env.py sync --board <ID>` uses the same copier. Never print secrets or commit local files.

Before a mutating Git command or destructive shell operation, use `guard.py check-git -- "<command>"` or `guard.py check-delete -- "<command>"`. A denial stops the operation; a guard pass does not grant missing user authorization. `guard.py check-repos` checks mapping and `guard.py check-policy` checks generated permissions. Do not bypass failures or hand-edit the generated permission block.

Verify proportionately, update essential docs, and report actual results. Stage and commit only with applicable user authorization, on the assigned nonprotected branch, preserving unrelated work. Existing merge conflicts are resolved in place; do not start or complete a merge as part of conflict resolution.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py verify <slug>
python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <ID>
```

Handoff prints root-relative review and lifecycle commands; the human runs them from the control root. `verify` requires a clean tree and commits ahead of base for merge readiness. Report an intentionally uncommitted task as such, not ready to merge. Human merge preview/apply uses `merge --board <ID>` and `merge --board <ID> --apply`; full completion records outcomes and cleans up, while conflicts/partial multi-repo progress are preserved. Cleanup uses `cleanup --board <ID> --apply` only after merged/clean checks. Discard is a separate human-only permanent-loss decision with preview and explicit `--apply --discard`; never execute it unasked. Do not auto-create another workspace after merge.

`guard.py sync --repo <ID>` previews the supported harness copy; add `--apply` only with authorization. Project control repositories receive `agent`, `command`, `skills`, `policies`, the harness ignore file, and generated permissions. Apps inherit local config without receiving another harness or generated `AGENTS.md`; existing handwritten instructions remain untouched. Sync does not copy scope/catalog layers.

For a missing project, use `/bootstrap` or `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project` from the factory checkout root; default destination is `project/`, with optional `--destination <new-path>`. Never manually copy a new project. The tool copies the blank template and full harness, creates empty apps, then initializes Git without staging/commits. Existing destinations, invalid paths/maps and missing prerequisites are refused. Failures retain partial state; no destructive rollback or copying fallback. See `README.md` for exact constraints. This supersedes manual-only bootstrap; existing projects/apps remain untouched.
