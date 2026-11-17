---
description: Run the QA and UI/UX review lane with Playwright and produce evidence
---

Run the QA lane and the UI/UX critique for a frontend row. Evidence, not assertions.
Spec: `docs/UI-UX.md` §3 and §5.
Use the original assigned repo-specific workspace set, including fixes and fresh reviewer sessions;
never create a review worktree. Read local rules and explicitly permitted shared governance.
Application source stays read-only; approved auth/navigation and evidence writes are allowed.

1. **Confirm the app runs.** Use the dev command from `docs/STACK.md`. If it does not start,
   report the blocker; do not fake a review.
2. **Capture with the script** — it drives the project's own Playwright and writes a full-page
   screenshot, `console.log`, `page-errors.log`, and `network.json` per route per viewport, plus a
   `summary.json` with the counts and the overflow result:

       node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url <url> --route /path \
           --scope <scope> --task-id <task-id> --project apps/<scope>

   The script computes the canonical artifact path itself — `artifacts/<scope>/qa/<date>/<task-id>/`
   in the **main checkout** — so no agent has to remember it.

   Viewports: 390×844 (mobile), 834×1112 (tablet), 1440×900 (desktop), 1920×1080 (wide), and
   320×800 as the overflow floor.

   **The script is the only way to capture UI evidence.** Ad-hoc `chromium`, `npx playwright
   screenshot`, `curl`-and-guess, or any other browser command run from bash is not acceptable
   evidence for a UI review. The script never installs a browser and never falls back to another
   driver. If the script cannot do something the review needs, say what is missing and propose
   the change — a change to a project tool is a reviewed change, not a silent patch mid-review.
   Do not work around it with another tool.

   Extra flags: `--scheme light|dark|both`, `--component <css-selector>` (repeatable),
   `--compare <dir>` (before | after sheet), `--label <slug>` (names the round's capture),
   `--chromium <path>` (the path of a chromium binary handed to Playwright's launch; it
   overrides `PLAYWRIGHT_CHROMIUM_PATH`). When no chromium is found at all, the script exits 2
    with the list of places it searched.
   Authenticated routes use `--storage-state <ignored-local.json>` and/or `--navigation
   <ignored-local.json>` with the approved schema in the QA skill. Ask for test access if absent;
   MFA/SSO is manual user login, never bypassed. `--allow-destructive` requires explicit action
   approval. No secret literals in CLI, commits or evidence. Masking covers known credentials/session
   values, not arbitrary sensitive content; inspect evidence before sharing. All counts/checks remain.
3. **Check the round ledger** — a row goes through at most 3 QA↔fix rounds, and each round's
   review is done by a fresh reviewer who reads the ledger, not the previous reviewer's
   reasoning:

       python3 .kilo/skills/qa-review/scripts/ledger.py status --task-id BOARD-005

   The ledger lives at shared control-root `artifacts/reviews/<task-id>-ledger.md`.
   `status` prints the resolved path; use its directory for all reports and findings.
4. **Store artifacts** under `artifacts/<scope>/qa/<YYYY-MM-DD>/<task-id>/` with a
   `notes.md` recording what was checked and expected vs actual. Never stage or commit artifacts,
   including notes and component shots. Reports, findings and ledgers live in the control main
   checkout's ignored `artifacts/reviews/`, shared by worktrees: `<task-id>-qa.md`, `<task-id>-ui.md`,
   `<task-id>-review.md`, `<task-id>-ledger.md` and `<task-id>-finding-<n>.md`.
5. **Check** and report findings as expected-vs-actual:
   - keyboard focus, visible focus ring, focus trapping in dialogs
   - contrast, accessible names on controls, alt text
   - tap targets ≥ 24×24 CSS px
   - console errors, unexpected 4xx/5xx
   - horizontal overflow at 320px
   - does the screen match the approved component gallery (tokens, states, density)
6. **UI/UX critique** against the 15 anti-slop rules in `docs/UI-UX.md` §2, **and** the
   user-centred (U1–U8) and modern (M1–M10) criteria in §3. Each finding names the rule, the
   screenshot or `file:line` that proves it, and the fix. A screen that passes §2 and fails §3
   is still a FAIL.
   The critique also runs the unslop pass: every sign in `.kilo/skills/unslop/references/signs.md`
   that the capture shows, with where it lives. The precedence rule for a disagreement is in
   `AGENTS.md` §B4.3.
7. **Validate each finding and take its fingerprint**:

       python3 .kilo/skills/qa-review/scripts/check-finding.py --body-file <finding.md> \
           --kind bug --priority medium --category functional --route /path

   Exit 0 prints the fingerprint on stdout. Pass it to `board.py add --fingerprint`; a repeat
   fingerprint is refused and the existing row is escalated to `Blocked` instead.
8. **Verdict**: a frontend row cannot leave `In Review` until both QA and the critique are
   green. Findings request `In Progress` unless a §B4.4 stop condition applies. If round 3 ends
   with unresolved blocking findings, stop automatically. Highlight remaining problems, severity,
   user impact, evidence and attempted fixes. Record the stop reason and request `Blocked` from
   the orchestrator. Ask the user how to proceed, directly when interactive or through the
   orchestrator when delegated. Offer a revised approach, defer/drop, or explicitly scoped
   follow-up. Never start round 4, reset the ledger or claim completion. Round 3 success follows
   the normal merge gate, not automatic `Blocked` status.

Report in this order: what was done, what is proven, what is not done and why, next action.
