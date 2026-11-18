---
name: qa-review
description: Verify a change against its acceptance criteria with Playwright, capture screenshot and console evidence, and file each finding as a board row. Use for the QA lane of any frontend or API change, or when the user says "QA review", "verify this", or "run QA".
---

# QA Review

Check the assigned behavior against observable acceptance criteria. Stay read-only against application source; approved navigation and evidence writes are permitted. Use focused checks and the original workspace, not a new review worktree. Report what passed and what remains unverified; capture completion alone is not a behavior pass.

## Capture

Use the documented development command from `docs/RUNNING.md` or `docs/STACK.md`, then the existing capture tool:

```bash
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url <url> --route /path --scope <scope> --task-id <ID> --project <app-path>
```

It captures screenshots, console/page errors, network failures, and overflow at its configured mobile/tablet/desktop/wide viewports, including the 320px floor. Exit 0 means capture completed, even with errors; exit 2 means fatal/capture/authentication failure. Report the command, error, and exit code on failure; do not install tools or invent a substitute capture mechanism.

Use `--scheme light|dark|both`, `--component <selector>`, `--compare <dir>`, or `--label <slug>` when relevant. `--chromium <path>` selects an available approved browser. Keep the raw capture unchanged in the shared control-main `artifacts/<scope>/qa/<date>/<ID>/`, including `summary.json` and notes. Reports/findings/ledgers belong in ignored `artifacts/reviews/`; never stage or commit artifacts. `ledger.py status --task-id <ID>` prints the shared ledger path when needed.

## Authentication

Use authorized ignored local `--storage-state <file>` and/or `--navigation <file>`. Ask for test access when absent; MFA/SSO remains manual, never bypassed. Login/state capture requires navigation with `approved: true` and an app-specific `authenticatedSelector` visible after navigation. A matching URL or missing password form does not prove login.

Navigation supports `login` and `steps` arrays (up to 50 each), `authenticatedPath` for login, and actions `goto/path`, `fill/selector/env`, `click/selector/intent`, `waitForURL/path`, `waitForSelector/selector`. Page changes declare the final destination with `waitForURL`; paths stay same-origin without credentials/query/fragment. Click intents are `login`, `navigation`, or `destructive`; destructive actions also require explicit user authorization and `--allow-destructive`. Use environment-variable names for credentials, never literals. Inspect evidence for sensitive content before sharing; masking is not comprehensive.

## Review

Check the actual user flow, relevant loading/empty/error states, keyboard focus and names, contrast, tap targets, responsive layout, and unexpected console/network failures. Auth, script, API, data-loss, and security failures remain meaningful blockers. A missing favicon is nonblocking only when proven development-only and harmless; retain its raw evidence and rationale rather than filtering logs or excusing other errors.

Share one capture with `ui-critic` to review hierarchy, usability, and product character without source edits. Consolidate all findings once, deduplicate, and prioritize by user impact.

## Findings And Handoff

Actionable findings state `Summary`, `Repro steps`, `Expected behavior`, `Actual behavior`, `Evidence`, `Acceptance criteria`, and `Risk`. Validate persisted findings with:

```bash
python3 .kilo/skills/qa-review/scripts/check-finding.py --body-file <finding.md> --kind bug --priority medium --category functional --route /path
```

Exit 0 accepts and prints a fingerprint; exit 66 means the finding needs better detail. The coordinator uses `board.py` for Fix rows and existing fingerprints for deduplication; reviewers report, not edit the board. Fixes reuse the original workspace and recheck affected criteria.

Use the existing `ledger.py` for QA/fix rounds when iterating: `next-round`, `finding`, `status`, and `stop` with `--task-id <ID>` (other required arguments via `--help`). It caps at three rounds; do not reset it or loop indefinitely. Escalate unresolved blockers with evidence and attempted fixes. Report pass only for proven criteria, not untested claims. Keep the final report concise: changed scope, actual checks/results, meaningful findings, and limitations.
