---
name: git-worktree
description: Create, work inside, and hand off an isolated git worktree for any change. Use before editing any file in a project that follows the worktree rule — every change happens in its own worktree on its own branch, and the merge is always the human's.
---

# Git Worktree

Every change in this factory happens in an isolated git worktree. The worktree carries the code
**and** the documentation for that change. `main` is never edited by an agent.

This skill is the CLI procedure. It uses `git` only — no `gh`, no extension, no browser.

---

## 0. The rules this skill enforces

| Rule | Why |
|---|---|
| Every change gets its own worktree | Parallel work never collides; `main` stays clean and reviewable. |
| The worktree is named after the feature | `feat/user-login`, `fix/session-timeout` — not after the agent or session. |
| Work only inside the worktree | Edits in the main checkout are invisible to review and to the merge. |
| Never commit to `main`/`master`/`base` | The human controls the base branch. |
| Never commit to an existing branch from a worktree | One branch, one worktree, one task. |
| Never merge, never push, never open a PR | The merge is a human decision. |
| Local commits on the worktree branch are required | Without commits there is nothing to merge. |
| Never delete a worktree holding unmerged work | WIP is preserved, not destroyed. |

---

## 1. Preconditions

```bash
git rev-parse --is-inside-work-tree     # must print: true
git branch --show-current                # the base branch you will branch from
git log --oneline -1                     # the commit the worktree will start from
```

If the repository has no commits, a worktree cannot branch from it. The base branch needs one
commit before any worktree can exist.

---

## 2. Create the worktree

The worktree directory is `.kilo/worktrees/<feature-slug>/` inside the repository. The branch is
`<type>/<feature-slug>` created from the base branch.

```bash
# from the repository root
git worktree add .kilo/worktrees/<feature-slug> -b <type>/<feature-slug> <base-branch>
```

- `<type>` — `feat` | `fix` | `chore` | `docs` | `refactor` | `test` | `perf`
- `<feature-slug>` — short, kebab-case, and identical to the board task slug.
- `<base-branch>` — `main` by default. Use a feature branch only when the board row's
  `Blocked by` says the work depends on it.

Example:

```bash
git worktree add .kilo/worktrees/user-login -b feat/user-login main
```

**Do not** run `git worktree add` outside `.kilo/worktrees/`. **Do not** create a worktree with
`--detach`. **Do not** reuse a branch that already has a worktree.

Verify:

```bash
git worktree list
git -C .kilo/worktrees/<feature-slug> branch --show-current
```

---

## 3. Work inside it

Every edit, every command, every verification run happens with the worktree as the working
directory:

```bash
git -C .kilo/worktrees/<feature-slug> status
git -C .kilo/worktrees/<feature-slug> diff
```

Rules while working:

- Do not edit files in the main checkout. The only exception: the live board
  (`docs/BOARD.md`), which the orchestrator writes in the main checkout.
- Do not `git checkout` another branch inside the worktree.
- Do not `git merge` the base branch into the worktree unless the task needs it, and then
  resolve conflicts inside the worktree. Never use `git stash` — stashes are shared across
  worktrees and cause conflicts.
- Keep the diff minimal: one logical change per commit.

---

## 4. Commit locally

Local commits on the worktree branch are required — they are what the human reviews and merges.

```bash
git -C .kilo/worktrees/<feature-slug> add -A
git -C .kilo/worktrees/<feature-slug> commit -m "<emoji> [<type>] <scope>: <subject>" \
  -m "- one bullet on what changed and why"
```

Message format (`AGENTS.md` §B4.1):

    📝 [docs] handover: describe the factory as it is today

    - replace the template with the real factory structure

Types: `feat fix chore refactor test perf docs ci ui security revert wip`.
Subject ≤ 72 characters, imperative voice. One logical change per commit.

**Never** `git push`, `git merge`, `git commit --amend` someone else's work, or `--force` anything.

---

## 5. Verify before handing off

Run the project's verification command from `docs/STACK.md` inside the worktree. Then produce
the evidence a reviewer needs:

```bash
git -C .kilo/worktrees/<feature-slug> log --oneline <base>..HEAD   # what is on the branch
git -C .kilo/worktrees/<feature-slug> diff --stat <base>           # what changed
git -C .kilo/worktrees/<feature-slug> diff <base>                   # the actual diff
git -C .kilo/worktrees/<feature-slug> status --short                # nothing uncommitted
```

A worktree is ready for handoff only when:

- [ ] the verification command passed, and the command + result are recorded
- [ ] every acceptance criterion on the board row has its proof recorded
- [ ] the documentation for the change is updated in the same branch
- [ ] the working tree is clean — nothing uncommitted

---

## 6. Hand off for human approval

The agent **never** merges. The handoff marks the work as needing human approval:

1. The orchestrator sets the board row to `Pending Merge` in the main checkout, with the
   worktree path and branch in the `Branch/Worktree` column.
2. The agent reports: what was done, what is proven, what is not done and why, and the next
   action.
3. The agent prints the exact commands for the human to review and merge.

```bash
# review
git worktree list
git -C .kilo/worktrees/<feature-slug> log --oneline main..HEAD
git -C .kilo/worktrees/<feature-slug> diff main

# merge — run by the human, in the main checkout
git merge --no-ff <type>/<feature-slug> -m "merge: <feature-slug>"

# cleanup — run by the human, after the merge
git worktree remove .kilo/worktrees/<feature-slug>
git branch -d <type>/<feature-slug>
```

The merge target is the human's call: `main`, or a feature branch when the work is part of a
larger feature. Either way the agent only prepares it.

---

## 7. Clean up

After the human merges:

```bash
git worktree remove .kilo/worktrees/<feature-slug>   # only if the branch is merged
git branch -d <type>/<feature-slug>
```

Guardrails:

- **Never** remove a worktree whose branch has unmerged commits. Check first:
  `git -C .kilo/worktrees/<feature-slug> log --oneline main..HEAD` must be empty.
- **Never** remove the main checkout or a worktree with a running process.
- **Never** delete worktrees outside `.kilo/worktrees/`.

---

## 8. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `fatal: invalid reference: HEAD` | The repository has no commits | The base branch needs one commit before any worktree exists |
| `fatal: '<branch>' is already checked out` | The branch already has a worktree | Use a new branch, or remove the old worktree first |
| Merge conflict at merge time | The base branch moved since the worktree started | Merge the base into the worktree, resolve there, re-verify, then hand off again |
| `git stash` conflicts across worktrees | Stashes are shared | Do not stash. Resolve conflicts inside the worktree |
| Worktree looks empty | The base branch had no commits | Commit on the base branch first |

---

## 9. Relationship to the rest of the factory

- The board row is the work item. The worktree is where it happens. The row records the path.
- The builder agents (`frontend-dev`, `backend-dev`, `mobile-dev`) work inside the worktree.
- The reviewer agents (`qa-reviewer`, `ui-critic`) run against the worktree state and report
  findings; the orchestrator turns findings into `Type: Fix` board rows.
- The root `AGENTS.md` owns the rules. This skill is the executable procedure for them.
