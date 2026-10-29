---
name: qa-review
description: Verify a change against its acceptance criteria with Playwright, capture screenshot and console evidence, and file each finding as a board row. Use for the QA lane of any frontend or API change, or when the user says "QA review", "verify this", or "run QA".
---

# QA Review

The QA lane **produces evidence, not assertions**. A finding without a screenshot, a console log,
or a failing command is not a finding — it is an opinion.

**The script captures. You judge.** The script does the mechanical work; you decide what is a
defect, what the severity is, and what the fix should be.

---

## 1. The scripts

| Script | Does |
|---|---|
| `.kilo/skills/qa-review/scripts/browser-review.mjs` | drives Playwright, captures screenshots, console errors, page errors, network failures, overflow |
| `.kilo/skills/qa-review/scripts/check-finding.py` | validates a finding body before it becomes a board row |

The Playwright runner uses the **project's own** Playwright installation. It never installs
anything.

---

## 2. Capture the evidence

Start the app first, using the dev command from `docs/STACK.md`. Then:

```bash
node .kilo/skills/qa-review/scripts/browser-review.mjs \
  --base-url http://localhost:15173 \
  --route / --route /settings \
  --artifact-dir apps/web/artifacts/qa/2026-10-29/BOARD-005 \
  --project apps/web
```

- `--route` repeats; capture every route the change touches.
- `--viewports` defaults to `390x844,834x1112,1440x900,1920x1080,320x800`.
- `--project` is where Playwright must resolve from. Default: the current directory.

It writes, per route and viewport: `full.png`, `console.log`, `page-errors.log`, `network.json`,
plus a top-level `summary.json` with the counts and the horizontal-overflow result at each width.

The script exits 0 when the capture completed, even when errors were found. Findings are your
job. It exits 2 on a fatal failure (browser launch, bad URL) — report that, do not fake a review.

---

## 3. What counts as a failure

A row is **red** when any of these fire:

- a console error (`level === 'error'`)
- an uncaught page error
- a 5xx response during the flow
- a 401/403 on a page that requires auth
- horizontal overflow at 320px
- a non-blank guard fails: the page is empty where it should have content — a list page shows no
  rows and no empty-state element; a dashboard shows no widget with real data
- an acceptance criterion has no observable check

**A 200 response with a blank body is a bug, not a pass.**

---

## 4. Judge the evidence

For each acceptance criterion on the board row, write one observable check and its result.
Then look at the screenshots and answer:

- Does the screen match the approved component gallery — tokens, radius, type scale, accent,
  spacing, states?
- Does it read as designed by a person, or generated? Check the 15 anti-slop rules in
  `docs/UI-UX.md` §2.
- Do the empty, loading, and error states say something specific and name the next action?
- Is the primary action obvious? Does the hierarchy read at 320px?

---

## 5. Write the finding

One file per finding, in the scope you reviewed:

```
apps/<scope>/artifacts/qa/<date>/<task-id>/finding-<n>.md
```

Required sections — the validator enforces this:

```markdown
## Summary
One sentence: what is wrong and where.

## Repro steps
1. exact route and action
2. next action
3. observed failure

## Expected behavior
What should happen, citing the acceptance criterion.

## Actual behavior
What happened instead.

## Evidence
- Screenshot: apps/web/artifacts/qa/2026-10-29/BOARD-005/settings/full.png
- Console: 0 errors, see console.log
- Network: one 500 on /api/export, see network.json
- Spec: apps/web/e2e/export.spec.ts

## Acceptance criteria
- [ ] POST /api/export returns a CSV
- [ ] the export button is disabled while the request runs

## Risk
🟡 medium — one endpoint is unreachable from the export button.
Reversibility: two-way. Blast radius: anyone using the export flow.
```

Validate before submitting:

```bash
python3 .kilo/skills/qa-review/scripts/check-finding.py \
  --body-file apps/<scope>/artifacts/qa/<date>/<task-id>/finding-<n>.md \
  --kind bug --priority medium --category functional --route /settings
```

Exit 0 → accepted. Exit 66 → the finding is too weak to act on; fix the body. A finding that
names no expected behavior, no repro, and no evidence is not a finding.

---

## 6. File the findings on the board

A validated finding becomes a **board row of type `Fix`**:

- `Status: Ready` — or `Blocked` when the finding needs a product decision
- `Priority` from the severity: `high` → `P1`, `medium` → `P2`, `low` → `P3`
- `Risk` from the blast radius of the defect
- `Blocked by: BOARD-xxx` — the row that produced the finding
- `Notes` — expected, actual, repro, evidence path

```bash
python3 .kilo/skills/board/scripts/board.py add \
  --id BOARD-006 --task "Export button stays enabled during the request" --type Fix \
  --status Ready --priority P2 \
  --risk "🟡 medium — one endpoint is unreachable while the request runs" \
  --blocked-by "BOARD-005" \
  --note "Expected: button disabled during request. Actual: stays enabled, user can double-submit. Repro: /settings -> Export. Evidence: apps/web/artifacts/qa/2026-10-29/BOARD-005/settings/full.png"
```

**The board is written by the orchestrator in the main checkout.** A reviewer working in a
worktree reports its findings; the orchestrator creates the rows.

---

## 7. Verdict

- **PASS** — every criterion verified with a proof line, no findings. The row may proceed to
  `Pending Merge`.
- **FAIL** — any finding, or any criterion without a proof. The row returns to `In Progress` with
  the failing findings restated.

Never mark an unchecked criterion as done. Never write a "not verified" section on the finding —
an unchecked acceptance criterion plus a one-line reason replaces it.

---

## 8. Report back

What was done, what is proven, what is not done and why, the next action — in that order, four
lines or fewer.
