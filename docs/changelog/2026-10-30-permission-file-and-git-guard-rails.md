# Permission file and git guard rails — 2026-10-30

**Board:** BOARD-001 | **Branch:** feat/add-a-permission-file-and-git

## What changed

The factory had guard rails written down but nothing that stopped an agent. The rules said never
push, never commit on `main`, never switch branches inside a worktree — and every one of them was
a sentence an agent could skip.

Now there is one file that holds the rules, `.kilo/policies/git-policy.json`, and two layers read
from it:

- the `permission` map in `kilo.jsonc`, generated from the policy and never hand-edited, which
  stops a command before it runs;
- `guard.py check-git`, which reads the same policy at runtime and answers allow / ask / deny.

`guard.py check-policy` proves the two layers still match, and `check-policy --write` regenerates
the map after the policy changes.

## Why one policy file

Two copies of the same rules drift. The map in `kilo.jsonc` and the rules the script reads would
answer differently the first time someone added a rule to one of them and forgot the other.

With one file, the rules have one home. The map becomes a build artefact, not a second source of
truth, and a check can prove the two agree.

The policy also carries the **reason** for each rule next to the rule, so the refusal an agent
prints says why the rule exists rather than only that a rule matched.

## Why last-match-wins ordering

Kilo evaluates permission rules in config order and the **last matching rule wins**. The generated
map therefore puts the broad fallback first and the narrow exceptions after it:

```
"git *": "ask",          <- the broad net, first
"git status*": "allow",  <- the narrow exceptions, after it
"git push*": "deny",     <- the irreversible, last
```

A map written the other way round would be useless: `git push` would match `git *` first and the
narrow rule would never be reached. The ordering is therefore not a style choice — it is what
makes the specific rules reachable at all.

## Why the context checks live in the script and not in the permission map

A permission pattern sees a command string. It cannot see the state the command would run in.

Three rules depend on context, so they live in `guard.py`:

1. **No commit on `main`/`master`/`base`.** The command string `git commit -m "fix"` is identical
   on a worktree branch and on the base branch. Only the current branch decides whether it is
   allowed. A keyword list cannot express that.
2. **No branch switch inside a worktree.** `git switch feat/x` is a normal command in the main
   checkout and a destructive one inside a worktree, where it moves the working tree out from
   under the agent. Only the worktree state decides.
3. **No raw `git worktree remove`.** The command is always the same; whether it is safe depends on
   whether the branch is merged and the tree is clean. `worktree.py cleanup` checks both, so the
   guard points at that script instead.

`check-git` evaluates the context checks **first**, because they are more specific than any
keyword list: a commit on `main` is denied even though `git commit` is on the allow list.

## The known limitation

A permission pattern cannot see a command that a shell wrapper hides. A command run through a
wrapper script, an alias, a `make` target, or any indirection that rewrites the command before git
sees it does not match the pattern, and the guard reads the command as given, not as executed.

This is a real gap. The mitigation is that the policy denies `git push` and the other irreversible
commands at the point where they are typed, and the human still merges. A command hidden behind a
wrapper is a case the human review catches, not one the map can.

## Verification

    python3 .kilo/skills/git-worktree/scripts/guard.py check-policy          # exit 0, "policy in sync"
    python3 .kilo/skills/git-worktree/scripts/guard.py check-git -- "git push origin main"   # exit 1
    python3 .kilo/skills/git-worktree/scripts/guard.py check-git -- "git merge feat/x"       # exit 3
