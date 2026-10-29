# Port super-board mechanics into factory scripts

**Date:** 2026-10-29
**Branch:** `feat/port-super-board-scripts`
**Board:** BOARD-005
**Source:** `EricTechPro/super-board` (MIT), analysed at `.tmp/super-board`

## The idea being ported

super-board does not ask an agent to "be careful with deletes" or "remember to update the board".
It ships scripts that do those things, and the skill tells the agent to run them. The division is
simple: **the agent supplies judgment, the script supplies mechanics.** A rule that can be a
script is a script, because a rule an agent is trusted to follow is not a rule.

Four upstream pieces were portable to a CLI-only, GitHub-free factory:

| Upstream | Ported as |
|---|---|
| `hooks/guard-delete-outside.py` | `.kilo/skills/git-worktree/scripts/guard.py` |
| `hooks/guard-worktree-path.py` | the same script, `check-worktree` |
| `hooks/cleanup-wt.py` | `.kilo/skills/git-worktree/scripts/worktree.py cleanup` |
| `scripts/super-board-card.sh` | `.kilo/skills/board/scripts/board.py` |
| `skills/super-qa/scripts/runtime_browser.mjs` | `.kilo/skills/qa-review/scripts/browser-review.mjs` |
| `scripts/super-qa-file-bug.sh` (body validation only) | `.kilo/skills/qa-review/scripts/check-finding.py` |

The upstream hook payload format was dropped: Kilo has no hook runner, so the guard is a CLI
command the agent runs before a destructive command, and the refusal is a non-zero exit.

## What is stricter here

Upstream blocks deletion **outside the project**. This factory blocks deletion **outside the
current linked worktree**:

- Allowed: the current linked worktree, and temp dirs under `/tmp` or `$TMPDIR`.
- Denied: the main checkout, the repository root, `/`, `$HOME`, and any *other* linked worktree.

The delete guard also covers `git clean`, `git worktree remove`, `git branch -D`,
`git reset --hard`, and `git checkout --` — not just `rm`.

## The board stopped being hand-edited

The live board was the least deterministic part of the factory: a markdown table the orchestrator
edited by hand, where a stray pipe or a mis-typed row breaks the table. `board.py` now owns
`add`, `set-status`, `set-field`, `remove`, `show`, and `lanes`, and rewrites the file atomically.

## QA findings must earn their row

Upstream refuses to file a weak ticket. `check-finding.py` ports that: a finding must have a
summary, two repro steps, expected behavior, actual behavior, evidence, two acceptance criteria,
and a risk line that states the level, the blast radius, and whether the fix is one-way or
two-way. Placeholders (`TBD`, `TODO:`, `<...>`) are refused. A weak finding exits 66 instead of
becoming a row nobody can act on.

## Not ported

Upstream's GitHub Project board, `gh` issue and PR automation, the BFS route crawler, the
headless dispatcher, the model routing ladder, and the `mattpocock-skills` dependency chain.
This factory has a local markdown board and a CLI. The upstream queue crawler would need a queue
file and a spec suite, which is a later decision, not a port.

## Result

Five commands replace what used to be prose:

```bash
python3 .kilo/skills/git-worktree/scripts/worktree.py create <slug> --type <type> --base <base>
python3 .kilo/skills/git-worktree/scripts/guard.py check-delete -- "<command>"
python3 .kilo/skills/board/scripts/board.py set-status <ID> "In Progress"
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url <url> --route /path --artifact-dir <dir>
python3 .kilo/skills/qa-review/scripts/check-finding.py --body-file <finding.md>
```
