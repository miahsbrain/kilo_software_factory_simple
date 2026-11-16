# HANDOVER — software factory

> **Session Notes** (keep at the very top, updated every session)
> - **BOARD-113 policy correction:** Approved review-only relative/absolute write exceptions precede
>   protected-path denials. Task config regenerated; main config untouched. Active reviewer sessions
>   now permit normal reviewer report writes after the user's latest reload. The report and final
>   delta evidence were saved with `apply_patch`; no alternate write method was used.
>   Resolved nested SSH-key gap with approved `**/id_rsa*` denial beside existing `id_rsa*`.
>   Final independent permission regression passed: 1 test, both modes, 0.053s, exit 0; maps in sync.
>   Ledger/source review passed 6 tests in 0.107s, exit 0, with no blocking source findings.
> - **2026-11-16, BOARD-113:** Implemented approved shared ignored review storage in
>   `.kilo/worktrees/store-reviews-as-ignored-artifacts`, branch `chore/store-reviews-as-ignored-artifacts`.
>   Ledger defaults reuse control-root discovery; explicit directory overrides remain. Rules,
>   reviewer prompts and templates require contextual human escalation for round-three blockers,
>   not automatic blocking on success. BOARD-113 has no unresolved review or runtime-write blocker.
> - **Migration:** Four BOARD-102/103 reports/ledgers copied byte-for-byte from main to shared
>   `artifacts/reviews/`; main and feature originals were identical. Only feature originals removed.
>   Historical links inside evidence remain unchanged; resolve old `docs/reviews/<name>` references
>   to `artifacts/reviews/<name>`. BOARD-103's three rounds and stop reason remain intact.
> - **Next action:** review and merge the clean BOARD-113 branch through the human lifecycle CLI.
>   The report is shared ignored `artifacts/reviews/BOARD-113-review.md`. The user's reason text
>   and SSH-denial order are preserved; review allows were normalized with explicit approval.
>   Focused verification is recorded in §10 below. No agent merge or cleanup was performed.
>   The shared Git exclude `.kilo/` hides the new test from normal status; the orchestrator must
>   explicitly include only `test_ledger.py` when staging, never ignored artifacts. Excludes unchanged.
> - **Previous work:** the human resolved conflicts and committed lifecycle/authenticated review
>   on main at `d5ace2f`, including feature commit `44ca90b`. BOARD-103 through BOARD-112 are now
>   Merged; their old worktree remains pending human cleanup. BOARD-101/102 are also Merged.
>   The historical capped review and subsequent authorized follow-up remain preserved in artifacts
>   and the engineering log. This change does not reopen those rounds or modify lifecycle/auth code.

## 1. Overview

- **What it is:** the software factory — a written rule set, a live work board, specialised
  builder and reviewer agents, and a loop that carries every task from decision to merged branch.
  There is no application runtime here.
- **Who uses it:** one human owner and the Kilo Code agents that act for them. The owner approves
  decisions and merges branches; agents build and review in the assigned workspace set.
- **Tech stack:** Markdown rules plus the Kilo Code agent and command system (`.kilo/agent/`,
  `.kilo/command/`) running on git worktrees. Python 3.9+ standard library for the scripts.
  Details in `docs/STACK.md`.
- **How to use it:** open the factory in Kilo Code. Read `AGENTS.md` at the root. Run `/board` to
  see the live board, `/decide` to approve a decision, `/run` to build in the assigned workspace, `/ui`
  for the QA lane, `/closeout` to refresh docs, `/handover` to refresh the application memory map.

## 2. Directory map

| Path | Contents |
|---|---|
| `AGENTS.md` | Root rules for the architect, orchestrator, and every builder (Part A, Part B). |
| `README.md` | The front page: what the factory is, how to point it at a project, quick start. |
| `.kilo/agent/` | Seven specialists: `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`, `merge-conflict-resolver`. |
| `.kilo/command/` | The eight slash commands: `decide`, `board`, `board-view`, `run`, `components`, `ui`, `handover`, `closeout`. |
| `.kilo/policies/` | The canonical guard-rail policy: `git-policy.json`. |
| `.kilo/repos.json` | The repo map of this repository. The only way into a repository. |
| `.kilo/scopes/` | Canonical specialization rules; generated ignored pointers expose them to assigned work surfaces. |
| `.kilo/skills/` | The three skills with their scripts: `board`, `git-worktree`, `qa-review`. |
| `.kilo/worktrees/` | Original repo-specific workspace set reused by all lanes and finding rows. Git-ignored. Optional mode also permits assigned nonprotected current checkouts. |
| `.devcontainer/` | Container definition: `Dockerfile`, `devcontainer.json`, the redaction script. |
| `docs/` | The factory's own governance set. Product documentation lives in the project repository. |
| `artifacts/reviews/` | Ignored reports, findings and round ledgers in the control main checkout, shared by worktrees. Never stage or commit. |
| `.kilo/scopes/service.md` | The default scope rules for a work surface with no scope file of its own. A work surface carries a pointer to this file, never a copy of it. |
| `templates/project/` | The blank project skeleton a new project starts from. |
| `project/` | A project repository in this workspace. Its own git repository. Never tracked here. |

## 3. Entry points

| Entry point | What it does |
|---|---|
| `AGENTS.md` | The rule set, read by every agent at the start of a task. |
| `.kilo/command/*.md` | Slash commands that package the workflow. |
| `.kilo/skills/board/scripts/board.py` | The board's only writer. `show`, `add`, `set-status`, `set-field`, `note`, `remove`, `lanes`, `add-column`. |
| `.kilo/skills/board/scripts/board_serve.py` | The read-only board viewer on port 15180. Vertical accordion of collapsible lanes, compact cards that expand to their detail, folds remembered in the browser. |
| `.kilo/skills/git-worktree/scripts/worktree.py` | Creates/reuses workspaces; `mode required\|optional\|status`, `handoff`, `merge`, `discard`, `list`, `verify`, `cleanup`. Merge/discard/cleanup preview by default; applying them is a human CLI operation. |
| `.kilo/skills/git-worktree/scripts/guard.py` | The guard rails: `check-git`, `check-policy`, `check-delete`, `check-worktree`, `check-repos`, `sync` (one repo or `--all`). |
| `.kilo/skills/git-worktree/scripts/scope.py` | The generated pointer a work surface carries, and the local exclude rule that keeps it out of every commit. |
| `.kilo/skills/qa-review/scripts/browser-review.mjs` | The only UI capture path. Supports ignored local storage state/approved navigation; destructive actions require explicit approval. |
| `.kilo/agent/merge-conflict-resolver.md:1` | Specialist for existing conflicted merges; assigned edits/checks only, no commit/merge/abort/reset/rebase/push/discard. |
| `.kilo/skills/qa-review/scripts/check-finding.py` | Validates a QA finding and prints its fingerprint. |
| `.kilo/skills/qa-review/scripts/ledger.py` | Reports/updates QA↔fix rounds; defaults to shared control-root `artifacts/reviews/`; `--ledger-dir` before subcommand overrides it. |

## 4. Modules and functions

| Symbol | File | Responsibility | Kind |
|---|---|---|---|
| `board.py` | `.kilo/skills/board/scripts/board.py` | Deterministic manipulation of the markdown board. Never writes prose. | effectful (file I/O) |
| `board_serve.py` | `.kilo/skills/board/scripts/board_serve.py` | Serves the board and the live worktree state read-only, as a collapsible accordion dashboard with compact cards and persisted folds. | effectful (network, file I/O) |
| `worktree.py` | `.kilo/skills/git-worktree/scripts/worktree.py` | Creates the worktree for a board row, derives its name and branch, records it back on the row. | effectful (git, filesystem) |
| `guard.py` | `.kilo/skills/git-worktree/scripts/guard.py` | The guard rails and the sync that carries them into an app repository. | effectful (git, filesystem) |
| `check-finding.py` | `.kilo/skills/qa-review/scripts/check-finding.py` | Validates a finding and derives its fingerprint. | pure |
| `default_ledger_dir(cwd)` | `.kilo/skills/qa-review/scripts/ledger.py:37` | Imports and reuses `worktree.control_root(cwd)`; validates board/map presence, returns shared ignored directory, refuses unknown roots. | effectful (Git, filesystem) |
| `ledger_path(ledger_dir, task_id)` | `.kilo/skills/qa-review/scripts/ledger.py:33` | Computes the existing ledger filename within the chosen directory. | pure |
| `read_ledger(path)` | `.kilo/skills/qa-review/scripts/ledger.py:80` | Missing files are empty; other read errors refuse instead of resetting history. | effectful (file I/O) |
| `cmd_next_round(args)` | `.kilo/skills/qa-review/scripts/ledger.py:135` | Opens rounds 1–3; refuses round 4 without writes and explains conditional escalation. | effectful (file I/O, output) |
| `main(argv)` | `.kilo/skills/qa-review/scripts/ledger.py:213` | Resolves default directory only without override; dispatches existing commands, reports root/I/O failures clearly. | effectful (Git, filesystem, output) |
| `browser-review.mjs` | `.kilo/skills/qa-review/scripts/browser-review.mjs` | Captures screenshots, console, page errors and network for a route. | effectful (browser, filesystem) |

### Lifecycle tooling inventory (2026-11-16)

`.kilo/skills/git-worktree/scripts/guard.py:758` exposes pure
`permission_maps_match(current, expected)`, extracted from the existing `cmd_check_policy()`
ordered-items comparison. It checks tool-key membership and each nested rule's insertion order;
both `cmd_check_policy()` and `cmd_create()` use it with the existing generated permission map.
Reordered inherited maps fail closed without rewriting them: the new checkout/branch and journaled
initialization error survive, and the board stays unchanged. The two new lifecycle test methods
cover reordered `edit`, `bash` and `read` rules and ordered inherited app maps in both modes,
with no app-local config. All test mutations are confined to disposable standard-temp fixtures.

In `.kilo/skills/git-worktree/scripts/worktree.py`, `checked_git()` fails closed on command
errors; `confined()` rejects path escapes and symlink components; `local_state()` atomically
reads/writes `.git/kilo-workspace.json` in the control repository's common Git directory.
`workspace_mode()` reads that project-local mode and `cmd_mode()` regenerates canonical,
linked and existing mapped/inherited configurations from the control policy through the
existing guard generator. It preflights every effective map, restores prior map contents on
write failure, and saves mode only after the maps are written. Missing/malformed effective
configuration or an external `KILO_CONFIG` override is refused. These functions are effectful.

`load_guard_policy(root)` at `.kilo/skills/git-worktree/scripts/worktree.py:122` extracts the
existing mode policy loader for reuse by creation; it validates the control policy (effectful).
`cmd_create()` at `.kilo/skills/git-worktree/scripts/worktree.py:519` uses the existing generator
to initialize only the new checkout's local `kilo.jsonc` from saved project mode before success.
Inherited maps must already match; base/canonical configs remain unchanged. App checkouts
without a local config retain inheritance and generated scope pointers, not a copied harness.
Invalid initialization preserves the created branch/worktree, records the error locally,
reports incomplete creation, and leaves the board unchanged for human recovery.
The authorized follow-up resolves the former inherited-map order blocker by calling
`permission_maps_match(current, expected)` at `.kilo/skills/git-worktree/scripts/worktree.py:642`.
Independent proof: 33 tests passed, including six reordered-rule cases and two ordered success
cases at `.kilo/skills/git-worktree/scripts/test_lifecycle.py:246-300`. The template hold is resolved.

`lifecycle_selection()` resolves board rows and mapped repo IDs; `validate_workspace()`
checks registered linked workspaces, branches, confinement and locks; `require_clean()` allows
only `docs/BOARD.md` dirt in the control checkout. `related_rows()` and
`update_lifecycle_board()` use the existing board parser/writer, never manual table replacement.
`cmd_lifecycle()` sequences preflight, merge/discard, cleanup and journal updates.
`require_committed_merge()` checks named-target ancestry, cleanliness and absence of
`MERGE_HEAD` before cleanup. These functions are effectful. Board association uses branch
and recorded board identities, and terminal historical rows do not adopt reused-path outcomes.
`cmd_verify()` uses the saved original base unless `--base` overrides it.

The guard's `generated_permission(policy, mode="required")` is pure;
`write_permission_map()` supports non-writing preview and atomic file replacement.
`git_commands()` resolves separated, attached, empty and repeated relative `-C` arguments,
refuses unsupported directory routing and missing values, and passes actual destinations
to the effectful `context_verdict()`. Protected-branch commits remain denied in both modes.
Directory-changing chains (`cd`, `pushd`, `popd`, wrapper/subshell routing and shell evaluation)
are refused rather than interpreted; supported direct Git `-C` forms remain available.

Human CLI examples, from the project root:

```sh
python3 .kilo/skills/git-worktree/scripts/worktree.py mode status
python3 .kilo/skills/git-worktree/scripts/worktree.py mode optional
python3 .kilo/skills/git-worktree/scripts/worktree.py create --board BOARD-002 --reuse BOARD-001 --repo api
python3 .kilo/skills/git-worktree/scripts/worktree.py handoff --board BOARD-001
python3 .kilo/skills/git-worktree/scripts/worktree.py merge --board BOARD-001 --board BOARD-002
python3 .kilo/skills/git-worktree/scripts/worktree.py merge --board BOARD-001 --apply
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board BOARD-001 --repo api
python3 .kilo/skills/git-worktree/scripts/worktree.py discard --board BOARD-001 --repo api --apply --discard
```

`--repo` can repeat and disambiguates identical slugs; omitted means all row repositories.
`--target` overrides the saved base, otherwise each repository uses its own resolved base.
Fix rows reuse their single parent's workspace automatically, or use explicit `--reuse`.
Merge requires every related row to be review-ready and every selected source/target clean,
with commits ahead of target. The target branch must already be checked out.

Multi-repository merges are not atomic. A failure halts the batch and records the error and
completed work locally; conflicted and unprocessed workspaces remain. Resolve a conflict in
the affected target and have the human commit the existing merge before retrying. Recovery
requires the exact saved source/target identity and merge parents; unrelated subsequent
commits are refused. Interrupted post-merge cleanup can resume with the same command.
Merge explicitly requests a commit and independently proves it before deleting anything.
A row becomes Merged or Dropped only after all its entries have that outcome.
No command untracks the board or board writer. A preview does not change the journal or board.

### Authenticated Review And Assigned Scopes

Agent specialization is not a fixed folder boundary. Prompts assign mapped repos/paths and permit
local rules/shared governance reads explicitly. All lanes use the original paths; new reviewer
sessions do not create new worktrees. Optional mode changes workspace requirements, not scope.

The effectful `browser-review.mjs` entrypoint accepts `--storage-state <ignored-local.json>` and
`--navigation <ignored-local.json>`. Navigation requires `approved:true`, uses `login`,
`authenticatedPath`, `authenticatedSelector`, `steps`, and accepts goto/fill-from-env/click-with-intent/waitForURL/
waitForSelector. Login or storage state requires a visible application-specific authenticated marker;
page-changing navigation declares its final URL with waitForURL. See the QA skill for the exact schema.
Login needs authenticatedPath; same-origin
URLs forbid credentials/query/fragment. Only explicit user approval permits destructive actions
with `--allow-destructive`. Ask for test access; MFA/SSO is manual user login, never bypassed.
Known credentials/session values are masked, not arbitrary sensitive content. Inspect evidence
before sharing; all viewport/count/accessibility checks remain. No new dependency or auth service.

| Symbol | Source | Responsibility | Kind |
|---|---|---|---|
| `safeUrl`, `validateNavigation` | `.kilo/skills/qa-review/scripts/browser-review.mjs:234-279` | Validate same-origin paths, approved actions and explicit auth/final-route proof. | pure |
| `stateSecrets`, `redact` | `.kilo/skills/qa-review/scripts/browser-review.mjs:337-351` | Extract session values for masking and redact known sensitive strings. | pure |
| `localJson` | `.kilo/skills/qa-review/scripts/browser-review.mjs:280-304` | Load only confined ignored local state/navigation JSON. | effectful |
| `runSteps`, `proveAuthentication` | `.kilo/skills/qa-review/scripts/browser-review.mjs:306-335` | Apply authorized browser actions and prove the visible ready marker. | effectful |
| `PlaywrightPage`, `captureEntry` | `.kilo/skills/qa-review/scripts/browser-review.mjs:543`, `.kilo/skills/qa-review/scripts/browser-review.mjs:724` | Reuse the browser session and write sanitized per-viewport evidence. | effectful |

Conflict resolution uses base/ours/theirs and both branch intents in the existing conflicted
checkout, preserving unrelated changes. The specialist reports exact staged/unstaged files and
smallest-check evidence. Human reviews/completes the merge, then reruns the lifecycle command.

## 5. Data

| Artefact | Where | What it holds |
|---|---|---|
| The board | `docs/BOARD.md` | One row per unit of factory work. The only state. |
| The decisions | `docs/DECISIONS.md` | Append-only ADR table, ADR-001 onward. |
| The changelog | `docs/changelog/CHANGELOG.md` | The engineering log, newest first, one section per change. |
| The repo map | `.kilo/repos.json` | Repo id → path, relative to this repository's root. |
| The policy | `.kilo/policies/git-policy.json` | The guard-rail rules. The source of the generated permission map. |

## 6. States and state transitions

The board's lanes are the state machine of the factory:
`Backlog` → `Ready` → `In Progress` → `In Review` → `Pending Merge` → `Merged`, plus `Blocked`
and `Dropped`. Unresolved findings block handoff; verified shared parent/Fix rows may reach
`Pending Merge` together. The QA↔fix loop is capped at three rounds. Full rules in `AGENTS.md` §B4.

## 7. Public interfaces

The factory exposes no network API. Its public surface is the file layout above and the CLI of
the three scripts.

## 8. Configuration and environment

See `docs/ENVIRONMENT.md`. Names only, never values.

## 9. Dependencies

| Dependency | Why |
|---|---|
| Python 3.9+ standard library | Every script. No third-party package. |
| Playwright (global install in the dev container) | The QA capture path. |
| Chromium (`/usr/bin/chromium`) | The QA capture path. |
| Git | Worktrees, branches, the guard rails. |

## 10. Testing

BOARD-113 ledger regressions use disposable temp repositories and ledgers only:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/qa-review/scripts -p test_ledger.py -v
```

2026-11-16: builder **6 tests passed in 0.129s, exit 0**; independent reviewer reproduced
**6 tests in 0.107s, exit 0** with no blocking findings.
`.kilo/skills/qa-review/scripts/test_ledger.py:15` covers main/linked/nested shared control-root
resolution, ignored report paths, round 1–3 and immutable fourth-round refusal, contextual
escalation without false successful-cap blocking, absolute/relative overrides, unknown roots,
read failures and byte-preserving migrated capped history. No real ledger was mutated by tests.
Migration used existing `cp -n -p` and `cmp`: main/feature versions of the four BOARD-102/103
files were identical and shared copies matched byte-for-byte before feature originals were removed.
No browser, full lifecycle/auth suite or production build was run for BOARD-113. A separate
permission regression passed independently on the final delta with **1 test in 0.053s, exit 0**:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -k review_artifact -v
```

It checks relative/absolute review access, ordered secret/live-board denials, source restrictions
in both modes and generated-map consistency. Normal reviewer file-tool writes succeeded after the
latest reload, including the final delta report update. Earlier failed writes remain in history;
they were not bypassed. The reviewed policy delta changes reasons and equivalent SSH-denial order.

Lifecycle stdlib regression tests use only disposable repositories in Python's default
temporary directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_lifecycle.py -v
```

2026-11-16 final-correction result: 31 tests passed in 12.054s, exit 0, on one focused suite
run. New regressions cover unsupported directory chains, both saved-mode/base-map directions,
app inheritance/pointers and existing local maps, unchanged base configs, and failed creation
preserving its partial workspace and board bytes. Prior coverage includes attached/repeated `-C`, no-commit merge options,
uncommitted zero-exit merge refusal, human-completed conflict retry and unrelated-commit
rejection, control/linked/app mode transitions, malformed maps and write rollback, historical
board integrity, and saved-base verification. Printed injected cleanup/unfinished-merge
failures are expected passing test cases. No actual mode or permission-map regeneration was
performed on actual repositories in this correction; earlier permission regeneration belongs
to the original chunk. That round's independent discovery reported `Ran 0 tests in 0.000s` and
provided no pass. The subsequently authorized BOARD-107 follow-up supersedes that evidence:
absolute-path discovery in the correct workspace ran 33 tests in 14.190s, `OK`, exit 0, and
independent current-source review found no blocking issue. The final template alignment is
documentation only; verification is limited to file review and `git diff --check` for that change.

Authenticated capture regressions:

```sh
node --test .kilo/skills/qa-review/scripts/browser-review.test.mjs
```

2026-11-16: 19 tests passed, including the canonical capture script against a temporary local HTTP
fixture. It proves one login, a protected password-settings page, shared cookies/session storage
across two viewports, and PNG artifact creation. It does not prove external SSO/MFA or real accounts.

The verification of other changes is the smallest relevant script run, recorded with
its result and a `file:line` proof (AGENTS.md §B4 "Verification cost rule"). The dev container
ships `.devcontainer/test-kilo-redact.sh`, which checks the redaction startup file.

## 11. Known issues and risks

- The factory has no remote, so the harness cannot be shared yet. The user decides where it goes.
- A project copies the harness by hand, so a factory change does not reach the project
  automatically (ADR-054). The copy is deliberate: the project owns its copy from then on.
- Multi-repo merge is non-atomic; preserve partial outcomes and rerun only after human conflict
  completion/review. Discard is irreversible for uncommitted content and needs explicit loss approval.
- Required-mode edit permissions may block resolution in a preexisting conflicted target outside
  linked worktrees. Do not bypass the guard; request an approved assignment/permission decision.
- Lifecycle handoff/merge/discard currently validate linked mapped worktrees; optional current
  checkout edits/commits do not imply those commands accept a nonlinked source checkout.
- BOARD-113's generated task configuration allows only shared review evidence outside required-mode
  source worktrees, preserving later secret/board denies. Normal report writes now succeed; main
  config was not changed by the agents. Reports are ignored local evidence, so Git does not back
  them up. Nested separate-app control-root discovery was source-reviewed, not fixture-tested.
- Live `docs/BOARD.md` prose still describes the old workflow. Row updates remain script-managed;
  root rules and lifecycle CLI are authoritative. No direct live-board prose edit was attempted.
- Authenticated captures may contain sensitive page content beyond known credentials/session masks.

## 12. Open questions

- Where the factory repository is published, and where the project repository is pushed.
- When the owner chooses to copy this factory harness into a project. Factory updates do not
  propagate automatically; `guard.py sync` refreshes work-surface pointers, not project harnesses.

## 13. Document map

- `AGENTS.md` — the rules.
- `docs/PROJECT_STRUCTURE.md` — the layout.
- `docs/BOARD.md` — the factory's live board.
- `docs/DECISIONS.md` — the factory's decisions.
- `docs/STACK.md` — the tools and commands.
- `docs/ENVIRONMENT.md` — the environment variables.
- `docs/PROJECT_STATE.md` — where the work stands.
- `docs/changelog/` — the engineering log.
- `templates/project/` — the blank project skeleton.
