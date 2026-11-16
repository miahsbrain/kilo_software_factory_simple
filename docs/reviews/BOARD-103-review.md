# Independent Review: BOARD-103

## Summary
Lifecycle safety, recovery and authenticated-capture invariants need correction before handoff.

## Repro steps
1. From a feature checkout, guard a commit using attached `git -C/path` targeting main.
2. In a disposable repo, set the target merge options to `--no-commit`, then run lifecycle merge.
3. Cause a merge conflict, resolve and commit it as the human, then retry lifecycle merge.
4. Change workspace mode from a linked checkout or mapped application checkout.
5. Merge a Feature row, then discard a Chore row with the same title and reused workspace path.
6. Verify a workspace based on integration when integration is ahead of main but the feature is empty.
7. Capture `/app`, click to settings, then wait for a settings selector without a final URL assertion.
8. Capture an expired-session, same-URL SSO gate; compare an authenticated password-settings page.
9. Read the project template's work-surface sync instructions against the root pointer model.

## Expected behavior
Check the actual Git destination; prove a committed merge before deleting any source; resume a
human-completed conflict; synchronize mode and effective maps; preserve historical board outcomes;
verify the saved base; assert the final destination and an app-specific authenticated-ready marker;
document only the generated ignored-pointer model.

## Actual behavior
Attached `-C` is missed. Successful Git exit alone triggers cleanup. Completed conflict retries are
refused. Shared mode and per-checkout maps diverge. Path reuse changes old terminal rows. Verification
uses a different default base. Successful click navigation is rejected, same-URL auth gates can pass,
and password forms are rejected. The template still describes a duplicate harness/rules copy.

## Evidence
- Independent lifecycle source review: `.kilo/skills/git-worktree/scripts/guard.py:505-513`;
  `.kilo/skills/git-worktree/scripts/worktree.py:122-137`, `:700-724`, `:768-802`, `:841-854`, `:908-912`.
- Independent auth/template source review: `.kilo/skills/qa-review/scripts/browser-review.mjs:743-751`;
  `templates/project/AGENTS.md:1237-1246`. Line numbers refer to the first reviewed revision.
- Console: lifecycle regression command passed 17 tests; browser regression command passed 12 tests.
  Neither suite covered these scenarios at that revision.
- Screenshot and network: not captured in this initial source-review pass; authenticated capture
  needs focused browser proof. Spec/test sources: `test_lifecycle.py` and `browser-review.test.mjs`
  beside the existing reviewed scripts.

## Acceptance criteria
- [x] Destination protection and committed-merge cleanup have disposable-repo regression proof.
  Proof: authorized BOARD-107 independent follow-up suite, 33 discovered/passed, exit 0; includes the existing guard and committed-merge regressions.
- [x] Conflict retry, consistent mode/maps, board incarnation and saved-base regressions pass.
  Proof: same 33-test independent suite, including reordered inherited rule regressions at `.kilo/skills/git-worktree/scripts/test_lifecycle.py:246-300`.
- [x] Successful nested navigation and explicit authenticated-ready proof pass capture tests.
  Proof: independent Round 2 run of `node --test .kilo/skills/qa-review/scripts/browser-review.test.mjs`, 19 passed, exit 0; test source at lines 222-250,279-288,359-387.
- [x] The project template matches the existing ignored-pointer model.
  Proof: independent Round 2 source review of `templates/project/AGENTS.md:1236-1250`.
- [x] Corrected current state receives an independent review before merge readiness.
  Proof: authorized BOARD-107 follow-up independently reviewed current source and passed 33 tests;
  auth/rules independently passed in Round 2. Subsequent changes are documentation only, reviewed
  against approved rules by the orchestrator; no further parent review round was opened.

## Risk
High: faulty lifecycle checks can lose source work or misreport merges. Discard and source deletion
are one-way; corrective code/config/documentation edits are two-way. No real merge or discard was run.

## Round 2
Independent lifecycle review passed 25 tests but found two uncovered repeats:
- BOARD-104: `.kilo/skills/git-worktree/scripts/guard.py:494-502` ignores shell directory changes.
  A `cd` chain can make the real Git destination differ from the checked feature workspace.
- BOARD-107: `.kilo/skills/git-worktree/scripts/worktree.py:599-611` creates a new checkout from
  base configuration without regenerating its map for the saved project mode.
The existing rows and parent were Blocked, not duplicated. The user then explicitly approved
rejecting unsupported directory-changing chains, regenerating maps during creation, focused
regressions and one third/final independent review in this original workspace.

Independent auth/rules review found no blocking BOARD-110 through BOARD-112 defects. Its single
`node --test .kilo/skills/qa-review/scripts/browser-review.test.mjs` run passed 19 tests, exit 0.
Proof: `.kilo/skills/qa-review/scripts/browser-review.mjs:271-303,758-775`,
`.kilo/skills/qa-review/scripts/browser-review.test.mjs:222-250,279-288,359-387`, and
`templates/project/AGENTS.md:1236-1250`. The canonical-script fixture proves one login, retained
cookie/sessionStorage authentication and two settings-page visits across two viewports, PNG
creation, and no fixture password/session values in console/page-error/network/stdout/stderr.
No screenshot pixels, external SSO/MFA, real account or real-browser imported-state flow were
reviewed; arbitrary private page content still needs human evidence inspection.

## Round 3: Blocked
P1 repeat `bug|functional|/factory|mode-map-consistency`: inherited permission validation at
`.kilo/skills/git-worktree/scripts/worktree.py:640-643` compares dictionaries without insertion
order. In optional mode, moving `permission.edit["*"]: "allow"` after secret-deny entries leaves
dictionary equality unchanged but changes effective protection. An app checkout inheriting that
map is accepted instead of preserving an incomplete creation. The existing ordered-items check
at `.kilo/skills/git-worktree/scripts/guard.py:775-778` is the reuse candidate for a follow-up.

Builder evidence: the authorized lifecycle suite passed 31 tests in 12.054 seconds, exit 0.
Final independent attempt reported `Ran 0 tests in 0.000s`, exit 0; this is no regression proof.
The finding is established by current-source inspection, not an executed exploit.

BOARD-107 and parent BOARD-103 are Blocked. The round cap is reached; no fourth correction or
review is authorized. The template BOARD permission hold also remains. Preserve the original
workspace and checkpoint commits; do not merge, discard or enable the feature. A human follow-up
decision and permission reload are required. No actual merge, discard or mode change was run.

## Authorized BOARD-107 Follow-Up
The user explicitly authorized a separate focused follow-up after the capped parent review.
The original three-round ledger is preserved. Existing ordered-items comparison was extracted
to pure `permission_maps_match(current, expected)` at
`.kilo/skills/git-worktree/scripts/guard.py:758-762` and reused by `check-policy` at line 782 and
inherited validation at `.kilo/skills/git-worktree/scripts/worktree.py:642`.

Independent current-source review found no blocking defect. Its sole command used the correct
workspace and absolute discovery path:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s /projects/kilo_inhouz_ai/.kilo/worktrees/configurable-shared-workspace-lifecycle-and-authenticated/.kilo/skills/git-worktree/scripts -p test_lifecycle.py -v`.
Result: `Ran 33 tests in 14.190s`, `OK`, exit 0, nonzero discovery. The orchestrator inspected the
baseline diff separately; the independent reviewer did not run `git diff 08ac314`.
Tests cover reordered edit/bash/read maps in both modes, ordered maps accepted, inherited/base
configuration and board unchanged on refusal, preserved partial tree/branch/journal error, and
no copied app harness. All lifecycle effects used disposable temporary repositories.

The former BOARD-107 rule-order defect is resolved and verified. The unchanged, denied BOARD
template remains the parent hold. No merge-readiness claim, actual lifecycle action or mode change.

After code checkpoint `f0b9c95`, the user confirmed a task-worktree reload and authorized one
template-edit retry. `apply_patch` still returned the project rule
`{"permission":"edit","pattern":"**/docs/BOARD.md","action":"deny","source":"project"}`.
The template is unchanged. No alternate-tool bypass or repeat attempt was made. A session with
effective permission for the approved template-only edit is still required; parent stays Blocked.

## Template Hold Resolved
After the user's permission edits and latest reload, the approved template update succeeded.
`templates/project/docs/BOARD.md:27-49` now documents shared workspace reuse, required/optional
mode, clean human merge with automatic cleanup/board outcomes, partial failures and explicit
dirty/unmerged discard. The orchestrator reviewed these changes against approved root rules.
Verification limited to file review because this was a low-risk visual/static change; whitespace
is checked with `git diff --check`. No lifecycle/auth source changed after the verified fix.
The capped ledger remains historical; no fourth parent round or real lifecycle action was run.
After the documentation commit and clean-source check, shared rows can be Pending Merge together.
The approved temporary policy edits were restored in both checkouts and the feature config.
Main generated-config restoration was tool-denied and remains human cleanup; the only tracked
target diff is live-board metadata. The verified feature policy/map are unchanged from checkpoint.
