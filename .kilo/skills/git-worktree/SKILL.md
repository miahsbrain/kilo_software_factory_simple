---
name: git-worktree
description: Manage project-local workspace mode, original workspace reuse, verification and human lifecycle handoff. The script owns mechanics; the agent supplies intent and judgment.
---

# Git Worktree

Use one assigned repo-specific workspace set per change, carrying code and documentation across
build, fixes, QA, critique, docs and conflict resolution. Required mode (default) uses linked
worktrees. Optional mode permits the assigned current checkout on a nonprotected branch; scopes,
secret protection and protected-branch commit checks remain. Never create a fresh review/fix
workspace or an empty workspace immediately after merge. New workspaces require an explicit user
request or the next approved task after the previous change merged.

`python3 .kilo/skills/git-worktree/scripts/worktree.py mode required|optional|status` selects or
reports project-local mode (choose one value). Mode changes regenerate permissions; restart Kilo.
`board.py` and `docs/BOARD.md` remain tracked pending user clarification.

This is **CLI only**: plain `git`, no extension, no `gh`, no browser, no pull requests.

**The script does the mechanics. You supply the intent.** Do not hand-run `git worktree add` when
the script can do it — the script is where the naming rules and the refusals live.

---

## 1. The scripts

| Script | Does |
|---|---|
| `.kilo/skills/git-worktree/scripts/worktree.py` | mode · create · resume · list · verify · handoff · merge · discard · cleanup |
| `.kilo/skills/git-worktree/scripts/env.py` | sync · status · clean — the env files of a worktree |
| `.kilo/skills/git-worktree/scripts/guard.py` | check-delete · check-worktree · check-git · check-policy · sync · check-repos · install-hooks · policy |

Python 3.9+, standard library only.

---

## 2. Create the worktree

The name comes from the **board row**, not from what you type. The script reads the row, derives
the branch type from its `Type` column and the slug from its task title, creates the worktree,
and records the path and branch back onto the row.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <BOARD-ID> [--base <branch>]
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <FIX-ID> --reuse <PARENT-ID> --repo <ID>
```

- For a new workspace the **branch type** comes from the row's `Type`: `Feature` → `feat`, `Fix` → `fix`,
  `Chore` → `chore`, `Docs` → `docs`, `Research` → `chore`.
- The **slug** comes from the task title, kebab-cased, trimmed to the first 6 words when it is
  longer than 48 characters.
- The branch is `<type>/<slug>` and the directory is `.kilo/worktrees/<slug>/`.
- `--slug <override>` replaces the derived slug. It must be kebab-case.
- `--base` defaults to the target repository's own base: `main` when it exists, otherwise the
  branch it names as `origin/HEAD` (the microservices use `dev`). Name one with `--base` to
  override. Use a feature branch only when the row's `Blocked by` says so.

Reuse links a finding to the original repo-specific branch/path; it does not rename or duplicate
it. Inspect existing row links before creating anything. The script refuses unknown rows, or,
for new workspaces, when the branch or directory already exists, or
when the row's type is unknown. It never deletes anything. It writes the board row in the **main
checkout**, so the live board always points at the running worktree.

During new worktree creation, the script recursively copies ignored or untracked regular `.env*`
files from the target repository's primary checkout to matching paths, except `.env.example`. File
permissions are preserved; tracked sources, symlinks, non-regular files and existing destinations
are skipped. It also copies `.kilo/local/qa-navigation.json` when present. These local files stay
untracked, and `.env*` remains unreadable to agents. Reused workspaces are not recopied.
**When the row already has a live worktree, `create` refuses** and points to resume, human-only
discard, or a different `--slug`. A second worktree for one row is never created.

**When the slug directory is already taken by another row's worktree, `create` refuses too**,
with a different message: it names the slug directory, the row that owns it when the board
records one, and the ways that actually work — `--slug <other-slug>`, or human-only discard for
that other row. It never offers a `resume` for a row whose worktree does not exist.

Before creating, check for an in-flight worktree on the same task:

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py list
```

---

## 2a. Local files: provisioned once, never overwritten

`create` recursively copies ignored/untracked regular `.env*` files except `.env.example` and
`.kilo/local/qa-navigation.json` from the mapped target repository's primary checkout. It skips
tracked sources, symlinks, non-regular files and existing destinations; copied file permissions
are preserved. Copied env paths are added to the repository's shared `.git/info/exclude`.
Values are never printed. `env.py sync` delegates to this same safe copier. `resume` does not copy
again, and cleanup never deletes a local file without recorded provenance. The agent read policy
for env files remains denied.

```bash
python3 .kilo/skills/git-worktree/scripts/env.py status --board <BOARD-ID>
python3 .kilo/skills/git-worktree/scripts/env.py sync --board <BOARD-ID>
python3 .kilo/skills/git-worktree/scripts/env.py clean --board <BOARD-ID>            # dry run
python3 .kilo/skills/git-worktree/scripts/env.py clean --board <BOARD-ID> --apply
```

`env.py sync --worktree <path>` provisions one worktree directly, without a board row.
A main checkout with no env file is not an error: the script says so and exits 0.

---

## 2b. Reuse a worktree: resume and discard

A board row that already has a worktree is **resumed**, not duplicated.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py resume --board <BOARD-ID>
```

`resume` finds the row's live worktree, prints its path and branch, and puts the row back in
`In Progress` without recopying local files. It refuses when the row has no live worktree.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <BOARD-ID>           # dry run
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <BOARD-ID> --apply --discard
```

`discard` is a human-only, permanent loss operation. It previews by default; acting requires both
`--apply` and the explicit `--discard` consent flag. It removes only the selected mapped linked
worktree and its branch, including dirty or unmerged work. It creates no backup, patch or TSV.
The selected board entry is cleared; the row becomes `Dropped` only when no other linked
worktrees remain. Kilo agent-tool execution is denied by policy.

`list` shows a `state` column: `active`, `merged`, `stale` or `unknown`. A worktree whose row
says `Merged` or `Dropped` but that still exists is `stale` — a leftover to clean up.

---

## 2c. Repos: a work surface in its own repository

`.kilo/repos.json` maps a **repo id** to a path relative to the control repo root:

```json
{
  "control": ".",
  "web": "apps/web",
  "mobile": "apps/mobile",
  "api": "apps/api"
}
```

`control` is the control repo itself. An app may live in its own git repository under `apps/`;
that repo is a **work surface** — it holds application code and nothing else. The harness stays
in the control repo, and the work surface carries a generated pointer to it.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <BOARD-ID> --repo api
```

- The id comes from the map. The default is `control`. A repo is addressed by id, never by a raw
  path on the command line, and the map is the only way in.
- The **board stays in the control repo**. The **worktree is created in the target repo**, under
  that repo's own `.kilo/worktrees/`.
- The row's `Branch/Worktree` cell records the path relative to the control repo root, for example
  `apps/api/.kilo/worktrees/<slug> · branch feat/<slug>`. A row with worktrees in several repos
  holds several entries.
- The row's `Repos` cell gains the repo id.
- `--base` must exist in the target repo. Without it, the repo's own base is used.
- The new worktree gets the generated pointer as its `AGENTS.md`. Untracked files do not travel
  into a worktree, so `create` writes it there. The pointer is never committed: it is listed in
  the repository's `.git/info/exclude`.

`cleanup` and `verify` find the worktree from the row's `Branch/Worktree` cell, so they work for
worktrees in any repo. `list` shows the worktrees of every repo in the map, with the repo id next
to each.

### The repo map and the guard rails

```bash
python3 .kilo/skills/git-worktree/scripts/guard.py check-repos   # map vs layout
python3 .kilo/skills/git-worktree/scripts/guard.py sync --repo api   # dry run
python3 .kilo/skills/git-worktree/scripts/guard.py sync --repo api --apply
```

- `check-repos` fails when a mapped path is missing, when a git repository under `apps/` is not
  registered, or when the control repo is not registered as `control`. A registered folder that
  is not a git repository yet is reported, not a failure.
- `sync` gives the target the pointer it needs. A **control repo** — one that holds a repo map
  and a board — receives the `.kilo/` slice (`agent/`, `command/`, `skills/`, `policies/`,
  `scopes/`, `catalog/`) and a regenerated `kilo.jsonc` permission map. A **work surface** receives one
  generated file: `AGENTS.md`, a pointer that names the project, the canonical scope rules and the
  unit's documentation. It is a dry run unless `--apply` is given. It copies files only: it never
  deletes anything and never touches the target's `docs/`.
- The pointer is never committed. `sync` adds `AGENTS.md`, `.kilo/` and `kilo.jsonc` to the
  target's `.git/info/exclude`, which belongs to the clone, is shared by every worktree of that
  repository, and never enters a commit. A work surface's committed content is its own code.
- `sync --all` does the same for every repository in the map except the control repo.
- A pointer that is already current is left alone, and a hand-written `AGENTS.md` is never
  replaced.
- Canonical scope rules live in `.kilo/scopes/<id>.md`. Work surfaces receive a generated ignored
  `AGENTS.md` pointer to those rules and shared governance, not a committed duplicate harness.
- The **slice source** is the **tree the shell is in**, the same rule `check-policy` follows: a
  sync run in a worktree copies that worktree's `.kilo/` slice and scope rules.
- The **target repository** is resolved in the control repo's **main checkout**, because a nested
  app repository under `apps/` is not tracked by the control repo and exists only there. The
  exception is `control` itself, which is the tree the shell is in, so `sync --repo control` in a
   worktree targets that worktree's control configuration, never the main checkout's.
- A file that is already its own destination is skipped, so `sync --repo control` is safe to run.

---

## 3. Guard-rail policy and the permission map

`.kilo/policies/git-policy.json` is the **single source of truth** for the guard rails. Every rule
lives there with its reason. The `permission` block in `kilo.jsonc` is **generated** from that file
and is never hand-edited.

Kilo evaluates permission rules **in config order, and the last matching rule wins**. The
generated map therefore puts the broad fallback first and the narrow exceptions after it.

```bash
python3 .kilo/skills/git-worktree/scripts/guard.py check-git -- "git push origin main"
```

- Exit 0 → allowed. Run the command.
- Exit 1 → denied. The reason is on stdout. Do not run the command.
- Exit 2 → usage error, or the policy file is missing.
- Exit 3 → needs the user's approval. Ask the user; do not run it silently.

`check-git` resolves the real git subcommand (past `-C <path>`, `-c <k=v>` and the other global
options), then evaluates the **context checks first**, because they are more specific than any
keyword list:

| Context check | Fires when |
|---|---|
| `protected_branch` | the current branch is on the policy's `protected_branches` list, or is the branch the repository names as its default through `origin/HEAD` |
| `in_worktree` | required mode denies commits outside linked `.kilo/worktrees/`; optional mode permits assigned nonprotected current checkouts |
| `branch_switch_in_worktree` | the shell is in a linked worktree and the command switches branches |
| `always` | always — used for the raw `git worktree remove` |

Then the `bash` rules apply with **last match wins**, exactly like Kilo.

The generated edit map follows project-local mode: required confines edits to worktrees; optional
permits the current checkout while preserving secret and rules-file protections. Task assignments
still confine allowed paths; mode is not authorization to edit unrelated files. `docs/BOARD.md`
is denied to file tools and written by `board.py`. Restart Kilo after regeneration.

The same commit rule is enforced without the model: `guard.py install-hooks` writes a fail-closed
`pre-commit` hook into the control repo and every repository in the map. The hook finds the
nearest `guard.py` and runs `check-git`. A missing guard refuses the commit.

```bash
python3 .kilo/skills/git-worktree/scripts/guard.py install-hooks --all          # dry run
python3 .kilo/skills/git-worktree/scripts/guard.py install-hooks --all --apply  # install
```

The policy's `hidden_paths` block is expanded into `deny` rules for the file-reading tools —
`read`, `grep`, `glob` and `list` — so no agent can read a git config, credential file or `.env`
that may carry a secret. It covers `.env`, `.env.*` (except `.env.example`), `.git/config`,
`*.git/config`, submodule configs, `.git-credentials`, `~/.gitconfig`, the XDG git config and
credential stores, `.npmrc` and private keys. The list lives in `.kilo/policies/git-policy.json`;
add a path there, not in `kilo.jsonc`.

A shell command has no path awareness, so the same rule is enforced for bash by the
`$BASH_ENV` startup file (`.devcontainer/kilo-redact.sh`): it refuses any `bash -c` command whose
text names one of those files. `devcontainer.json` sets `KILO_CONFIG` to the root `kilo.jsonc`, so
a nested app repository inherits the permission map without a copy. The map needs a Kilo restart;
the shell guard is live as soon as the file is installed.

Keep the two layers in sync:

```bash
python3 .kilo/skills/git-worktree/scripts/guard.py check-policy          # proves they match
python3 .kilo/skills/git-worktree/scripts/guard.py check-policy --write  # regenerates kilo.jsonc
python3 .kilo/skills/git-worktree/scripts/guard.py policy                 # prints the block to paste
```

`check-policy` exits 0 and prints `policy in sync` when `kilo.jsonc` still matches the policy
file. On a mismatch it exits 1 and prints the exact `permission` block to paste.

**Known limitation.** A permission pattern cannot see a command a shell wrapper hides — for example
`sh -c "git push …"`. `guard.py check-git` is the precise layer, so **run it before a mutating git
command**. The permission map is the coarse net; the guard is the enforcement point.

---

## 4. Work inside it

Every edit, command and verification uses the assigned repo-specific workspace path.

```bash
git -C .kilo/worktrees/<slug> status
git -C .kilo/worktrees/<slug> diff
```

- Required mode uses linked worktrees; optional permits the assigned nonprotected current
  checkout. The orchestrator alone writes the live board through its script in the control checkout.
- Do not `git checkout` another branch inside the worktree.
- Never start a merge. Assign `merge-conflict-resolver` only to the existing conflicted checkout;
  the human reviews/completes that merge and reruns the lifecycle command. Never use `git stash`.
- Keep the diff minimal: one logical change per commit.

---

## 5. Guarded deletes

**Deletion inside the worktree only.** Before any destructive command, run the guard:

```bash
python3 .kilo/skills/git-worktree/scripts/guard.py check-delete -- "rm -rf build"
```

- Exit 0 → allowed. Run the command.
- Exit 1 → denied. The reason is on stderr. Do not work around it; do not run the command.

The guard blocks `rm`, `rmdir`, `unlink`, `trash`, `find -delete`, `git clean`,
`git worktree remove`, `git branch -D`, `git reset --hard`, and `git checkout --` when the
target resolves outside the current worktree or inside the main checkout. `/` and `$HOME` are
never deletable. Temp dirs under `/tmp` and `$TMPDIR` are allowed.

The same guard has a worktree-path check:

```bash
python3 .kilo/skills/git-worktree/scripts/guard.py check-worktree -- "git worktree add .kilo/worktrees/x -b feat/x main"
```

---

## 6. Commit locally

Local commits on the assigned nonprotected branch are expected for clean handoff, unless the
current task explicitly says not to commit yet. Never stage unrelated changes.

```bash
git -C .kilo/worktrees/<slug> add -A
git -C .kilo/worktrees/<slug> commit -m "<emoji> [<type>] <scope>: <subject>" -m "- what changed and why"
```

Message format (`AGENTS.md` §B4.1):

    📝 [docs] handover: describe the factory as it is today

    - replace the template with the real factory structure

Types: `feat fix chore refactor test perf docs ci ui security revert wip`.
Subject ≤ 72 characters, imperative voice. One logical change per commit.

**Never** `git push`, `git merge`, `git commit --amend` someone else's work, or `--force` anything.

---

## 7. Verify before handing off

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py verify <slug> [--base <branch>]
```

Prints the branch, the commits ahead of base, the changed files, the dirty state, and a
`READY FOR MERGE` or `NOT READY` line. `READY FOR MERGE` requires a clean tree and at least one
commit ahead of base.

A worktree is ready for handoff only when:

- [ ] the verification command from `docs/STACK.md` passed, and the command + result are recorded
- [ ] every acceptance criterion on the board row has its proof recorded
- [ ] the documentation for the change is updated in the same branch
- [ ] `worktree.py verify` prints `READY FOR MERGE`

---

## 8. Hand off for human approval

The agent **never** merges.

1. The orchestrator sets the board row to `Pending Merge` in the main checkout, with the
   worktree path and branch in the `Branch/Worktree` column.
2. The agent reports: what was done, what is proven, what is not done and why, the next action.
3. Generate the all-repository handoff and let the human run the printed lifecycle commands.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <ID>
# human: preview, then apply; repeat --board for a batch
python3 .kilo/skills/git-worktree/scripts/worktree.py merge --board <ID>
python3 .kilo/skills/git-worktree/scripts/worktree.py merge --board <ID> --apply
3. The agent prints the hand-off block for the human.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board <BOARD-ID>
```

That prints the block: the worktree path, the branch, the base, the diff command, the log
command, the merge command and the teardown command — commands and paths only. It never runs a
git command that changes anything. Every session that worked in a worktree ends with it, so the
diff command and the merge command always reach the human together.

The block looks like this:

```text
board:    BOARD-00X
worktree: <path>/.kilo/worktrees/<slug>
branch:   <type>/<slug>
base:     main

diff:
  git -C <path>/.kilo/worktrees/<slug> diff main
log:
  git -C <path>/.kilo/worktrees/<slug> log --oneline main..HEAD
merge (run by the human, in the main checkout):
  git merge --no-ff <type>/<slug> -m "merge: <slug>"
after the merge, remove the worktree and delete the branch:
  python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup --board BOARD-00X --apply
```

The teardown is the last section: it names the row, so the human uses the lifecycle CLI to remove
the worktree and delete the branch. Do not replace it with raw Git teardown commands.

When the branch is already merged into the base, the block prints a `git show --stat` line
instead of the merge command, so nobody is handed a merge that would fail.

The same commands by hand, if the human prefers them:

```bash
# review
python3 .kilo/skills/git-worktree/scripts/worktree.py list
git -C .kilo/worktrees/<slug> diff main
git -C .kilo/worktrees/<slug> log --oneline main..HEAD

# merge — run by the human, in the main checkout
git merge --no-ff <type>/<slug> -m "merge: <slug>"

# cleanup — run by the human, after the merge
python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup --board BOARD-00X --apply
```

The human may select `--repo <ID>` and `--target <branch>`; the saved base is default. ALL clean
sources/targets (except live control-board metadata), readiness and commits are preflighted before
mutation. Multi-repo merge is non-atomic: halt on conflict and preserve partial state. The human
completes a preexisting conflicted merge after specialist resolution/review/checks, then reruns
the command. Rows become `Merged` only when every required surface completes; merged worktrees
and feature branches are cleaned up automatically. Shared parent/Fix rows can hand off together.

---

## 9. Clean up

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup <slug>           # dry run
python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup <slug> --apply   # act
python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup --board BOARD-00X --apply
```

`--board` is the alternative to the slug: it takes the worktree from the row's
`Branch/Worktree` cell, the same way `resume` and `discard` do, and it clears that cell when
the worktree is gone. Give a slug or `--board`, never both and never neither — either mistake
is a usage error. The teardown the hand-off block names is the `--board` form, because the row
is what the human holds.

`cleanup --board` owns the lane for the row it tears down: a successful cleanup puts the row in
`Merged` and clears the cell, in the same write. The slug form of `cleanup` cannot know the
row, so it touches nothing on the board. A refused cleanup changes nothing on the board: the
lane stays as it was and the cell keeps pointing at the live worktree.

The script refuses when the branch has commits not reachable from the base, or when the worktree
is dirty. It writes a recovery record to `<git-common-dir>/cleanup-wt/<timestamp>.tsv` before
merged cleanup. Discard is a separate permanent-loss operation with no backup:

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <ID> --repo <ID>
# human only, after explicit approval of loss:
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <ID> --repo <ID> --apply --discard
```

Discard previews by default; only selected mapped linked `.kilo/worktrees/` and feature branches
may be removed, even dirty/unmerged. Never main/protected/outside-map checkouts. Fully discarded
linked rows become `Dropped`; partial outcomes stay recorded. No backup is created. Agent-tool
execution is denied by policy; **never run discard through an agent tool.**

---

## 10. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `fatal: invalid reference: HEAD` | The repository has no commits | The base branch needs one commit before any worktree exists |
| `branch ... is already checked out` | The branch already has a workspace | Reuse the assigned existing path; do not duplicate it |
| `worktree.py create` refuses | The slug, branch, or directory already exists | Inspect the existing assignment and reuse if it belongs to this change |
| `branch ... is already checked out` | The branch already has a worktree | Use a new branch, or clean up the old worktree first |
| `worktree.py create` refuses | The slug, branch, or directory already exists | Pick another slug, or clean up first |
| `worktree.py create` refuses with resume / discard / new slug | The row already has a live worktree | Resume it, ask a human to discard it, or create with `--slug` — never a second worktree |
| `worktree.py create` refuses with new slug / discard <other row> | The slug directory is taken by another row's worktree | Create with `--slug`, or discard that other row's worktree with its own row id |
| `worktree.py resume` refuses | The row has no live worktree | `create` one, or `discard` the stale entry first |
| `worktree.py discard` refuses | The selected row entry is missing/invalid or apply lacks explicit consent | Recheck the row; only a human may use `--apply --discard` |
| The application does not start in a worktree | The env files were never provisioned | `env.py sync --board <BOARD-ID>` — never read the file yourself |
| `guard.py check-delete` denies | The target is outside the worktree | Delete inside the worktree, use a temp dir, or ask the user |
| Merge conflict at merge time | Both branches changed the same area | Preserve partial state; specialist resolves the existing conflict, human completes/retries |
| `git stash` conflicts across worktrees | Stashes are shared | Do not stash. Resolve conflicts inside the worktree |
| `worktree.py create --repo x` refuses | `x` is unknown in `.kilo/repos.json`, or its path is not a git repository | Register the repo in the map, or make the folder a repository first |
| `guard.py sync --repo x` refuses to apply | The target is not a git repository | Make the folder a repository, then sync again |

---

## 11. Relationship to the rest of the factory

- The board row is the work item; linked findings share its original repo-specific workspace set.
- The builder agents (`frontend-dev`, `backend-dev`, `mobile-dev`) use assigned original paths,
  including assigned nonprotected checkouts in optional mode.
- The reviewer agents (`qa-reviewer`, `ui-critic`) use the same state and report
  findings; the orchestrator turns findings into `Type: Fix` board rows.
- The root `AGENTS.md` owns the rules. This skill is the executable procedure for them.
