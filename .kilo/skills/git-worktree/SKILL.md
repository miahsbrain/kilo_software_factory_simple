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

| Script | Does |
|---|---|
| `.kilo/skills/git-worktree/scripts/worktree.py` | create · resume · discard · list · verify · cleanup |
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
```

- The **branch type** comes from the row's `Type`: `Feature` → `feat`, `Fix` → `fix`,
  `Chore` → `chore`, `Docs` → `docs`, `Research` → `chore`.
- The **slug** comes from the task title, kebab-cased, trimmed to the first 6 words when it is
  longer than 48 characters.
- The branch is `<type>/<slug>` and the directory is `.kilo/worktrees/<slug>/`.
- `--slug <override>` replaces the derived slug. It must be kebab-case.
- `--base` defaults to the target repository's own base: `main` when it exists, otherwise the
  branch it names as `origin/HEAD` (the microservices use `dev`). Name one with `--base` to
  override. Use a feature branch only when the row's `Blocked by` says so.

The script refuses when the row does not exist, when the branch or directory already exists, or
when the row's type is unknown. It never deletes anything. It writes the board row in the **main
checkout**, so the live board always points at the running worktree.

**When the row already has a live worktree, `create` refuses** and prints the three ways
forward: `resume` the worktree, `discard` it, or create with `--slug <other-slug>`. A second
worktree for one row is never created.

**When the slug directory is already taken by another row's worktree, `create` refuses too**,
with a different message: it names the slug directory, the row that owns it when the board
records one, and the ways that actually work — `--slug <other-slug>`, or
`worktree.py discard --board <owning-row> --apply` for that other row. It never offers a
`resume` for a row whose worktree does not exist.

Before creating, check for an in-flight worktree on the same task:

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py list
```

---

## 2a. Env files: provisioned, never committed

A new worktree has no local env files, so the application cannot start there. `create` copies
them from the repository's **main checkout** into the new worktree, and `cleanup` removes the
copies again.

| File | Behaviour |
|---|---|
| `.env` | copied when the main checkout has it |
| `.env.local` | copied when the main checkout has it |

Nothing else travels: not `.env.production`, not `.env.example`, not any other file.

- The copy is written with mode `0600`.
- The copy is listed in the repository's `.git/info/exclude`, under a marker comment, so it can
  never be committed. The rule is written once and is idempotent.
- A destination that does not resolve under `<repo>/.kilo/worktrees/` is refused.
- **The contents are never printed.** The script reports the file name and the byte count, and
  nothing else.
- The agent's read policy on env files stays **denied**. The app reads the file; the agent runs
  the app. The policy file and `kilo.jsonc` are unchanged.

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

`resume` finds the row's live worktree, prints its path and branch, puts the row back in
`In Progress`, and re-provisions the env files. It refuses when the row has no live worktree.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <BOARD-ID>           # dry run
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <BOARD-ID> --apply
```

`discard` refuses when the worktree is dirty or when the branch holds commits the base does not
have — the same checks `cleanup` uses. With `--apply` it removes the worktree, deletes the
branch, removes the env copies, clears the row's `Branch/Worktree` cell, and writes a recovery
TSV. **Unmerged work is never deleted.**

### Forcing a discard: two steps

`--force` lets a human destroy work that the normal path refuses. It acts in two steps, and
the first step never touches anything.

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <BOARD-ID> --force
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board <BOARD-ID> --force --yes
```

**Step one — `--force` alone** prints the destruction plan: the worktree path, the branch, how
many commits the base does not have, how many files are dirty, and exactly what will be lost.
It then refuses with the command that acts. No file is written and nothing is deleted.

**Step two — `--force --yes`** acts: it removes the worktree and deletes the branch. Before it
destroys anything it writes a recovery copy under `<git-common-dir>/cleanup-wt/`:

| File | What it holds |
|---|---|
| `<timestamp>.patch` | The uncommitted changes, produced with `git diff HEAD`. Untracked files are added with intent-to-add first, so their content is in the same patch. No patch is written when the worktree is clean. |
| `<timestamp>.tsv` | One row per action, plus the sha of every commit the base does not have, with the command that restores it. |

Both paths are printed. To restore:

```bash
git apply <git-common-dir>/cleanup-wt/<timestamp>.patch     # the uncommitted changes
git branch <branch> <sha>                                    # the commits, from the TSV
```

`--force` only relaxes the refusal. It never changes the dry-run default: `--apply` still
governs acting on the normal path, and `--force` without `--yes` never acts. `--yes` without
`--force` is a usage error. The row's lane is not touched — the orchestrator owns lanes.

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
  `scopes/`) and a regenerated `kilo.jsonc` permission map. A **work surface** receives one
  generated file: `AGENTS.md`, a pointer that names the project, the canonical scope rules and the
  unit's documentation. It is a dry run unless `--apply` is given. It copies files only: it never
  deletes anything and never touches the target's `docs/`.
- The pointer is never committed. `sync` adds `AGENTS.md`, `.kilo/` and `kilo.jsonc` to the
  target's `.git/info/exclude`, which belongs to the clone, is shared by every worktree of that
  repository, and never enters a commit. A work surface's committed content is its own code.
- `sync --all` does the same for every repository in the map except the control repo.
- A pointer that is already current is left alone, and a hand-written `AGENTS.md` is never
  replaced.
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

| Context check | Fires when |
|---|---|
| `protected_branch` | the current branch is on the policy's `protected_branches` list, or is the branch the repository names as its default through `origin/HEAD` |
| `in_worktree` | the shell is **not** in a linked worktree under `.kilo/worktrees/` — `git commit` is denied in the main checkout |
| `branch_switch_in_worktree` | the shell is in a linked worktree and the command switches branches |
| `always` | always — used for the raw `git worktree remove` |

Then the `bash` rules apply with **last match wins**, exactly like Kilo.

The `edit` map is the deterministic file-change gate. Its fallback is `deny`; the only allow is
`**/.kilo/worktrees/**`. So a file tool cannot write anywhere except inside a linked worktree,
whatever the model decides. `docs/BOARD.md` is `deny` for file tools; the board is written only by
`board.py`. The map is loaded at Kilo start, so a policy change takes effect on the next session.

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
acting. It removes the env copies from the worktree first. **Never delete a worktree holding
unmerged work.**

---

## 10. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `fatal: invalid reference: HEAD` | The repository has no commits | The base branch needs one commit before any worktree exists |
| `branch ... is already checked out` | The branch already has a worktree | Use a new branch, or clean up the old worktree first |
| `worktree.py create` refuses | The slug, branch, or directory already exists | Pick another slug, or clean up first |
| `worktree.py create` refuses with resume / discard / new slug | The row already has a live worktree | `resume` it, `discard` it, or create with `--slug` — never a second worktree |
| `worktree.py create` refuses with new slug / discard <other row> | The slug directory is taken by another row's worktree | Create with `--slug`, or discard that other row's worktree with its own row id |
| `worktree.py resume` refuses | The row has no live worktree | `create` one, or `discard` the stale entry first |
| `worktree.py discard` refuses | The worktree is dirty or holds commits the base does not have | Commit or hand the work over first; unmerged work is never deleted |
| `worktree.py discard --force` refuses | `--force` alone never acts | Read the plan, then run the same command with `--force --yes` |
| The application does not start in a worktree | The env files were never provisioned | `env.py sync --board <BOARD-ID>` — never read the file yourself |
| `guard.py check-delete` denies | The target is outside the worktree | Delete inside the worktree, use a temp dir, or ask the user |
| Merge conflict at merge time | The base branch moved since the worktree started | Merge the base into the worktree, resolve there, re-verify, hand off again |
| `git stash` conflicts across worktrees | Stashes are shared | Do not stash. Resolve conflicts inside the worktree |
| `worktree.py create --repo x` refuses | `x` is unknown in `.kilo/repos.json`, or its path is not a git repository | Register the repo in the map, or make the folder a repository first |
| `guard.py sync --repo x` refuses to apply | The target is not a git repository | Make the folder a repository, then sync again |

---

## 11. Relationship to the rest of the factory

- The board row is the work item; the worktree is where it happens; the row records the path.
- The builder agents (`frontend-dev`, `backend-dev`, `mobile-dev`) work inside the worktree.
- The reviewer agents (`qa-reviewer`, `ui-critic`) run against the worktree state and report
  findings; the orchestrator turns findings into `Type: Fix` board rows.
- The root `AGENTS.md` owns the rules. This skill is the executable procedure for them.
