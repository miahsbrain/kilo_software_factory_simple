# Factory Handover

## Session Notes

BOARD124 extends bootstrap/restore only in assigned `.kilo/worktrees/restore-local-harness-and-bootstrap-service`, branch `chore/restore-local-harness-and-bootstrap-service`, shared with fixes BOARD125/126/127. The user separately authorized committing the reviewed factory implementation and preparing its shared human merge handoff. Bootstrap approval covers initial commits only in genuinely new repositories, plus fixture-only Git tests. Existing `/projects/kilo_inhouz_ai/project` and apps are untouched; no agent merge, push or install. Coordinator owns live-board updates.

ADR-085 records the approved tracked/local boundary: source/product docs and one `services.json` manifest survive cloning; harness/config/devcontainer/generated root instructions/live board are ignored. Arbitrary meaningful product-role kebab-case services occupy `apps/<name>`: frontend/backend variants, workers, cronjobs, no fixed slots/suffix enum. Ask unclear name and explicit separate/project ownership. Separate bootstrap creates one initial ignore-file commit; project bootstrap initial-commits only intended docs/manifest/ignore. Integrated creation never stages/commits control. Manifest registration changes in existing control await separate authorization.

Review the committed branch and focused test evidence. Handoff all four rows together only after clean lifecycle readiness verification; final commit ID/readiness are recorded on the live board. Historical BOARD122/123 approvals/results remain in the engineering log; ADR-085 supersedes only the relevant new-bootstrap no-commit/tracked-harness behavior. The real shared `.git/info/exclude` is untouched; staging includes only reviewed implementation files and the new template service manifest.

## Current Harness

Factory source tracks agreement, agents/commands/skills/policies, config, devcontainer and blank template board. Project/service copies are local ignored tooling. Tracked `services.json` records name/path/Git ownership; ignored `.kilo/repos.json` is generated control plus separate services only. No competing tracked repo map. Existing project/maps are not migrated.

For an app with an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Develop reusable components first using Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme; choices are not limited to installed libraries. Present the initial gallery and ask whether unslop is wanted. Run focused QA regardless, fix meaningful findings and recheck before composing screens from those components. Do not require another gallery for each screen. New applications and user-facing features present the frontend flow for user approval, using labeled fixtures where needed, before backend/APIs and integration. Backend-only maintenance needs no unrelated frontend work. UI critique and any requested general read-only unslop task run in parallel against shared evidence; consolidate meaningful findings once. A proven harmless development-only missing favicon is nonblocking, with raw evidence retained.

## Operations

- Board: coordinator uses `board.py` for the ignored main live board; viewer `board_serve.py --port 15180`.
- Workspaces: feature implementation uses assigned linked worktrees; explicit sharing via `create --board NEW --reuse EXISTING --repo ID` remains. Project-owned services use control's worktree, separate services their mapped worktree. Bootstrap creates the narrowly authorized initial commit; features wait for successful initialization/assignment. No saved-mode or permission changes.
- QA: existing capture/finding/ledger tools unchanged. No UI change or browser needed here.
- Bootstrap: factory-root `python3 .kilo/skills/git-worktree/scripts/bootstrap.py project [--destination <new-path>]`; control-root `python3 .kilo/skills/git-worktree/scripts/bootstrap.py app shop-frontend --git separate` or `app inventory-cron --git project`. New project/separate repos only: exactly one initial commit with empty index/unborn HEAD. Actual init/add/commit commands honor hard denials; only protected-branch/worktree context has the new-repo exception. Identity/hooks remain, no configuration invention/hook skipping. Preflight identity may stop before creation; late errors retain files/index for inspection, never delete/reinitialize.
- Restore: `python3 /path/to/factory/.kilo/skills/git-worktree/scripts/bootstrap.py restore --destination /path/to/project`. Restore control first, then clone separate services yourself at manifest paths and use `restore --destination /path/to/project/apps/shop-frontend --project /path/to/project`. Context required unless safely inferable from canonical placement. Missing checkouts reported; no network or fabricated remotes.
- Restore safety: all outputs and their tracked ancestors preflighted, differences/symlinks/unsafe paths refused before writes, missing restored and identical left. Clone-local excludes only, no source/ignore/index/HEAD/Git config changes, init/add/commit/install/build. App inherits control tooling and creates ignored local instructions/config/harness with relative control pointers, not an app map/board/devcontainer. Canonical placement reconciles existing lifecycle control-root discovery.
- Devcontainer: restore the control environment, open that container, then work under `apps/<name>`. App-only mounts cannot supply inherited control tooling and are not generated. The control directory retains Dockerfile/features/env/ports; generated post-create installs only the local shell guard, not factory global Git/doctor actions. No image build.

## Mechanics

`bootstrap.py` now owns `project(source, destination)`, `app(source, root, name, git_mode)` and `restore(source, destination, control=None)`. Only bootstrap implementation/tests and instructions/templates/docs change. Existing `worktree.py`, `guard.py`, `scope.py`, policies, permission configuration and sync behavior are unchanged. Routine sync still copies the four harness directories/config to controls; full clone reconstruction is the explicit factory restore command, including app local tooling where required.

## Testing

Focused command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_bootstrap` from `.kilo/skills/git-worktree/scripts`. First run: 12 tests in 2.475s, one test-expectation failure because argparse returns 2 for a dash-prefixed missing positional name. Removed that redundant case, kept other invalid names and expanded identity/hook/policy/preflight coverage. Final permitted rerun: 16 tests in 3.974s, all passed, exit 0. Temporary fixtures and isolated fixture identity only; no real-project Git/global config operations.

Coordinator subsequently ran all 17 tests successfully in 3.654s. Independent review found tracked-ancestor, external-target-policy and app-container-context gaps, recorded as BOARD125/126/127 in the original workspace. Repairs now reject tracked ancestors, honor both source and target hard policy denials, and use the portable control-only container contract. The complete current suite passed 19 tests in 4.727s; whitespace checks passed. Independent re-review confirmed all three findings resolved with no remaining blocker. No user-imposed test-run limit exists; earlier two-run wording described the builder assignment only.

## Limitations

Focused fixtures/file review only, no full lifecycle suite, build, install, UI capture or real-project runtime. Devcontainer files/config verified, not image-built. App-only container environments are unsupported; use control's environment. No hostile concurrent filesystem-race/disk-failure transaction guarantee. Differing local files need manual reconciliation; no force mode. Separate app clones outside registered control paths are refused for lifecycle discovery. Existing projects require an agreed migration; no registration auto-commit in existing control. Historical ADR/changelog entries remain history.

## Documents

See `PROJECT_STATE.md`, `PROJECT_STRUCTURE.md`, ADR-085 in `DECISIONS.md`, the README pair, `/bootstrap`, worktree skill and `changelog/CHANGELOG.md`. Product rules belong to independent products, not this factory.
