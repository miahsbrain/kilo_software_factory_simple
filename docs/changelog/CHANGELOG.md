# CHANGELOG

Newest first. Append-only. One section per change.
Full rationale for a change lives in `docs/changelog/<YYYY-MM-DD>-<slug>.md`.

## [2026-11-11] OpenCode V2 port, chunk 1
**Type:** Chore
**Board:** BOARD-114 | **Branch:** feat/port-factory-harness-to-opencode-v2
**Changed:** tracked `.kilo/` harness moved to `.opencode/` with plural agents/commands; `opencode.jsonc`; existing Python/JS path references, native permission generator, factory base selector, templates and active docs. Added architect primary because no existing primary orchestrator definition covered that role; retained six specialists and upstream licences. App base semantics unchanged.
**Why:** Approved OpenCode-only integration port on `opencode`; `main` retains Kilo. Reused lifecycle, env, scope, board and QA mechanics rather than introducing replacement tools.
**Impact:** Chunk 1 only, not merge-ready. Bootstrap worktree stays unmoved and ignored; steady-state guards accept only `.opencode/worktrees/`. Security plugin/search-path enforcement, native runtime validation and devcontainer migration remain later work. No dependencies, commit, merge or push.
**Verification:** `python3 .opencode/skills/git-worktree/scripts/test_env.py` → exit 0, `all checks passed`; the only verification command. Runtime package ignores are root-anchored so moved board UI manifests remain trackable.

## [2026-11-11] The /plan and /unslop commands
**Type:** Chore
**Board:** BOARD-113 | **Branch:** chore/add-plan-and-unslop-commands
**Changed:** `.kilo/command/plan.md`, `.kilo/command/unslop.md`, `docs/UI-UX.md` §2.1, `docs/changelog/CHANGELOG.md`
**Why:** The plan and unslop skills sit in `.kilo/skills/`, but the skill loader does not expose them, so neither was discoverable as a command. Both procedures were already the rules; they were only reachable by asking.
**Impact:** `/plan` packages the plan skill's five phases into a product-planning shortcut that points at the decision gate; `/unslop` packages the unslop procedure — direction, sign audit, nine passes, checklist — and writes the audit to `docs/reviews/<task-id>-unslop.md`. Neither command adds a rule: both name the by-path read and defer to `AGENTS.md`. The command directory is part of the harness slice, so a project copy carries both.

## [2026-11-11] The board screen becomes a dense dashboard
**Type:** Feature
**Board:** BOARD-112 | **Branch:** feat/rebuild-factory-pages-as-a-split
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `.kilo/skills/board/ui/src/app.css`, `.kilo/skills/board/static/board.css`, `docs/UI-UX.md` §6.2, `docs/reviews/BOARD-112-*.md`, `docs/changelog/CHANGELOG.md`
**Why:** The board was still the single-column console while `/gallery` already carried the approved dashboard shell. The user asked for an elegant, dense, useful dashboard, so the real board moved onto the same components.
**Impact:** `GET /` now renders a 240px lane/filter sidebar, a main column with a KPI strip, flow meter and lane panel, and a 320px sticky worktrees rail. All filters, search, keyboard, URL state, folds, pause/refresh, parsed Notes and branch copy are preserved. The old inline CSS and its renderers are removed; the Tailwind stylesheet is the only style system. Footer pluralisation and the copy-button tap target were fixed from the review.

## [2026-11-11] The factory page language moves to Tailwind
**Type:** Feature
**Board:** BOARD-112 | **Branch:** feat/rebuild-factory-pages-as-a-split
**Changed:** `.kilo/skills/board/ui/package.json`, `.kilo/skills/board/ui/package-lock.json`, `.kilo/skills/board/ui/src/app.css`, `.kilo/skills/board/static/board.css`, `.kilo/skills/board/static/fonts/*`, `.kilo/skills/board/scripts/board_serve.py`, `.kilo/skills/board/SKILL.md`, `docs/DECISIONS.md` (ADR-072), `docs/STACK.md`, `docs/UI-UX.md` §6.2, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-11-factory-tailwind.md`
**Why:** The board screen read as a generic Bootstrap-style stack, and the single-file hand-written CSS made a consistent component language slow to evolve. The user chose Tailwind v4 with a self-hosted Geist pair and a Swiss-industrial direction.
**Impact:** The board UI is now built from Tailwind v4 at author time into one committed stylesheet; the runtime stays Python-standard-library and offline. `GET /gallery` is rebuilt in the new language; the board screen moves onto the same components in the next chunk. Self-hosted Geist Sans/Mono (SIL OFL) replace system fonts, so the page is noticeably more distinctive and the repo grows by about 140 KB of woff2. A class change now requires `npm --prefix .kilo/skills/board/ui run build`.

## [2026-11-11] The factory page language and component gallery
**Type:** Feature
**Board:** BOARD-112 | **Branch:** feat/rebuild-factory-pages-as-a-split
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/UI-UX.md` §6.2, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-11-factory-workbench.md`
**Why:** The split-workbench direction needed a settled token set and a reusable component factory before the board screen could be rebuilt. The gallery is the human approval artefact for that language.
**Impact:** Light and dark colour tokens move to paper/graphite with one signal-orange accent, and a `wb-` component set is shared by `/gallery` and, in the next chunk, the board. `GET /` keeps its structure, filters, keyboard and URL state, and gains one quiet footer link to `/gallery`. Routing, dependencies and the read-only, server-rendered, offline behaviour are unchanged.

## [2026-11-11] The unslop pass is mandatory on every UI change
**Type:** Docs
**Board:** BOARD-111 | **Branch:** docs/make-the-unslop-pass-mandatory
**Changed:** `AGENTS.md` (§B4.2, §B4.3), `docs/UI-UX.md` (§2.1), `.kilo/agent/ui-critic.md`, `.kilo/agent/frontend-dev.md`, `.kilo/skills/qa-review/SKILL.md`, `docs/changelog/CHANGELOG.md`
**Why:** The BOARD-109 review read the unslop signs list but never ran the unslop procedure, and the loader does not expose the `unslop` skill, so nothing forced an agent to open it. A real audit of the merged console then found uppercase tracked labels, negative tracking on small text, redundant 650/700 weights and five equal stat cards — signs the QA and UI pass had let through.
**Impact:** Every UI change now runs the full unslop procedure — five-line direction, full `references/signs.md` audit, nine passes, checklist — in the same review round as the QA capture, recorded in the UI report. A UI row with no recorded unslop audit cannot leave `In Review`. The skill is opened by path because the loader does not expose it. Precedence is unchanged: where the skill and `AGENTS.md` disagree, `AGENTS.md` wins, and the conflict is reported.

## [2026-11-11] The board console passes the unslop audit
**Type:** Fix
**Board:** BOARD-110 | **Branch:** fix/fix-the-unslop-signs-in-the-board-console
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/UI-UX.md` §6.1, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-11-unslop-board-console.md`
**Why:** The merged console (BOARD-109) tripped four sign groups in `.kilo/skills/unslop/references/signs.md`: five equal stat cards for the lane counts, uppercase tracked labels, negative tracking on small text, and weights of 650 and 700. The palette, type scale, layout and controls were already right, so this is a polish pass only.
**Impact:** The five lane counts are one framed flow instrument of five hairline-separated stops; only the stop with the highest non-zero count carries the accent, and on mobile the instrument scrolls rather than stacking. Lane names and table headers are sentence case with normal tracking, small-text tracking is zero, and every weight is 400, 500 or 600. Counts, click-to-filter, aria-pressed sync and the all-clear headline are unchanged; the viewer stays read-only, server-rendered and offline.

## [2026-11-10] The live board becomes a factory console
**Type:** Feature
**Board:** BOARD-109 | **Branch:** feat/elevate-the-live-board-ui-into-a-factory-console
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `.kilo/skills/board/SKILL.md`, `docs/UI-UX.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-factory-board-console.md`
**Why:** The viewer was a vertical accordion that showed cards but not the shape of the flow, and its lane and notes content was slow to scan. The board is the orchestrator's main surface, so it needs a dense, keyboard-first console with filters, parsed acceptance criteria and the worktree state in the same view.
**Impact:** `GET /` now renders again after a `TypeError` in `render_pipeline()` that broke the whole page while `/health` and the JSON endpoints stayed up. The page keeps its read-only, server-rendered, offline behaviour, and `/api/board` and `/api/worktrees` are unchanged. The visual language is recorded in `docs/UI-UX.md` §6.1.

## [2026-11-10] The teardown command sets the board lane
**Type:** Fix
**Board:** BOARD-108 | **Branch:** fix/cleanup-and-discard-set-the-board
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-cleanup-and-discard-set-the-lane.md`
**Why:** `worktree.py cleanup --board BOARD-107 --apply` removed the worktree, deleted the branch and cleared the row's `Branch/Worktree` cell, but left the row in `Pending Merge`. The lane is the source of truth for what is in flight, so a row whose branch is merged and whose worktree is gone must read `Merged`. A discard left the same confusion in `In Progress`.
**Impact:** The teardown command owns the lane for the row it tears down (ADR-071). `cleanup --board <ID> --apply` puts the row in `Merged` and clears the cell; `discard --board <ID> --apply` puts the row back in `Ready` and clears it; the slug form of `cleanup` cannot know the row and touches nothing on the board. `clear_row_worktree` takes the lane as an argument and writes the lane cell and the worktree cell in the same atomic write, so they never drift. A refused cleanup or discard changes nothing on the board. The board write stays in the control repo's main checkout. `AGENTS.md` §B4 rule 12 and §B3 say the script is the board's writer for a teardown the human runs, so the orchestrator does not set the lane by hand afterwards.

## [2026-11-10] The specialist skills, ported as a read-on-demand catalogue
**Type:** Feature
**Board:** BOARD-107 | **Branch:** feat/port-the-specialist-skill-catalog
**Changed:** `.kilo/catalog/` (67 skill folders + `README.md`, 438 upstream markdown files), `AGENTS.md`, `.kilo/agent/frontend-dev.md`, `.kilo/agent/backend-dev.md`, `.kilo/agent/mobile-dev.md`, `.kilo/agent/qa-reviewer.md`, `.kilo/agent/docs-writer.md`, `.kilo/skills/git-worktree/scripts/guard.py`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STRUCTURE.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-specialist-skill-catalog.md`
**Why:** The builders need specialist depth — a React, a FastAPI, a Postgres, a Playwright expert — without 67 skills crowding the system prompt. The upstream catalogue (MIT, © 2025 Jeffallan, https://github.com/Jeffallan/claude-skills) is kept as files the agent reads when the task is in that domain.
**Impact:** The catalogue lives at `.kilo/catalog/<skill>/`, outside the auto-discovered skills folder: the loader only scans directories named `skill`/`skills`, so `.kilo/catalog/` is invisible to it and none of the 67 skills enters the system prompt. `kilo debug skill` still lists exactly the six repository skills — `board`, `git-worktree`, `qa-review`, `plan`, `unslop`, `kilo-config`. Every upstream file is carried over byte for byte with its MIT frontmatter; each `SKILL.md` gains a three-line header that maps the Claude Code tool names onto this harness, and 20 `AskUserQuestion` mentions plus 13 subagent mentions in the body become `question tool` and `Task tool agent`. The index at `.kilo/catalog/README.md` is read first, then the one matching `SKILL.md`. `AGENTS.md` §A7 gains a Specialist skills section that states the precedence rule once — this repository's rules win — and each builder agent file names its own specialists. `guard.py sync` now carries `catalog` in its slice, so a project receives the catalogue with the rest of the harness.

## [2026-11-10] The plan skill, merged from two upstream skills
**Type:** Feature
**Board:** BOARD-106 | **Branch:** feat/port-a-merged-plan-skill
**Changed:** `.kilo/skills/plan/` (SKILL.md, references/ ×12), `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STRUCTURE.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-plan-skill.md`
**Why:** A new project or a large feature needs a planning procedure that writes into the documents this repository already has. The upstream `feature-forge` and `architecture-designer` skills carry the question banks, the specification template, the EARS syntax, the ADR template and the NFR checklist, and nothing of their own was kept.
**Impact:** One merged skill at `.kilo/skills/plan/`, with all twelve upstream references carried over intact under their MIT credit lines. Each of the five phases names the document it writes into: `DOMAIN.md`, `docs/BUSINESS-LOGIC.md`, `docs/DECISIONS.md`, `docs/RISKS.md`, `docs/STACK.md`, `ROADMAP.md` and `docs/BOARD.md`. The upstream `AskUserQuestions` tool becomes the `question` tool, the upstream `Task` subagents become this harness's `Task` tool, and the upstream "write a spec document" step becomes "write into the mapped document". The precedence rule is stated once, in the skill, and referenced from `AGENTS.md` §A2, §A4 and §A6. Attribution: MIT, © 2025 Jeffallan for the two upstream skills; MIT, © Jesse Vincent for the two superpowers research documents.

## [2026-11-10] The unslop skill, adopted and merged into the QA lane
**Type:** Feature
**Board:** BOARD-105 | **Branch:** feat/add-the-unslop-skill-and-merge
**Changed:** `.kilo/skills/unslop/` (SKILL.md, references/, scripts/snapshot.mjs, examples/), `.kilo/skills/qa-review/SKILL.md`, `.kilo/agent/ui-critic.md`, `AGENTS.md`, `docs/UI-UX.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/PROJECT_STRUCTURE.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-unslop-skill-and-qa-checker.md`
**Why:** The 15 anti-slop rules catch the loud tells but not the quiet ones — a stray `mt-[13px]`, a mixed number format, an icon nudged off its column. The upstream skill carries a full sign-by-sign checklist, and it belongs in the lanes that judge a screen.
**Impact:** The unslop skill (Damir Sokolovsky, CC BY 4.0) is adopted as a standalone skill at `.kilo/skills/unslop/`, and its signs list is merged into the QA lane: `AGENTS.md` §B4.3 states the precedence rule once, the qa-review skill and the ui-critic agent each add the unslop pass, and `docs/UI-UX.md` §2.1 points at the list. The story video and every image-generation instruction are removed, so a visual is built in code; `scripts/snapshot.mjs` resolves Playwright and chromium the way the QA script does and exits 2 when no browser is found. The credit line survives in every copied file.

## [2026-11-10] The teardown is named by the board row
**Type:** Feature
**Board:** BOARD-104 | **Branch:** feat/hand-off-names-the-teardown
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** The hand-off block named the cleanup by slug and listed the worktree removal and the branch deletion as loose lines, so the human had to read the path back out of the block to run the teardown.
**Impact:** `worktree.py cleanup` takes `--board <ID>` as an alternative to the slug: it resolves the row's `Branch/Worktree` cell, runs the same cleanup, and clears that cell when the worktree is gone. Giving a slug and `--board` together, or neither, is a usage error. The hand-off block now ends with a teardown section that names `cleanup --board <ID> --apply` and, below it, the manual `git worktree remove` and `git branch -d` pair; the old cleanup lines are gone from the block. `AGENTS.md` §B5 says the block ends with that command. The slug form of `cleanup` and every other command keep their behaviour.

## [2026-11-10] The hand-off block, printed by the script
**Type:** Feature
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** Every work session had to hand the human the merge command, and usually forgot the diff command, so the human could not review the work before merging it.
**Impact:** `worktree.py handoff --board <ID>` prints the hand-off block for a row's worktree: the path, the branch, the base, the diff command, the log command, the merge command and the cleanup command. It prints commands and paths only and never changes anything. A branch already merged into the base gets a `git show --stat` line instead of a merge command that would fail. `AGENTS.md` §B5 now requires every session report for work in a worktree to end with that block, diff command first.

## [2026-11-10] Forced discard, confirmed in two steps
**Type:** Feature
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** `discard` refused a dirty worktree or a branch with unmerged commits, so the only way to destroy that work was by hand, and a hand `git worktree remove --force` left nothing behind to recover from.
**Impact:** `discard --force` alone prints the destruction plan — the path, the branch, the unmerged and dirty counts and exactly what is lost — and refuses without writing a file or deleting anything. `discard --force --yes` acts, and before it destroys anything it writes the uncommitted changes as a patch and the lost commit shas into the recovery files under the repository's `cleanup-wt/` folder, printing both paths. `--force` only relaxes the refusal: `--apply` still governs acting on the normal path, and `--yes` without `--force` is a usage error. The policy, the permission map and the board are unchanged.

## [2026-11-10] Corrective round: distinct create refusals, section order, symlink-safe env copy
**Type:** Fix
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/env.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-11-10-provision-env-files-and-reuse-worktrees.md`
**Why:** The review found that `create` used one refusal message for two situations, so a row whose slug directory was taken by another row was told to `resume` or `discard` a worktree it did not have — a circle. The two new SKILL.md sections were also numbered 2b and 2c but placed before the existing 2a, and the env copy followed a symlink planted at the destination.
**Impact:** `create` now prints a separate message when the slug directory belongs to another row: it names the owning row when the board records one and offers only a new `--slug` or `discard` for that owning row. The SKILL.md sections now read 2a Env files, 2b Reuse a worktree, 2c Repos. The env copy is written with `O_NOFOLLOW`, so a symlink at the destination is replaced by the copy instead of being written through. No change to the policy, the permission map or the board.

## [2026-11-10] Provision env files into worktrees and reuse an existing worktree
**Type:** Feature
**Board:** BOARD-103 | **Branch:** feat/provision-env-files-into-worktrees
**Changed:** `.kilo/skills/git-worktree/scripts/env.py`, `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/git-worktree/scripts/test_env.py`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/DECISIONS.md`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`
**Why:** A new worktree had no local env files, so the application could not start there, and the agent could not read or copy them because the policy denies reading them. Separately, `worktree.py create` did not notice a worktree that already existed for the same board row, so agents piled up duplicates.
**Impact:** `create` copies `.env` and `.env.local` from the repository's main checkout into the new worktree with mode `0600` and lists them in the repository's `.git/info/exclude`; the contents are never printed and the read policy is unchanged. `create` now refuses when the row already has a live worktree and prints the resume / discard / new-slug options. New `resume` and `discard` commands reuse or remove that worktree, `cleanup` removes the env copies, and `list` gained a `state` column. No behaviour change to the existing commands beyond the new refusal and the env provisioning.

## [2026-11-04] Board heading gets the page gutter
**Type:** Fix
**Board:** BOARD-102 | **Branch:** feat/compact-accordion-redesign-of-the-live
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/changelog/CHANGELOG.md`
**Why:** The board section had no CSS rule, so its heading and count line ran flush to the viewport edge while the lane stack and the header had a 24px gutter.
**Impact:** The board section now carries the same horizontal gutter as the header and the lane stack, and the lane stack's own margins were made relative so its cards stay aligned with the heading above them. Content, behaviour, the JSON endpoints and the escaping are unchanged.

## [2026-11-04] Board viewer fixes from QA round 1
**Type:** Fix
**Board:** BOARD-102 | **Branch:** feat/compact-accordion-redesign-of-the-live
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/changelog/CHANGELOG.md`
**Why:** The first QA pass found text clipped at narrow widths, a favicon request to the network, and lanes that looked populated while holding no cards.
**Impact:** Long values now wrap instead of clipping, the favicon is inline so the page makes no extra request, a lane with no cards stays collapsed, the board path is shown as a path, and a 480px breakpoint tightens the header, filter and panels. Content, behaviour, the JSON endpoints and the escaping are unchanged.

## [2026-11-04] Compact accordion board viewer
**Type:** Feature
**Board:** BOARD-102 | **Branch:** feat/compact-accordion-redesign-of-the-live
**Changed:** `.kilo/skills/board/scripts/board_serve.py`, `docs/HANDOVER.md`, `docs/changelog/CHANGELOG.md`
**Why:** The viewer was a horizontal kanban with every lane always open, so the growing Merged lane forced an endless scroll and hid the work that was in flight.
**Impact:** The dashboard now renders the lanes as a vertical accordion of collapsible sections, cards as compact rows that expand to their detail, the Merged lane as the last 10 rows with a "Show all" control, and fold state kept in the browser. Read-only behaviour, the board file and the JSON endpoints are unchanged.

## [2026-11-02] Make worktree-only changes deterministic
**Type:** Fix
**Board:** BOARD-001 | **Branch:** chore/enforce-worktree-only-changes-and-serve
**Changed:** `.kilo/policies/git-policy.json`, `kilo.jsonc`, `.kilo/skills/git-worktree/scripts/guard.py`, `.kilo/skills/git-worktree/SKILL.md`, `.kilo/skills/board/scripts/board_serve.py`, `docs/changelog/CHANGELOG.md`
**Why:** The worktree rule was prose the model had to obey. Edits in the main checkout were allowed, `git commit` was allow-listed, no hook enforced the rule, and the board server showed one board.
**Impact:** The `edit` permission map now denies every path by default and allows only `**/.kilo/worktrees/**`; `docs/BOARD.md` is denied to file tools. A new `in_worktree` policy check denies `git commit` in the main checkout, and `guard.py install-hooks` writes a fail-closed pre-commit hook into the control repo and every mapped repository. `board_serve.py` discovers and renders both the harness board and the project board, and `/api/board` returns both. Verified: main-checkout commit denied, worktree commit allowed, `check-policy` in sync, both boards listed over HTTP.

## [2026-11-02] Close the last two gaps in the worktree rule
**Type:** Fix
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `.kilo/skills/git-worktree/scripts/{guard.py,worktree.py}`, `.kilo/policies/git-policy.json`, `.kilo/skills/git-worktree/SKILL.md`, `AGENTS.md`, `docs/changelog/CHANGELOG.md`
**Why:** Two things were documented but not true. A commit straight onto `dev` in a microservice was allowed, because only `main`, `master` and `base` were protected, and the microservices base on `dev`. And `worktree.py create` wrote the pointer into the new worktree but not into the repository root, so a brand-new repository had no pointer until a separate `sync` ran.
**Impact:** `protected_branches` in `.kilo/policies/git-policy.json` now names `dev` as well, and the repository's own default branch from `origin/HEAD` is always added. `guard.py check-git` refuses a commit on the base branch in every repository. `worktree.py create` writes the pointer into the repository root and into the new worktree, so a new repository is complete the moment its first worktree is created. Verified on a throwaway repository: the pointer appeared in both places, was excluded from git, a commit on `dev` was blocked and a commit on the worktree branch was allowed.

## [2026-11-02] Give a work surface a pointer instead of a copy of the rules
**Type:** Chore
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `.kilo/skills/git-worktree/scripts/{scope.py,guard.py,worktree.py}`, `.kilo/skills/board/scripts/board.py`, `.kilo/skills/git-worktree/SKILL.md`, `.kilo/scopes/service.md`, `AGENTS.md`, `docs/{DECISIONS,HANDOVER,PROJECT_STRUCTURE}.md`, `docs/changelog/CHANGELOG.md`
**Why:** The harness was copied into every work surface, so a factory change had to be re-applied in every application repository and the factory could not grow without touching them all. The board was also unreachable from inside a work surface, because the harness looked for `apps/<repo>/docs/BOARD.md`.
**Impact:** The harness stays in the control repo. A work surface receives one generated file, `AGENTS.md`, that names the project, the canonical scope rules and the unit's documentation; it is listed in the repository's `.git/info/exclude`, so it is never committed. `guard.py sync --all` refreshes every pointer in one command. The harness now finds the control repo by walking up, so the board, the repo map and the guard rails work from inside any work surface. ADR-058, ADR-059 and ADR-060 record the decisions. No application behaviour changes.

## [2026-11-02] Split the factory from the project
**Type:** Chore
**Board:** - | **Branch:** chore/split-factory-and-project
**Changed:** `AGENTS.md` (§A1 "The factory and the project", §A2 boot sequence), `README.md`, `.gitignore` (ignores `/project/`), `.kilo/repos.json` (the control repo only), `docs/{BOARD,DECISIONS,ENVIRONMENT,HANDOVER,PROJECT_STATE,PROJECT_STRUCTURE,README,STACK}.md` (rewritten for the factory), `docs/changelog/CHANGELOG.md`, `templates/project/**` (new: the blank project skeleton)
**Why:** The factory and the product shared one repository, so 79 project handover files, the platform architecture and the product's risk register were committed to the software factory, and the factory's board carried product rows.
**Impact:** The factory holds the harness only — rules, agents, commands, skills, policies, scope rules and the blank project skeleton. The Inhouz Cloud AI platform is its own git repository in `project/`, with its own board, documentation set, domain rules and 75 application repositories. `guard.py check-repos` exits 0 in both. The decision log is split: ADR-001 to ADR-099 are the factory's, the project's own decisions start at ADR-100. A project copies the harness in and owns the copy, so a factory change does not reach a project automatically. No behaviour changes.

## [2026-10-30] Deny every tool read access to git config, credential and .env files
**Type:** Security
**Board:** - | **Branch:** main (uncommitted)
**Changed:** `.kilo/policies/git-policy.json` (expanded `hidden_paths`, added `allow` list and edit denials), `.kilo/skills/git-worktree/scripts/guard.py` (expands `hidden_paths` into `read`/`grep`/`glob`/`list` deny rules and honours the allow list; `check-policy` compares every generated tool key), `kilo.jsonc` (generated), `.devcontainer/kilo-redact.sh` (new protected-file guard in the `$BASH_ENV` startup file), `.devcontainer/test-kilo-redact.sh` (10 guard checks), `.devcontainer/devcontainer.json` (`KILO_CONFIG` points at the root `kilo.jsonc`, so no subfolder copy is needed), `.kilo/skills/git-worktree/SKILL.md` (§3), `docs/DECISIONS.md` (ADR-052), `docs/HANDOVER.md`
**Why:** A git config or credential file can hold a token in a URL, a credential helper or an extra HTTP header, and a `.env` file holds application secrets. The agent never needs to read any of them, but only the `read` tool was blocked before, and a nested app repository did not load the root config.
**Impact:** `read`, `grep`, `glob` and `list` deny `.env`, `.env.*` (except `.env.example`), `.git/config`, `*.git/config`, submodule configs, `.git-credentials`, `~/.gitconfig`, the XDG git config and credential stores, `.npmrc`, `*.pem`, `*.key`, `*.p12` and `id_rsa*`. `edit` denies the same secret files. The `$BASH_ENV` guard refuses any `bash -c` command whose text names a protected file, in every subfolder and every repository; `.env.example` and `process.env` stay allowed. `KILO_CONFIG` points at the root config so nested repositories inherit it without a copy. No application behaviour changes. A Kilo restart is needed for the new permission block; the shell guard is active as soon as the file is installed. Shell commands that merely mention `.env` (for example a commit message) are also refused by the guard.

## [2026-10-30] Redact credentials from every shell command's output
**Type:** Security
**Board:** BOARD-002 | **Branch:** chore/redact-credentials-from-every-shell-command
**Changed:** `AGENTS.md` (§B11 — a credential never reaches a transcript through a URL), `.devcontainer/kilo-redact.sh` (new), `.devcontainer/test-kilo-redact.sh` (new), `.devcontainer/devcontainer.json` (`remoteEnv.BASH_ENV`, install step in `postCreateCommand`), `docs/{ENVIRONMENT,STACK,RISKS,DECISIONS,PROJECT_STATE}.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-redact-credentials-from-shell-output.md`
**Why:** The machine's global git config carried a `url.https://<token>@github.com/.insteadOf` rewrite, so `git remote -v` printed the credential in plaintext and it reached an agent transcript. The rewrite is removed — the token now lives in `/home/node/.git-credentials` (mode `600`) behind git's credential helper — and a `sed` filter installed as the container's `$BASH_ENV` startup file now scrubs both output streams of every shell command.
**Impact:** No URL carries a credential, so no routine git command can disclose one. `$BASH_ENV` is used because Kilo Code runs shell tools as `/bin/bash -c` and Debian's `~/.bashrc` returns immediately for a non-interactive shell. Output with no credential is byte-identical, including binary output; the exit code, the stdout/stderr split and the output order are preserved. The filter needs a container rebuild or window reopen to activate. The token itself was printed once and must be rotated at GitHub.

## [2026-10-30] Multi-repo support in the board and the git tools
**Type:** Feature
**Board:** BOARD-003, BOARD-004 | **Branch:** feat/multi-repo-support-in-the-board, docs/multi-repo-rules-agent-and-documentation
**Changed:** `.kilo/repos.json` (new), `.kilo/scopes/{web,mobile,api}.md` (new), `.kilo/skills/board/scripts/board.py` (`Repos` column, `add-column`, `add --repos`, `set-field --field repos`, strict row parsing), `.kilo/skills/board/scripts/board_serve.py` (column list), `.kilo/skills/git-worktree/scripts/worktree.py` (`create --repo`, board-driven `cleanup`/`verify`, repo-wide `list`), `.kilo/skills/git-worktree/scripts/guard.py` (`sync`, `check-repos`, policy root follows the shell, sync writes into the shell's tree), `.kilo/policies/git-policy.json` (`.kilo/scopes/*.md` asks), `kilo.jsonc` (generated), `.kilo/skills/{board,git-worktree}/SKILL.md`, `AGENTS.md` (§A1 multi-repo, §A7 script table, §B1, §B3 `Repos` column, §B4 repo-aware worktrees, the control-repo subsection), `.kilo/agent/docs-writer.md` (repository-aware units), `README.md` (multi-repo section), `apps/{web,mobile,api}/AGENTS.md` (synced copies), `docs/{PROJECT_STRUCTURE,HANDOVER,DECISIONS,README}.md`, `docs/handover/{README,web,mobile,api}.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-multi-repo-support-in-the-board.md`
**Why:** An application that keeps its own git repository under `apps/` could not be worked in: nothing could name the repo a row belonged to, nothing could give that repo the same guard rails, and the rules and the documentation still described a single repository.
**Impact:** The board gains a `Repos` column, migrated by `board.py add-column` instead of a hand edit. `worktree.py create --repo <id>` creates the worktree in that repo and keeps the board in the control repo. `guard.py sync --repo <id>` copies the `.kilo/` slice, the scope rules and the permission map into the target repo; `guard.py check-repos` proves the map and the `apps/` layout agree. `guard.py check-policy` now reads and writes the policy and config of the tree the shell is in, so a builder in a worktree no longer rewrites the main checkout; `guard.py sync` does the same and no longer fails when the target is the control repo itself. `AGENTS.md` and the `docs-writer` agent describe the control repo, the work surfaces and the repo map, and the scope rules are canonical in `.kilo/scopes/<id>.md` with `apps/<id>/AGENTS.md` as their synced copies.

## [2026-10-30] A documentation agent owns the application memory map
**Type:** Feature
**Board:** BOARD-002 | **Branch:** feat/add-a-documentation-agent-that-writes
**Changed:** `.kilo/agent/docs-writer.md` (new), `.kilo/command/handover.md` (rewritten, now routed to `docs-writer`), `docs/handover/{README,web,mobile,api}.md` (new), `AGENTS.md` (§A7 agent table, §A10 doc table, §B1 doc table, §B2), `docs/{README,PROJECT_STRUCTURE,HANDOVER,DECISIONS}.md`, `README.md`, `docs/changelog/CHANGELOG.md`, `docs/changelog/2026-10-30-docs-writer-and-application-memory-map.md`
**Why:** The handover was one file written from memory of a system, and a reader could not tell which parts of the code were pure and which touched the outside world.
**Impact:** `/handover` now runs the `docs-writer` agent, which reads the whole codebase on its first run in a session and writes one memory map per application under `docs/handover/` plus a global index. Every module is marked pure, reactive or effectful, and every claim carries a `file:line`. `docs/HANDOVER.md` stays as the factory's own handover. No behaviour change to the build, QA or merge lanes.

## [2026-10-30] One guard-rail policy, two enforcement layers
**Type:** Feature
**Board:** BOARD-001 | **Branch:** feat/add-a-permission-file-and-git
**Changed:** `.kilo/policies/git-policy.json` (new), `.kilo/skills/git-worktree/scripts/guard.py` (`check-git`, `check-policy`, `policy`), `kilo.jsonc` (generated `permission` map), `.kilo/skills/git-worktree/SKILL.md` (§3), `AGENTS.md` (§A7 table, §B9, §B11), `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `.kilo/command/{run,closeout}.md`, `docs/{PROJECT_STRUCTURE,HANDOVER,DECISIONS,PROJECT_STATE}.md`, `README.md`, `docs/changelog/CHANGELOG.md`
**Why:** The guard rails were prose in `AGENTS.md` and nothing stopped an agent from running `git push`, committing on `main`, or switching branches inside a worktree.
**Impact:** One policy file is the source of truth for the guard rails. The generated `permission` map in `kilo.jsonc` now denies the irreversible git commands (`git push`, `git reset --hard`, `git clean`, `git checkout --`, `git branch -D`, a raw `git worktree remove`, `git filter-branch`, `git filter-repo`, `git reflog expire`, `git gc`, `git update-ref -d`) and asks before the rest that changes history or the remote. `guard.py check-git` adds the three context checks a keyword list cannot make: no commit on `main`/`master`/`base`, no branch switch inside a worktree, and no raw `git worktree remove`. Edits to the rules files ask first; the real `.env` and key files are denied. `guard.py check-policy` proves the two layers still match.

## [2026-10-29] Starter: front page, no test residue, empty board
**Type:** Chore
**Board:** BOARD-013 | **Branch:** chore/starter-repo-prep
**Changed:** `README.md` (new), `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, `docs/changelog/CHANGELOG.md`, removed `artifacts/factory/qa/2026-10-29/BOARD-012/notes.md`, emptied `docs/BOARD.md`
**Why:** The repo is going public as a starter to plug into any project, so it needs a front page, no test residue, and a board that starts empty.
**Impact:** No behaviour change. A fresh clone has an empty board; the first row is added with `board.py add`. The handover and project state describe the starter, not a running project.

## [2026-10-29] One driver for the capture path, failures reported not routed around
**Type:** Chore
**Board:** BOARD-012 | **Branch:** chore/remove-cdp-and-report-failures
**Changed:** `.kilo/skills/qa-review/scripts/browser-review.mjs`, `AGENTS.md`, `.kilo/skills/qa-review/SKILL.md`, `.kilo/command/{ui,run}.md`, `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `docs/{UI-UX,STACK,HANDOVER,DECISIONS}.md`, `docs/changelog/CHANGELOG.md`
**Why:** The capture script advertised a CDP fallback it never had, and the incident behind the "ask before building a tool" rule was described with a protocol name instead of what actually happened.
**Impact:** The capture path drives Playwright only. `--chromium <path>` is a plain binary path handed to Playwright's launch, the resolution order is flag → env var → downloaded → system, and a missing chromium exits 2 with the searched list instead of being installed or replaced. A new rule makes an agent report a failed command, capture, or test instead of routing around it.

## [2026-10-29] One canonical artifacts folder, ask before building a tool
**Type:** Chore
**Board:** BOARD-010 | **Branch:** chore/one-artifacts-folder-and-ask-before
**Changed:** `.kilo/skills/qa-review/scripts/browser-review.mjs`, `.gitignore`, `AGENTS.md`, `docs/{UI-UX,HANDOVER,DECISIONS,PROJECT_STRUCTURE}.md`, `docs/changelog/CHANGELOG.md`, `.kilo/skills/qa-review/SKILL.md`, `.kilo/command/{ui,run}.md`, `.kilo/agent/{frontend-dev,backend-dev,mobile-dev,qa-reviewer,ui-critic}.md`, `apps/{web,mobile}/AGENTS.md`
**Why:** UI evidence was scattered across app folders, `docs/`, and `/tmp`, and an agent built a browser driver instead of asking, while Playwright was already installed globally.
**Impact:** All UI evidence lands under `artifacts/<scope>/qa/<date>/<task-id>/` in the main checkout; the capture script computes the path itself and writes `notes.md`. Review reports and ledgers stay in `docs/reviews/` — documents, not artifacts. A new rule makes an agent check for existing tooling and ask before building any.

## [2026-10-29] Live board viewer, bounded UI loop, gated UI tooling
**Type:** Feature
**Board:** BOARD-008, BOARD-009 | **Branch:** feat/live-board-viewer-html-dashboard-with
**Changed:** `.kilo/skills/board/scripts/board_serve.py` (new), `.kilo/skills/qa-review/scripts/{browser-review.mjs,check-finding.py,ledger.py}`, `.kilo/skills/board/scripts/board.py`, `.kilo/skills/git-worktree/scripts/worktree.py`, `.kilo/skills/{board,qa-review}/SKILL.md`, `.kilo/command/{board-view,run,ui}.md`, `.kilo/agent/{qa-reviewer,ui-critic}.md`, `kilo.jsonc` (Playwright MCP), `.devcontainer/devcontainer.json` (port 15180), `AGENTS.md`, `docs/{STACK,DECISIONS}.md`
**Why:** The markdown board is hard to scan, the UI critique → fix loop could run forever, and Playwright was installed but unreachable — so the agent built a browser driver by hand and looped proving it worked.
**Impact:** A read-only dashboard on port 15180 shows the lanes and the live worktrees. The QA loop is capped at 3 rounds with fingerprint dedupe and a ledger. The Playwright MCP is configured and the capture script resolves the global Playwright, so no hand-rolled browser client remains.
## [2026-11-11] OpenCode security adapter awaiting fixture access
**Type:** Feature
**Board:** BOARD-114 | **Branch:** feat/port-factory-harness-to-opencode-v2
**Changed:** `.opencode/plugins/factory-guard/`, canonical policy, guard file/search checks, config sync, STACK and session state
**Why:** Native search permissions do not enforce target paths; copied control repos need the complete runtime configuration
**Impact:** Incomplete security migration. Node tests exited 1 on temporary fixture directory EACCES; no workaround attempted. Container and native runtime verification remain pending.
