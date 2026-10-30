---
name: git-worktree
description: Create, verify, and clean up the isolated git worktree that carries every change in this factory. Use before editing any file in a project that follows the worktree rule. The script does the work — the agent supplies the slug and the judgment.
---

# Git Worktree

Every change in this factory happens in an isolated git worktree. The worktree carries the code
**and** the documentation for that change. `main` is never edited by an agent.

This is **CLI only**: plain `git`, no extension, no `gh`, no browser, no pull requests.

**The script does the mechanics. You supply the intent.** Do not hand-run `git worktree add` when
the script can do it — the script is where the naming rules and the refusals live.

---

## 1. The scripts

| Script                                          | Does                                                                                   |
| ----------------------------------------------- | -------------------------------------------------------------------------------------- |
| `.kilo/skills/git-worktree/scripts/worktree.py` | create · list · verify · cleanup                                                       |
| `.kilo/skills/git-worktree/scripts/guard.py`    | check-delete · check-worktree · check-git · check-policy · sync · check-repos · policy |

Python 3.9+, standard library only.

---

## 2. Create the worktree

The name comes from the **board row**, not from what you type. The script reads the row, derives
the branch type from its `Type` column and the slug from its task title, creates the worktree,
and records the path and branch back onto the row.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board <BOARD-ID> [--base main]
```

- The **branch type** comes from the row's `Type`: `Feature` → `feat`, `Fix` → `fix`,
  `Chore` → `chore`, `Docs` → `docs`, `Research` → `chore`.
- The **slug** comes from the task title, kebab-cased, trimmed to the first 6 words when it is
  longer than 48 characters.
- The branch is `<type>/<slug>` and the directory is `.kilo/worktrees/<slug>/`.
- `--slug <override>` replaces the derived slug. It must be kebab-case.
- `--base` defaults to `main`. Use a feature branch only when the row's `Blocked by` says so.

The script refuses when the row does not exist, when the branch or directory already exists, or
when the row's type is unknown. It never deletes anything. It writes the board row in the **main
checkout**, so the live board always points at the running worktree.

Before creating, check for an in-flight worktree on the same task:

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py list
```

---

## 2a. Repos: a work surface in its own repository

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
that repo is a **work surface** — it gets the same `.kilo/` slice and the same guard rails,
synced from the control repo.

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
- `--base` must exist in the target repo.

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
- `sync` copies the `.kilo/` slice (`agent/`, `command/`, `skills/`, `policies/`, `scopes/`) and
  the scope rules into the target repo and regenerates the target's `kilo.jsonc` permission map.
  It is a dry run unless `--apply` is given. It copies files only: it never deletes anything and
  never touches the target's `docs/`.
- The scope rules live in `.kilo/scopes/<id>.md`. `sync --repo <id>` writes that file to the
  scope's repository as its `AGENTS.md`. For the control repo itself the scope rules go to
  `apps/<id>/AGENTS.md`.
- The **slice source** is the **tree the shell is in**, the same rule `check-policy` follows: a
  sync run in a worktree copies that worktree's `.kilo/` slice and scope rules.
- The **target repository** is resolved in the control repo's **main checkout**, because a nested
  app repository under `apps/` is not tracked by the control repo and exists only there. The
  exception is `control` itself, which is the tree the shell is in, so `sync --repo control` in a
  worktree updates that worktree's own `apps/<id>/AGENTS.md` copies and never the main checkout's.
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

| Context check               | Fires when                                                          |
| --------------------------- | ------------------------------------------------------------------- |
| `protected_branch`          | the current branch is `main`, `master` or `base`                    |
| `branch_switch_in_worktree` | the shell is in a linked worktree and the command switches branches |
| `always`                    | always — used for the raw `git worktree remove`                     |

Then the `bash` rules apply with **last match wins**, exactly like Kilo.

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

Every edit, command, and verification run happens with the worktree as the working directory.

```bash
git -C .kilo/worktrees/<slug> status
git -C .kilo/worktrees/<slug> diff
```

- Do not edit files in the main checkout. The only exception is `docs/BOARD.md`, which the
  orchestrator writes in the main checkout.
- Do not `git checkout` another branch inside the worktree.
- Do not `git merge` the base branch in unless the task needs it; resolve conflicts inside the
  worktree. Never use `git stash` — stashes are shared across worktrees.
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

Local commits on the worktree branch are required — they are what the human reviews and merges.

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
python3 .kilo/skills/git-worktree/scripts/worktree.py verify <slug> --base main
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
3. The agent prints the review and merge commands for the human.

```bash
# review
python3 .kilo/skills/git-worktree/scripts/worktree.py list
git -C .kilo/worktrees/<slug> log --oneline main..HEAD
git -C .kilo/worktrees/<slug> diff main

# merge — run by the human, in the main checkout
git merge --no-ff <type>/<slug> -m "merge: <slug>"

# cleanup — run by the human, after the merge
python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup <slug> --apply
```

The merge target is the human's call: `main`, or a feature branch when the work is part of a
larger feature.

---

## 9. Clean up

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup <slug>           # dry run
python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup <slug> --apply   # act
```

The script refuses when the branch has commits not reachable from the base, or when the worktree
is dirty. It writes a recovery record to `<git-common-dir>/cleanup-wt/<timestamp>.tsv` before
acting. **Never delete a worktree holding unmerged work.**

---

## 10. Failure modes

| Symptom                                   | Cause                                                                     | Fix                                                                        |
| ----------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `fatal: invalid reference: HEAD`          | The repository has no commits                                             | The base branch needs one commit before any worktree exists                |
| `branch ... is already checked out`       | The branch already has a worktree                                         | Use a new branch, or clean up the old worktree first                       |
| `worktree.py create` refuses              | The slug, branch, or directory already exists                             | Pick another slug, or clean up first                                       |
| `guard.py check-delete` denies            | The target is outside the worktree                                        | Delete inside the worktree, use a temp dir, or ask the user                |
| Merge conflict at merge time              | The base branch moved since the worktree started                          | Merge the base into the worktree, resolve there, re-verify, hand off again |
| `git stash` conflicts across worktrees    | Stashes are shared                                                        | Do not stash. Resolve conflicts inside the worktree                        |
| `worktree.py create --repo x` refuses     | `x` is unknown in `.kilo/repos.json`, or its path is not a git repository | Register the repo in the map, or make the folder a repository first        |
| `guard.py sync --repo x` refuses to apply | The target is not a git repository                                        | Make the folder a repository, then sync again                              |

---

## 11. Relationship to the rest of the factory

- The board row is the work item; the worktree is where it happens; the row records the path.
- The builder agents (`frontend-dev`, `backend-dev`, `mobile-dev`) work inside the worktree.
- The reviewer agents (`qa-reviewer`, `ui-critic`) run against the worktree state and report
  findings; the orchestrator turns findings into `Type: Fix` board rows.
- The root `AGENTS.md` owns the rules. This skill is the executable procedure for them.
