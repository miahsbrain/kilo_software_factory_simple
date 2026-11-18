# Factory Handover

## BOARD129 Current

Final verification after guidance/documentation updates: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_bootstrap.py -v` passed all 24 tests in 4.858s (exit 0); `git diff --check` passed.

Independent read-only safety review found no actionable findings and independently passed `git diff --check`. The reviewer did not rerun the fixture suite. The user authorized committing this change and preparing a human merge handoff; it is not deployed to existing copied factories.

Implemented the approved factory guardrail in assigned `.kilo/worktrees/constrain-bootstrap-to-approved-working-directories`, branch `chore/constrain-bootstrap-to-approved-working-directories`. Commit the reviewed files, verify clean lifecycle readiness, and record the commit/readiness on BOARD-129 before human handoff. `project()` defaults to rejecting canonical destinations outside invoking factory CWD before writes/init/staging/commits, including direct calls. Project mode still requires CWD == source factory root; no fallback. Default local `project/` and custom internal destinations with existing parents work. Project-only `--allow-outside` supports intentional external creation only after actual user approval; the flag itself cannot prove approval. CWD/source/resolved destination print on stderr before creation without changing final stdout success. Existing path, traversal/symlink, policy, identity/hook checks remain.

Root/template agreement and README, active `/bootstrap` and `/run`, and worktree skill anchor mutation to approved resolved control/target roots. Stop mismatches; never derive sibling destinations from display/service names, enter siblings or reuse unrelated board/worktree paths without approval. No blanket lifecycle-helper CWD rule, source-resolver/worktree/policy/config changes. Restore retains explicit external clone targets without the flag; app/restore reject the flag. BOARD128 removal remains intact.

Initial focused command from this assigned workspace: `python3 -m unittest discover -s .kilo/skills/git-worktree/scripts -p test_bootstrap.py -v`, 24 tests passed in 4.978s, exit 0. Existing authorized fixture Git commits only; external policy/hook fixtures explicitly opt in individually. New tests prove default rejection leaves target parents and factory bytes (including index/HEAD metadata) unchanged, direct helper confinement, internal/approved-external success, project-only flag parsing, unchanged external restore, CWD and unsafe-path preflight.

No live external changes, migration, cleanup or install; no agent merge or push. Coordinator owns main live-board updates. The supplied diagnosis does not prove any historical automatic redirect; exact prior action remains unverified. This correction prevents unapproved external bootstrap by default, not all possible agent misuse. No full lifecycle, browser, build or image verification; concurrent filesystem races remain outside the existing preflight guarantee. ADR-088 records the decision. Earlier session/testing notes below describe BOARD128 history, not this task's authorization.

## Prior Session Notes

BOARD128 removes the unslop skill, command, bundled resources and active factory/template references in assigned `.kilo/worktrees/remove-unslop-from-factory-ui-workflows`, branch `chore/remove-unslop-from-factory-ui-workflows`. The user authorized committing the reviewed removal and preparing its human merge handoff. No agent merge, push, install or runtime changes. Existing `/projects/kilo_inhouz_ai/project` and apps are untouched; existing project copies are not migrated. Coordinator owns live-board updates.

ADR-085 records the approved tracked/local boundary: source/product docs and one `services.json` manifest survive cloning; harness/config/devcontainer/generated root instructions/live board are ignored. Arbitrary meaningful product-role kebab-case services occupy `apps/<name>`: frontend/backend variants, workers, cronjobs, no fixed slots/suffix enum. Ask unclear name and explicit separate/project ownership. Separate bootstrap creates one initial ignore-file commit; project bootstrap initial-commits only intended docs/manifest/ignore. Integrated creation never stages/commits control. Manifest registration changes in existing control await separate authorization.

Review the committed removal and generated human lifecycle handoff after clean readiness verification; commit ID/readiness are recorded on the live board. Independent final review found no correctness issues or active invocations, links or deleted-resource references in root guidance, agents, commands, skills or templates; final `git diff --check` passed. The template-board edit was initially denied, then corrected with explicit user approval for that file only; no permission configuration or live-board changes were made by the correction. ADR-087 supersedes earlier unslop-specific decisions; historical ADR/changelog and merged board rows remain unchanged.

## Current Harness

Factory source tracks agreement, agents/commands/skills/policies, config, devcontainer and blank template board. Project/service copies are local ignored tooling. Tracked `services.json` records name/path/Git ownership; ignored `.kilo/repos.json` is generated control plus separate services only. No competing tracked repo map. Existing project/maps are not migrated.

For an app with an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Develop reusable components first using Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme; choices are not limited to installed libraries. Present the initial gallery. Run focused QA, fix meaningful findings and recheck before composing screens from those components. Do not require another gallery for each screen. New applications and user-facing features present the frontend flow for user approval, using labeled fixtures where needed, before backend/APIs and integration. Backend-only maintenance needs no unrelated frontend work. Run UI critique against shared evidence; consolidate meaningful findings once. A proven harmless development-only missing favicon is nonblocking, with raw evidence retained.

## Operations

- Board: coordinator uses `board.py` for the ignored main live board; viewer `board_serve.py --port 15180`.
- Workspaces: feature implementation uses assigned linked worktrees; explicit sharing via `create --board NEW --reuse EXISTING --repo ID` remains. Project-owned services use control's worktree, separate services their mapped worktree. Bootstrap creates the narrowly authorized initial commit; features wait for successful initialization/assignment. No saved-mode or permission changes.
- QA: existing capture/finding/ledger tools unchanged. No UI change or browser needed here.
- Bootstrap: factory-root `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project [--destination <new-path>]`; control-root `python3 .kilo/skills/git-worktree/scripts/bootstrap.py app shop-frontend --git separate` or `app inventory-cron --git project`. New project/separate repos only: exactly one initial commit with empty index/unborn HEAD. Actual init/add/commit commands honor hard denials; only protected-branch/worktree context has the new-repo exception. Identity/hooks remain, no configuration invention/hook skipping. Preflight identity may stop before creation; late errors retain files/index for inspection, never delete/reinitialize.
- Restore: `python3 /path/to/factory/.kilo/skills/git-worktree/scripts/bootstrap.py restore --destination /path/to/project`. Restore control first, then clone separate services yourself at manifest paths and use `restore --destination /path/to/project/apps/shop-frontend --project /path/to/project`. Context required unless safely inferable from canonical placement. Missing checkouts reported; no network or fabricated remotes.
- Restore safety: all outputs and their tracked ancestors preflighted, differences/symlinks/unsafe paths refused before writes, missing restored and identical left. Clone-local excludes only, no source/ignore/index/HEAD/Git config changes, init/add/commit/install/build. App inherits control tooling and creates ignored local instructions/config/harness with relative control pointers, not an app map/board/devcontainer. Canonical placement reconciles existing lifecycle control-root discovery.
- Devcontainer: restore the control environment, open that container, then work under `apps/<name>`. App-only mounts cannot supply inherited control tooling and are not generated. The control directory retains Dockerfile/features/env/ports; generated post-create installs only the local shell guard, not factory global Git/doctor actions. No image build.

## Mechanics

BOARD128 changes instructions/docs and deletes resources only. Bootstrap, guard, worktree, sync, policies and permission configuration are unchanged. Generic harness copying naturally omits deleted sources for new copies; it does not remove old files from existing project copies. No replacement skill/checklist or relocated rules were introduced.

## Testing

BOARD128 `git diff --check` passed, exit 0. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_bootstrap` from `.kilo/skills/git-worktree/scripts` passed all 19 tests in 4.501s, exit 0. The suite validates generic harness copying/restore, not this removed skill directly. The final two active references in the blank template board were corrected with explicit user approval. The deleted inventory is 15 skill files (six WebP assets, two HTML examples, five reference Markdown files, skill and script) plus the command, 16 total. Empty skill directories were removed after guard approval; no replacement was introduced. Prior bootstrap test/review history remains in the engineering log.

## Limitations

Focused fixtures/file review only, no full lifecycle suite, build, install, UI capture or real-project runtime. Devcontainer files/config verified, not image-built. App-only container environments are unsupported; use control's environment. No hostile concurrent filesystem-race/disk-failure transaction guarantee. Differing local files need manual reconciliation; no force mode. Separate app clones outside registered control paths are refused for lifecycle discovery. Existing projects require an agreed migration; no registration auto-commit in existing control. Historical ADR/changelog entries remain history.

## Documents

See `PROJECT_STATE.md`, `PROJECT_STRUCTURE.md`, ADR-085/087 in `DECISIONS.md`, the README pair, `/bootstrap`, worktree skill and `changelog/CHANGELOG.md`. Product rules belong to independent products, not this factory.
