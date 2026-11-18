---
name: git-worktree
description: Manage project-local workspace mode, original workspace reuse, verification and human lifecycle handoff. The script owns mechanics; the agent supplies intent and judgment.
---

# Git Worktree

Use the assigned workspace for implementation, docs, fixes, and review. Inspect the board and existing workspace links before creating anything; do not duplicate a live assignment. `.kilo/repos.json` maps actual repositories, starting with `control: .`; add an app only when it exists and has been initialized as a repository. No app-level instruction layer is required.

Use the existing scripts from the control root:

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py mode status
python3 .kilo/skills/git-worktree/scripts/worktree.py list
python3 .kilo/skills/git-worktree/scripts/worktree.py resume --board <ID>
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <ID> --repo <repo-id> --base <branch>
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <FIX-ID> --reuse <PARENT-ID> --repo <repo-id>
```

Create only an authorized workspace. Required mode uses linked `.kilo/worktrees/`; optional mode permits an assigned nonprotected current checkout. Changing mode regenerates permissions and requires a Kilo restart. A repository with no commits cannot create a worktree: request authorization for an initial commit rather than making one silently.

New worktrees provision local ignored env files and QA navigation once without overwriting; `env.py status --board <ID>` reports provisioning and `env.py sync --board <ID>` uses the same copier. Never print secrets or commit local files.

Before a mutating Git command or destructive shell operation, use `guard.py check-git -- "<command>"` or `guard.py check-delete -- "<command>"`. A denial stops the operation; a guard pass does not grant missing user authorization. `guard.py check-repos` checks mapping and `guard.py check-policy` checks generated permissions. Do not bypass failures or hand-edit the generated permission block.

Verify proportionately, update essential docs, and report actual results. Stage and commit only with applicable user authorization, on the assigned nonprotected branch, preserving unrelated work. Existing merge conflicts are resolved in place; do not start or complete a merge as part of conflict resolution.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py verify <slug>
python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <ID>
```

Handoff prints root-relative review and lifecycle commands; the human runs them from the control root. `verify` requires a clean tree and commits ahead of base for merge readiness. Report an intentionally uncommitted task as such, not ready to merge. Human merge preview/apply uses `merge --board <ID>` and `merge --board <ID> --apply`; full completion records outcomes and cleans up, while conflicts/partial multi-repo progress are preserved. Cleanup uses `cleanup --board <ID> --apply` only after merged/clean checks. Discard is a separate human-only permanent-loss decision with preview and explicit `--apply --discard`; never execute it unasked. Do not auto-create another workspace after merge.

`guard.py sync --repo <ID>` previews the supported harness copy; add `--apply` only with authorization. Project control repositories receive `agent`, `command`, `skills`, `policies`, the harness ignore file, and generated permissions. Apps inherit local config without receiving another harness or generated `AGENTS.md`; existing handwritten instructions remain untouched. Sync does not copy scope/catalog layers. Bootstrap the complete project copy before Git initialization as documented in `README.md`; no provisioning CLI or automatic initial commit is needed.
