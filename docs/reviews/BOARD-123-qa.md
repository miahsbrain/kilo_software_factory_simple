# QA review — BOARD-123 Gate merge handoffs on finished clean worktrees

**Reviewed commit:** `2c1f1501b2e88dacb20b9ba57a54b05d2fd89f21`   **Verdict:** PASS
**Command:** `python3 -m unittest discover -s .opencode/skills/git-worktree/scripts -p 'test_handoff.py'`
**Result:** Builder's architect-authorized second run: exit 0, 13 tests in 3.847s, recorded in `docs/changelog/CHANGELOG.md:12`. Not rerun by this reviewer: assigned test budget exhausted. Independent diff/file review and live read-only refusal check below.

## Acceptance criteria

Criteria below map the delegated approved gates and ADR-082 to observable checks.

- [x] Unmerged work gets merge guidance only when clean, committed ahead and Pending Merge — `worktree.py:1020–1048`; `test_handoff.py:57–95` asserts ready ordering, staged/unstaged/untracked refusal, every nonready status, missing status and no commits ahead. Focused run above passed.
- [x] Failed Git checks never imply cleanliness/readiness — `worktree.py:1023–1048` checks status/count/ancestry and resolved tips; `git_out` at line 93 returns None on failure. `test_handoff.py:97–113` covers status, branch, count, ancestry and rev-parse failures plus empty successful count. Focused run above passed.
- [x] Refusal withholds merge and teardown, retaining review commands for a resolved worktree/base — independent `python3 .opencode/skills/git-worktree/scripts/worktree.py handoff --board BOARD-123` exited 1 as expected on clean reviewed commit. Output contained diff/log and `NOT READY: board status is In Review, not Pending Merge; finish verification and review`; no merge/cleanup/manual teardown commands. `test_handoff.py:47–55` checks all four forbidden command forms.
- [x] Already-merged work receives no redundant merge — `worktree.py:1050–1054`; `test_handoff.py:137–148` tests a clean no-ff merge with Merged status and retains review/cleanup. Focused run above passed. Existing same-tip exclusion is preserved from `branch_already_merged` at lines 942–954, not a new behavior.
- [x] Handoff is read-only; root/template/derived guidance prohibit manual bypass — `cmd_handoff` at `worktree.py:971–1066` reads board/Git and prints only; `test_handoff.py:123–129` compares board bytes and Git status. `git diff opencode..HEAD -- AGENTS.md templates/project/AGENTS.md .opencode/commands .opencode/skills/git-worktree/SKILL.md` shows §B5/§B11 and all four changed commands replacing unconditional guidance with the approved gate. No source or board edits in this review.

## Findings

| # | Severity | Expected | Actual | Repro | Evidence |
|---|---|---|---|---|---|
| — | — | Approved gates | No defect identified in reviewed scope | Live In Review handoff | Expected exit 1 and blocker above |

No Fix rows requested. No criterion needs to return to In Progress. PASS is not permission to merge: the orchestrator still owns the live Pending Merge transition.

## Review and coverage

- Reuse: extends existing `cmd_handoff`; reuses board parser, `STATUS_INDEX`, live-row/repo/base resolution and checked Git helpers. New tests reuse `test_env.make_repo/run/git/write`; no replacement tool or readiness framework.
- Regression integration: `test_env.py:314–365` now asserts initial refusal, commits the task file and sets scratch Pending Merge before expecting ready output; subsequent no-ff merged assertions remain. Existing fixture flow is compatible on file review; full suite execution is not claimed.
- Positive: error injection asserts externally visible refusal and omitted commands, rather than mock-call counts. Fresh temporary Git repositories isolate each test from live work.
- Nonblocking coverage limits: no dedicated live/recorded regression for a mismatched (rather than missing) recorded branch, dirty already-merged work, or repository-discovery failure; source uses the same blockers before either output branch. Same-tip ancestry follows existing semantics; fast-forward-specific behavior was not newly verified.
- User: a maintainer reviewing task work gets immediate review commands and an actionable status blocker, without a premature destructive next step. Output density suits terminal review.
- Skills used: catalogue `code-reviewer` (review checklist, spec-compliance, report-template) and `test-master` (unit/integration, testing anti-patterns, QA methodology, test reports); local `qa-review` and `git-worktree` procedures.

## Not done

- No new test execution, full lifecycle/env suite, build, installation, real merge or teardown: explicitly excluded by assignment/budget.
- No UI change: browser, gallery, screenshots, U1–U8/M1–M10 screen matrix, contrast/focus/tap targets, responsive, console/network and unslop gates are not applicable. No UI pass asserted.
- Historical unrelated HANDOVER conflict markers left unchanged as assigned. Separate project copy untouched.
- No board edits. Evidence is this report's command transcript summary, source/test line references and the existing builder run record; no browser artifacts were created.
