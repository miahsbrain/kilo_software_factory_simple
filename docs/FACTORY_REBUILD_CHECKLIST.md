# Factory rebuild verification

BOARD-137. Checked items identify delivered behavior or guidance, not guarantees about future agent output. Run the commands below from the factory implementation worktree.

## Implementation

- [x] **1. Frontend:** On a compatible stack, trace the approved library (default shadcn/ui) through its alias, export and screen import. Review gallery states, token use, focus and responsive layout before screen approval. See `.claude/agents/frontend-dev.md` and `docs/UI-UX.md`.
- [x] **2. Backend:** Preserve existing request, response and error contracts. Separate domain decisions from I/O; check authorization, validation, failure handling and query behavior. See `.claude/agents/backend-dev.md`.
- [x] **3. Specialists:** All seven roles specify what to inspect, what evidence to return and when to escalate. Root and generated instructions prioritize readable names, focused code and comments explaining decisions rather than mechanics.
- [x] **4. Authenticated QA:** The browser runner discovers the ignored profile and reuses a human-prepared test session. Require the exact origin and visible signed-in indicator; refuse invalid configuration. Provision only named QA files without overwriting current copies. Example: `.claude/skills/qa-review/qa-auth.example.json`. Do not put passwords in tracked templates.
- [x] **5. Board:** `approve-review` records the user's decision by scope, removes only the matching gate and returns the row to In Review only when no other blockers remain. A duplicate finding does not silently escalate. Acceptance is not a merge, automated check or new authorization.
- [x] **6. Workspace:** `mode adaptive` and `create --skip-worktree` permit eligible maintenance on an unprotected mapped checkout. Required mode refuses skipping. Features remain linked. Check the lane, blockers, assignment and effective permission map without switching branches or persisting a new assignment.
- [x] **7. Workflow:** `/factory-run`, `/factory-board`, `/factory-ui` and `/factory-closeout` reuse recorded decisions and distinguish acceptance, verification and Git handoff. Workspace refusals identify recovery/eligibility issues. Existing planning and initial gallery gates remain; no blanket permission override was added.
- [x] **8. Documentation:** README quick paths, working agreements, specialist and skill docs, UI guidance, decisions ADR-093 through ADR-095 and CHANGELOG describe the shipped behavior.
- [x] **9. Regression coverage:** Board approval plus adaptive checkout are exercised together against a disposable repository. Browser tests exercise protected routes, session reuse and denied access; lifecycle tests cover all three modes and nested checkouts. Reproduction commands below.
- [x] **10. Templates:** New projects receive local tooling and the credential-free example, not the factory's private state. New projects generate required-mode permissions independently of the factory; control restore respects the destination mode. Project instructions and UI guidance reflect the new conventions.

## Reproduce checks

For a new run, resolve `artifact_root=$(python3 .claude/skills/qa-review/scripts/ledger.py artifact-root) || exit 1` from the assigned source and verify the central directory before using it for temporary output. The results and evidence links below describe the original run, not new verification.

| Command | Result |
| --- | --- |
| `TMPDIR="$artifact_root" python3 -B -m unittest discover -s .claude/skills/git-worktree/scripts` (existing verified directory; repositories created by the tests are disposable fixtures) | 99 passed: bootstrap/restore and lifecycle |
| `python3 -B .claude/skills/git-worktree/scripts/test_env.py` | All standalone provisioning and reuse checks passed |
| `python3 -B -m unittest discover -s tests -v` | 10 passed: approval replay, mismatched gates, gallery controls and cross-CLI maintenance workflow |
| `node --test .claude/skills/qa-review/scripts/browser-review.test.mjs` | 25 passed, none skipped, including Chromium against disposable protected routes |
| `python3 -B -m unittest discover -s .claude/skills/qa-review/scripts -p test_ledger.py` | 8 passed |
| `bash .devcontainer/test-shell-redact.sh` | 26 passed |

## Verification limits

Follow-up Chromium review: the gallery fit all five configured viewports from 320 to 1920 px without horizontal overflow or reported console, page or network errors. Static update controls are disabled and labeled as fixture UI. Keyboard activation of the live refresh control reloaded the board with HTTP 200 at 390 and 1440 px. Evidence: `artifacts/reviews/gallery-refresh-recheck.json` and `artifacts/factory/qa/2026-11-23/gallery-refresh-fix/summary.json`.

The QA skill now documents human session creation and renewal with the installed Playwright CLI. Private-path preflight and disposable session reuse were tested. Interactive window-close-to-save was not exercised in this environment (no `xauth`).

- The factory gallery and board rows use the same `wb_card` function. In-process HTTP handler checks exercised `/health`, `/api/worktrees` with empty injected state, and an unknown route. This is not an end-to-end product design evaluation.
- [ ] Compile a real shadcn screen and evaluate its design against the user's brief in an assigned product. This factory contains no tracked shadcn app. No dependency was installed to manufacture a pass.
- [ ] Confirm session reuse with the intended product's dedicated test identity. Only disposable local accounts/sessions were exercised; real SSO, MFA and cross-origin identity flows were not tested. Sign-in and renewal remain human steps for reusable state.
- No existing independent project was migrated, no live workspace mode was switched, and no merge was performed.
