# The specialist skills, ported as a read-on-demand catalogue

**Date:** 2026-11-10
**Board:** BOARD-107
**Branch:** `feat/port-the-specialist-skill-catalog`

## What changed

The upstream catalogue at https://github.com/Jeffallan/claude-skills (MIT, © 2025 Jeffallan) is
ported into this repository as `.kilo/catalog/`: 67 skill folders, each a `SKILL.md` plus a
`references/` folder, and an index at `.kilo/catalog/README.md`.

## Why it lives outside the skills folder

Kilo's skill loader scans directories named `skill`/`skills` inside a config directory. A
catalogue placed under `.kilo/skills/` would be discovered, and 67 skills would enter the
system prompt on every session — most of them irrelevant to the task at hand, and all of them
paid for.

`.kilo/catalog/` is invisible to the loader. Nothing is discovered, nothing is injected, and
the catalogue costs no context until an agent opens a file. The agent reaches a skill by
reading `.kilo/catalog/<skill>/SKILL.md` when the task is in that skill's domain.

Verified: `kilo debug skill` in the worktree lists exactly six skills — `board`,
`git-worktree`, `qa-review`, `plan`, `unslop` and the builtin `kilo-config` — and none of the
67 catalogue skills.

## The layout

    .kilo/catalog/
      README.md              # the index: one row per skill
      <skill>/
        SKILL.md             # the upstream file, with a three-line header
        references/          # the upstream reference material, intact

## The light adaptation pass

The upstream text is not rewritten. Each file keeps its upstream bytes apart from two edits:

1. **A three-line header**, immediately after the `SKILL.md` H1 title, stating that this
   repository's rules win, mapping the Claude Code tool names onto this harness, and carrying the
   MIT attribution.

       > **This repository's rules win.** Where this upstream skill and `AGENTS.md` disagree, `AGENTS.md` wins.
       > Tool names in this file are Claude Code names. In this harness: `AskUserQuestion` → the `question` tool, `Task` and subagents → the `Task` tool, `TodoWrite` → `todowrite`, `Read` / `Write` / `Edit` → `read` / `write` / `edit`, `Bash` → `bash`, `Grep` / `Glob` → `grep` / `glob`.
       > Attribution: MIT, © 2025 Jeffallan, from https://github.com/Jeffallan/claude-skills.

2. **Tool names in the body**, only where the name would mislead:

   | Upstream | Here | Count |
   |---|---|---|
   | `AskUserQuestion` / `AskUserQuestions` | `question tool` | 20 |
   | `subagent` / `subagents` / `Subagents` | `Task tool agent` / `Task tool agents` | 13 |

   `Read tool`, `Write tool`, `Edit tool`, `Bash tool`, `Grep tool`, `Glob tool` and `TodoWrite`
   are left alone — the header maps them. The `subagent_type=` parameter in the upstream
   `Task(...)` call examples is left alone as well: it is a parameter of the `Task` tool, not a
   tool name, and the header already says that `Task` and subagents mean the `Task` tool.

## The wiring

- `AGENTS.md` §A7 gains a **Specialist skills** section: the index path, the rule that the
  agent reads the matching `SKILL.md` when the task is in that domain, and the precedence rule
  stated once — this repository's rules win.
- Each builder agent file names its own specialists and the path to read:
  `frontend-dev` (8), `backend-dev` (16), `mobile-dev` (4), `qa-reviewer` (3), `docs-writer` (1).
- `guard.py`'s `SYNC_SLICE` gains `catalog`, so `guard.py sync` carries the catalogue into a
  project that receives the harness.

## Attribution

MIT, © 2025 Jeffallan, from https://github.com/Jeffallan/claude-skills. Every skill keeps its
upstream `license: MIT` frontmatter and its `author: https://github.com/Jeffallan` line. One
skill, `django-storages-s3`, carries a contributor's author line upstream and is left as it is.
