# BOARD-121 — parent preview observations (2026-11-11)

**Status: HOLD.** Attributed parent observations only, not an independent QA verdict or a
whole-task pass. This document checkpoints supplied evidence; this builder ran no browser calls.

## Preview and observed evidence

Parent inspected the `fd89d5b` diff and started the main dashboard from the assigned worktree at
`http://127.0.0.1:15183/`. Live 15180 remained unchanged. Built-in browser tab:
`tab_13dd71d5-57f7-4613-b49f-512abb0f3628`.

Parent snapshot and DOM inspection reported:

- Project selected by default with 14 tasks; Harness has 21 tasks and its panel is hidden.
- Result count is 14 of 14 for the selected Project scope.
- Project rail has three worktrees: `docs/approve-prototype-contracts-and-toolchain`,
  `feat/ingest-channels-and-review-shorts-candidates`, and `main`.
- Hidden Harness contains eight control worktrees, separate from the Project rail.
- Actual viewport is 1000×700 CSS pixels with no horizontal overflow at that width.
- Refresh interval is 60 seconds; section heading is 17px/600; no fixture notice on main.

These observations establish the reported initial DOM state, not clicked tab switching, persisted
selection, keyboard operation, elapsed auto-refresh, complete visual conformance or responsive QA.

## Screenshot blocker

After `browser.tabs.focus`, the parent's built-in screenshot call returned
`browser.operation_failed`:

> Screenshot needs a visible tab. Call browser.tabs.focus and keep its desktop window visible.

No process exit code applies to this browser tool error. No screenshot was produced. Parent made
no retry or fallback. No artifact-path workaround, Playwright, MCP or capture script was used.
The desktop window must be visible before the parent resumes screenshot capture and review.

## Acceptance evidence and holds

- [x] Focused presenter/refresh regressions pass on implementation `fd89d5b`.
  Proof: `python3 .opencode/skills/board/scripts/test_board_serve.py` exited 0; 15 tests in
  0.048s. Existing builder proof, not rerun for this docs-only checkpoint.
- [x] Initial scope isolation/default and real-data counts observed by parent.
  Proof: parent snapshot/DOM observations above at 15183, tab named above; not independent QA.
- [ ] Screenshot-backed independent visual critique and rendered unslop audit.
  Held by the exact screenshot error above; no visual pass claimed.
- [ ] Keyboard/focus, interaction and refresh behavior in the browser.
  Not established by the supplied initial snapshot/DOM inspection.
- [ ] Full responsive matrix, contrast and target-size checks.
  Only 1000×700 overflow observation supplied; other sizes/checks remain unverified.

Docs-only handoff: no source edits, browser retries, tests, builds, server changes, rules or board
edits. Recommendation: keep the desktop window visible, then parent resumes built-in-browser QA;
do not mark this work merge-ready on these partial observations.
