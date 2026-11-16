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
- [ ] Destination protection and committed-merge cleanup have disposable-repo regression proof.
- [ ] Conflict retry, consistent mode/maps, board incarnation and saved-base regressions pass.
- [ ] Successful nested navigation and explicit authenticated-ready proof pass capture tests.
- [ ] The project template matches the existing ignored-pointer model.
- [ ] Corrected current state receives an independent review before merge readiness.

## Risk
High: faulty lifecycle checks can lose source work or misreport merges. Discard and source deletion
are one-way; corrective code/config/documentation edits are two-way. No real merge or discard was run.
