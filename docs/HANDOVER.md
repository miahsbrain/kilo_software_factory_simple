# HANDOVER — software factory

> **Session Notes** (keep at the very top, updated every session)
> - **2026-11-16:** BOARD-103 and its fixes BOARD-104 through BOARD-112 share
>   `.kilo/worktrees/configurable-shared-workspace-lifecycle-and-authenticated`, branch
>   `feat/configurable-shared-workspace-lifecycle-and-authenticated`. Includes CLI lifecycle,
>   assigned scopes, authenticated review and `merge-conflict-resolver`; no product changes.
> - **Verification:** 31 disposable-repo lifecycle regressions and 19 browser regressions passed.
>   The 31-test result is builder evidence; final independent discovery ran zero tests. Auth was
>   independently verified with a real local login/navigation fixture across two viewports.
> - **Final lifecycle corrections:** directory-changing shell routing is rejected, and newly
>   created checkout maps are initialized from saved project mode. Final review found a blocking
>   inherited-map order comparison defect at `worktree.py:640-643`. BOARD-107 and parent BOARD-103
>   are Blocked at the three-round cap. Do not merge or enable this implementation.
> - **Permission hold:** the template BOARD edit remains denied in this session. Its narrow `ask`
>   exception is in the feature policy/generated config, not loaded session permissions. Live board
>   prose also retains old guidance; only script-owned row metadata has changed there.
> - **Next action:** obtain a human follow-up decision for order-sensitive inherited-map validation
>   and reload the task-worktree permissions before the template edit. Preserve this workspace and
>   local checkpoint commits. No fourth fix/review round is authorized.
> - **Next action:** finish corrected-state review, then reload Kilo from this worktree configuration
>   to apply the template correction. Local feature commits are authorized. Do not merge while the
>   row is blocked. No real workspace was merged/discarded and no actual mode was changed.
> - **Previous work:** BOARD-101 and BOARD-102 are Merged on the live factory board.

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
| `.kilo/skills/qa-review/scripts/ledger.py` | Opens, closes and reports the QA↔fix rounds of a row. |

## 4. Modules and functions

| Symbol | File | Responsibility | Kind |
|---|---|---|---|
| `board.py` | `.kilo/skills/board/scripts/board.py` | Deterministic manipulation of the markdown board. Never writes prose. | effectful (file I/O) |
| `board_serve.py` | `.kilo/skills/board/scripts/board_serve.py` | Serves the board and the live worktree state read-only, as a collapsible accordion dashboard with compact cards and persisted folds. | effectful (network, file I/O) |
| `worktree.py` | `.kilo/skills/git-worktree/scripts/worktree.py` | Creates the worktree for a board row, derives its name and branch, records it back on the row. | effectful (git, filesystem) |
| `guard.py` | `.kilo/skills/git-worktree/scripts/guard.py` | The guard rails and the sync that carries them into an app repository. | effectful (git, filesystem) |
| `check-finding.py` | `.kilo/skills/qa-review/scripts/check-finding.py` | Validates a finding and derives its fingerprint. | pure |
| `ledger.py` | `.kilo/skills/qa-review/scripts/ledger.py` | The round ledger of a row. | effectful (file I/O) |
| `browser-review.mjs` | `.kilo/skills/qa-review/scripts/browser-review.mjs` | Captures screenshots, console, page errors and network for a route. | effectful (browser, filesystem) |

### Lifecycle tooling inventory (2026-11-16)

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
Known blocker: inherited-map dictionary equality at
`.kilo/skills/git-worktree/scripts/worktree.py:640-643` ignores rule insertion order. A trailing
wildcard allow can override secret denies while passing equality. Reuse the existing ordered-items
validation in `.kilo/skills/git-worktree/scripts/guard.py:775-778` in an approved follow-up;
the current implementation is not safe to enable.

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
to the original chunk. Final independent discovery reported `Ran 0 tests in 0.000s`, so it does
not independently reproduce the 31 passes. Final source review found the inherited-map rule-order
blocker; BOARD-103 remains Blocked, not merge-ready.

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
- `templates/project/docs/BOARD.md` retains stale mandatory per-row worktree/manual Merged text:
  the session deny still applies after two attempts. A narrow template-only `ask` exception is
  included in the feature config but requires a reload before the edit. Never bypass it.
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
