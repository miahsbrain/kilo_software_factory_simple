---
name: qa-review
description: Verify feature acceptance criteria, capture QA evidence, and hand over a manual QA checklist when access is blocked or a user requests a test guide for a board or feature.
---

# QA Review

Check the assigned behavior against observable acceptance criteria. Stay read-only against application source; approved navigation and evidence writes are permitted. Use focused checks and the original workspace, not a new review worktree. Report what passed and what remains unverified; capture completion alone is not a behavior pass.

## Manual checklist

At completion, write and link the guide for every skipped QA or UI scope, even when nothing is blocked. Name the skipped scope and reason. For skipped critique include the relevant visual hierarchy, usability, accessibility and responsive checks; do not present them as observed results.

If QA or UI critique cannot verify a criterion (for example, a redirect to an external identity provider, an unavailable service, or a missing device), keep the safe results already obtained and **write the manual guide before handing off**. Do not bypass the restriction or repeatedly retry it. Also produce a guide whenever the user asks for a QA checklist by board ID, feature name, or set of rows, even if automated QA succeeded. A checklist-only request needs no browser run, implementation or board transition.

1. Resolve the requested rows from the shared board. Match feature names to their IDs; ask only if the match is ambiguous. For a whole board, list the included IDs, group checks by feature and identify dropped or not-yet-implemented items separately. Use board criteria, the actual implementation or diff, documented run commands and prior evidence. Describe what changed in user terms; distinguish planned behavior from delivered behavior.
2. Give the tester the service/environment, revision (including uncommitted changes if relevant), start command and test role/data needed. Link directly to **each changed page**, using the known scheme, host, port and route from the assigned deployment or local run configuration. For redirects give the safe starting link, the expected destination and the visible sign of success. Never publish signed URLs, callback codes, secrets, personal IDs or passwords. If an origin or fixture ID is unknown or sensitive, say so and give a concrete way to obtain the URL from a known safe entry page; do not invent it. For non-UI changes use an exact safe command and working directory instead.
3. Write compact Markdown in the assigned repo's ignored `artifacts/reviews/<board-id>-manual-qa.md` (safe feature slug for a multi-row guide). Verify the destination is untracked, ignored, within the assigned artifacts root and free of symlinks. Reuse a matching guide for the same revision; preserve a tester's notes/results when generating a newer version. Link the actual file in the response, including the worktree path when relevant. If writing is unavailable, supply the guide inline and state why no file exists.

```markdown
## <BOARD-ID>: <feature>
Changed: <one sentence about the observable change>.

Setup: <direct safe URL or command; include prerequisites only if needed>.
- [ ] <Do one action>. Check that <observable result>.
- [ ] <Try the relevant failure or recovery action>. Check that <expected result>.
```

Use this format in the artifact and any inline handover. Follow ASD-STE100 plain-writing principles: short imperative sentences, consistent terms, and one test per checkbox. Use a literal `- [ ]` for each pending check, not paragraphs, tables, or approval recommendations. If blocked, give one `Blocked:` line before the checks. Do not ask the tester to repeat accepted checks. Keep non-testable items in a short scope note. Do not check a box on the strength of automated evidence. Do not ask the human to perform destructive operations on real data. Generating a checklist is not approval or a lane change.

**Required before delivery:** Run `python3 .kilo/skills/qa-review/scripts/check-finding.py --manual-guide --body-file artifacts/reviews/<guide>.md` on every new guide (use the installed control script path if needed). For inline output, pass the exact guide on stdin with `--body-file -`. Fix validation errors and recheck before linking or posting. Keep a tester's completed copy intact; for a new revision validate a fresh guide containing only outstanding checks. A successful format check does not verify product behavior.

## Capture

Before delegating and again in the specialist, run `python3 .kilo/skills/git-worktree/scripts/worktree.py reviews status` from the assigned Git root (use the inherited script's absolute path if needed). Read the returned `qa` and `ui` booleans; both default to true. A failed command or invalid policy means both scopes are manual, not permission to assume defaults. Do not change settings to run a review.

| `qa` | `ui` | Automatic work |
| --- | --- | --- |
| true | true | Run relevant QA; share its evidence with the critic. |
| true | false | Run relevant QA only. |
| false | true | Skip QA and fresh capture; critique existing evidence only. Hand off uncovered criteria. |
| false | false | Skip both; hand off the manual checklist. |

Normal code tests are independent of these switches. A user explicitly requesting a browser capture authorizes one manual runner invocation with `--human-requested-manual-capture`, not a policy change or an automatic review. A checklist, review, or implementation request alone is not a request for manual capture.

Use the documented development command from `docs/RUNNING.md` or `docs/STACK.md`. Run the existing capture tool with the assigned source repo/worktree as the current directory (use the tool's absolute path if it lives in the control repo):

```bash
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url <url> --route /path --scope <scope> --task-id <ID> --project <app-path>
```

It captures screenshots, console/page errors, network failures, and overflow at its configured mobile/tablet/desktop/wide viewports, including the 320px floor. Exit 0 means capture completed, even with errors; exit 2 means fatal/capture/authentication failure. Report the command, error, and exit code on failure; do not install tools or invent a substitute capture mechanism.

Use `--scheme light|dark|both`, `--component <selector>`, `--compare <dir>`, or `--label <slug>` when relevant. `--chromium <path>` selects an available approved browser. Keep raw captures unchanged in the caller's assigned Git top-level `artifacts/<scope>/qa/<date>/<ID>/`, including screenshots, components, comparisons, error logs, `summary.json`, and notes. Do not redirect worktree review evidence into control-main. Scope, date, task ID and label must be safe single path segments, not `.` or `..`. `--artifact-dir` is only an override within that same artifacts root; symlink roots/ancestors/destinations are refused before browser launch.

All newly generated review artifacts, images, reports, snapshots, network/console logs, and Playwright output belong under ignored `artifacts/` in the assigned repo/worktree, never the root, `/tmp`, or an external directory. Non-capture scratch scripts belong in `artifacts/scripts/`. Maintained review tool source remains tracked in `.kilo/skills/qa-review/`; bootstrap copies that source, never evidence. Legitimate canonical test fixtures may remain source, but generated fixture captures and test temporary directories use `artifacts/tmp/tests/` and are cleaned safely by the tests. Do not move or delete old project output without authorization. Never stage or commit artifacts.

Capture sets `TMPDIR`, `TMP`, and `TEMP` before loading/launching Playwright and restores them in `finally`. Their short relative paths resolve to the caller's `artifacts/tmp/browser-*/`, avoiding Chromium's Unix-socket pathname limit without external temp output; downloads and trace destinations are there too. Run from the assigned Git root to keep those paths short. It does not enable tracing or video. This confines the capture tool's configured and Playwright-managed output, not every Chromium/OS cache or crash artifact. Report any inaccessible browser-managed locations as a limitation rather than claiming universal filesystem enforcement.

Factory Playwright MCP is disabled by default. For saved browser evidence use only the existing runner from the assigned Git root; do not enable MCP, use alternate browser save tools or write ad-hoc capture scripts as a workaround.

Reports/findings/ledgers belong in ignored `artifacts/reviews/`. Run ledger commands from the assigned control source worktree; board coordination still resolves the shared control root, while evidence stays in the caller's Git root. `python3 .kilo/skills/qa-review/scripts/ledger.py status --task-id <ID>` prints that ledger path. An explicit override is `python3 .kilo/skills/qa-review/scripts/ledger.py --ledger-dir artifacts/reviews status --task-id <ID>`; outside-root and symlink overrides are refused.

## Authentication

Prefer a dedicated test account and human-prepared Playwright state. Never automate authentication in the integrated browser or MCP, bypass MFA/SSO, or ask for passwords or state contents in chat. If authorized state is missing or expired, report the protected criteria as unverified. Never print, inspect in chat, stage, or attach the state. Review evidence before sharing: screenshot masking is not comprehensive.

The standalone capture command discovers `.kilo/local/qa-auth.json` in the caller's assigned Git root, not in an ancestor or sibling checkout. The human can use the skill's `qa-auth.example.json` as the template: `approved` must be `true`, `origin` must be the exact canonical HTTP(S) origin (scheme, host, port; no slash or path), `storageState` must be `qa-storage-state.json`, and `authenticatedSelector` must identify a visible signed-in-only element. No other keys, credentials, arbitrary paths or scripts. The human places the state next to the config; keep both private (0600), ignored, untracked and free of symlinks. Use HTTPS except on loopback. State may contain only test host-only cookies and local storage for this origin; indexedDB, partitioned cookies, cross-origin resources/SSO and cross-origin API flows are not supported for state reuse. An invalid config stops capture, not an anonymous fallback.

### Human setup and renewal

Use a private graphical terminal in the **assigned project's Git root**. Verify `pwd -P` matches the assignment. Use the installed `playwright open --help` (look for `--save-storage`); if the CLI, approved browser or display is unavailable, stop rather than installing anything. Choose a test origin whose entire login and review flow stays on that origin. Do not continue to an external identity provider, edit exported cookies, or import your personal browser profile.

Run this Bash block yourself, replacing the example origin first. It refuses an existing state file. A failed check means **stop before login**; correct the path, ignore rule or permissions first.

```bash
(
  set -eu
  umask 077
  origin=http://localhost:3000
  config=.kilo/local/qa-auth.json
  state=.kilo/local/qa-storage-state.json
  test "$(pwd -P)" = "$(git rev-parse --show-toplevel)"
  for path in .kilo .kilo/local "$config" "$state" artifacts artifacts/tmp; do
    test ! -L "$path"
  done
  for path in "$config" "$state" artifacts/tmp/qa-browser-probe; do
    git check-ignore -q -- "$path"  # Without --no-index: tracked paths fail too.
  done
  test ! -e "$state"
  mkdir -p .kilo/local artifacts/tmp
  chmod 700 .kilo/local
  if test -e "$config"; then test -f "$config"; else touch "$config"; fi
  chmod 600 "$config"
  export TMPDIR=$(mktemp -d artifacts/tmp/qa-browser-XXXXXX)
  test -d "$TMPDIR"
  export TMP="$TMPDIR" TEMP="$TMPDIR"
  playwright open --browser chromium --save-storage "$state" "$origin"
  test -s "$state"
  chmod 600 "$state"
)
```

Each invocation opens a new context for this project: do not pass `--user-data-dir` or `--load-storage`, record a login, or enable traces/HAR. In that window, sign in manually with the dedicated test account, complete any same-origin MFA, and verify the signed-in-only element on the intended page. Close the browser window normally to save state. If login fails or redirects off-origin, do not approve or use the resulting file.

Privately edit the prepared config using `qa-auth.example.json` above as the shape. Set the actual origin and signed-in selector, then `approved: true` only for the authorized review. Run the normal capture command above with the matching `--base-url` and protected `--route`; no auth flags or navigation file are required. A missing marker or rejected state is not a pass. On expiry, revoke the old test session as appropriate, remove only the known stale private state, and repeat the preflight and manual login from a fresh context. Never share state across projects, even on the same hostname.

Create/resume provisioning and `env.py sync` can copy the two fixed ignored files from the corresponding primary checkout without replacing existing files; `env.py status` reports presence, not validity or values. Provision just the assigned worktree directly if reuse across that repo's worktrees is not authorized. The reviewer never saves or renews state; the human must renew any authorized stale copies.

Optional `--navigation` must be ignored, untracked, `approved: true` and use reviewed same-origin steps. With discovered state, login, fill, alternate state and conflicting markers are refused. Declare page changes with `waitForURL`; a URL alone does not prove login. The standalone CLI also accepts explicitly authorized `--storage-state` plus a navigation file with a signed-in marker when no local auth config exists. Destructive steps still require explicit user authorization and `--allow-destructive`.

## Review

Check the actual user flow, relevant loading/empty/error states, keyboard focus and names, contrast, tap targets, responsive layout, and unexpected console/network failures. Auth, script, API, data-loss, and security failures remain meaningful blockers. A missing favicon is nonblocking only when proven development-only and harmless; retain its raw evidence and rationale rather than filtering logs or excusing other errors.

Only when `ui` is enabled, share available evidence with `ui-critic` to review hierarchy, usability, and product character without source edits. Consolidate findings once, deduplicate, and prioritize by user impact.

## Findings And Handoff

Read the row's `[user-approved:<scope>]` note and evidence. Report the user's decision separately from checks you performed: do not request the same review again or treat missing automation alone as a blocker for an explicitly accepted manual criterion. Preserve independent failures and unverified criteria. Changed scope is not covered, and review evidence never grants new authorization or establishes commit or merge status.

Actionable findings state `Summary`, `Repro steps`, `Expected behavior`, `Actual behavior`, `Evidence`, `Acceptance criteria`, and `Risk`. Validate persisted findings with:

```bash
python3 .kilo/skills/qa-review/scripts/check-finding.py --body-file artifacts/reviews/<finding.md> --kind bug --priority medium --category functional --route /path
```

Exit 0 accepts and prints a fingerprint; exit 66 means the finding needs better detail. The coordinator uses `board.py` for Fix rows and existing fingerprints for deduplication; reviewers report, not edit the board. Fixes reuse the original workspace and recheck affected criteria.

Use the existing `ledger.py` for QA/fix rounds when iterating: `next-round`, `finding`, `status`, and `stop` with `--task-id <ID>` (other required arguments via `--help`). It caps at three rounds; do not reset it or loop indefinitely. Escalate unresolved blockers with evidence and attempted fixes. Report pass only for proven criteria, not untested claims. Keep the final report concise: changed scope, actual checks/results, meaningful findings, and limitations.
