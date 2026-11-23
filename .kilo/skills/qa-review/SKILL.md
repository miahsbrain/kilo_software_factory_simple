---
name: qa-review
description: Verify a change against its acceptance criteria with Playwright, capture screenshot and console evidence, and file each finding as a board row. Use for the QA lane of any frontend or API change, or when the user says "QA review", "verify this", or "run QA".
---

# QA Review

Check the assigned behavior against observable acceptance criteria. Stay read-only against application source; approved navigation and evidence writes are permitted. Use focused checks and the original workspace, not a new review worktree. Report what passed and what remains unverified; capture completion alone is not a behavior pass.

## Capture

Use the documented development command from `docs/RUNNING.md` or `docs/STACK.md`. Run the existing capture tool with the assigned source repo/worktree as the current directory (use the tool's absolute path if it lives in the control repo):

```bash
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url <url> --route /path --scope <scope> --task-id <ID> --project <app-path>
```

It captures screenshots, console/page errors, network failures, and overflow at its configured mobile/tablet/desktop/wide viewports, including the 320px floor. Exit 0 means capture completed, even with errors; exit 2 means fatal/capture/authentication failure. Report the command, error, and exit code on failure; do not install tools or invent a substitute capture mechanism.

Use `--scheme light|dark|both`, `--component <selector>`, `--compare <dir>`, or `--label <slug>` when relevant. `--chromium <path>` selects an available approved browser. Keep raw captures unchanged in the caller's assigned Git top-level `artifacts/<scope>/qa/<date>/<ID>/`, including screenshots, components, comparisons, error logs, `summary.json`, and notes. Do not redirect worktree review evidence into control-main. Scope, date, task ID and label must be safe single path segments, not `.` or `..`. `--artifact-dir` is only an override within that same artifacts root; symlink roots/ancestors/destinations are refused before browser launch.

All newly generated review artifacts, images, reports, snapshots, network/console logs, and Playwright output belong under ignored `artifacts/` in the assigned repo/worktree, never the root, `/tmp`, or an external directory. Put newly generated ad-hoc review/Playwright scripts in `artifacts/scripts/`. Maintained review TOOL SOURCE remains tracked in `.kilo/skills/qa-review/`; bootstrap copies that source, never evidence. Legitimate canonical test fixtures may remain source, but generated fixture captures and test temporary directories use `artifacts/tmp/tests/` and are cleaned safely by the tests. Do not move or delete old project output without authorization. Never stage or commit artifacts.

Capture sets `TMPDIR`, `TMP`, and `TEMP` before loading/launching Playwright and restores them in `finally`. Their short relative paths resolve to the caller's `artifacts/tmp/browser-*/`, avoiding Chromium's Unix-socket pathname limit without external temp output; downloads and trace destinations are there too. Run from the assigned Git root to keep those paths short. It does not enable tracing or video. This confines the capture tool's configured and Playwright-managed output, not every Chromium/OS cache or crash artifact. Report any inaccessible browser-managed locations as a limitation rather than claiming universal filesystem enforcement.

Factory Playwright MCP uses the installed supported `--output-dir artifacts/playwright-mcp` flag for automatically named output, relative to the MCP runtime CWD. Start it in the assigned worktree. Explicit MCP filenames bypass that default and resolve from the workspace root: always supply `artifacts/...` filenames for screenshots, snapshots, network/console logs and other saves, checking the resolved workspace is the assignment. The flag is not a sandbox for arbitrary filenames or internal browser temp output. Do not invent a wrapper, add dependencies, or change permissions to imply otherwise.

Reports/findings/ledgers belong in ignored `artifacts/reviews/`. Run ledger commands from the assigned control source worktree; board coordination still resolves the shared control root, while evidence stays in the caller's Git root. `python3 .kilo/skills/qa-review/scripts/ledger.py status --task-id <ID>` prints that ledger path. An explicit override is `python3 .kilo/skills/qa-review/scripts/ledger.py --ledger-dir artifacts/reviews status --task-id <ID>`; outside-root and symlink overrides are refused.

## Authentication

Use authorized ignored local `--storage-state <file>` and/or `--navigation <file>`. Ask for test access when absent; MFA/SSO remains manual, never bypassed. Login/state capture requires navigation with `approved: true` and an app-specific `authenticatedSelector` visible after navigation. A matching URL or missing password form does not prove login.

Navigation supports `login` and `steps` arrays (up to 50 each), `authenticatedPath` for login, and actions `goto/path`, `fill/selector/env`, `click/selector/intent`, `waitForURL/path`, `waitForSelector/selector`. Page changes declare the final destination with `waitForURL`; paths stay same-origin without credentials/query/fragment. Click intents are `login`, `navigation`, or `destructive`; destructive actions also require explicit user authorization and `--allow-destructive`. Use environment-variable names for credentials, never literals. Inspect evidence for sensitive content before sharing; masking is not comprehensive.

## Review

Check the actual user flow, relevant loading/empty/error states, keyboard focus and names, contrast, tap targets, responsive layout, and unexpected console/network failures. Auth, script, API, data-loss, and security failures remain meaningful blockers. A missing favicon is nonblocking only when proven development-only and harmless; retain its raw evidence and rationale rather than filtering logs or excusing other errors.

Share one capture with `ui-critic` to review hierarchy, usability, and product character without source edits. Consolidate all findings once, deduplicate, and prioritize by user impact.

## Findings And Handoff

Actionable findings state `Summary`, `Repro steps`, `Expected behavior`, `Actual behavior`, `Evidence`, `Acceptance criteria`, and `Risk`. Validate persisted findings with:

```bash
python3 .kilo/skills/qa-review/scripts/check-finding.py --body-file artifacts/reviews/<finding.md> --kind bug --priority medium --category functional --route /path
```

Exit 0 accepts and prints a fingerprint; exit 66 means the finding needs better detail. The coordinator uses `board.py` for Fix rows and existing fingerprints for deduplication; reviewers report, not edit the board. Fixes reuse the original workspace and recheck affected criteria.

Use the existing `ledger.py` for QA/fix rounds when iterating: `next-round`, `finding`, `status`, and `stop` with `--task-id <ID>` (other required arguments via `--help`). It caps at three rounds; do not reset it or loop indefinitely. Escalate unresolved blockers with evidence and attempted fixes. Report pass only for proven criteria, not untested claims. Keep the final report concise: changed scope, actual checks/results, meaningful findings, and limitations.
