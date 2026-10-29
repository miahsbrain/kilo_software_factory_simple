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
| `.kilo/skills/qa-review/scripts/check-finding.py` | validates a finding body before it becomes a board row, and prints its fingerprint |
| `.kilo/skills/qa-review/scripts/ledger.py` | tracks the bounded QA/fix rounds of one row |

The Playwright runner uses the **project's own** Playwright when it has one, and the global
install the devcontainer provides otherwise. It never installs anything and never drives a browser
over a hand-rolled protocol.

---

## 2. Capture the evidence

Start the app first, using the dev command from `docs/STACK.md`. Then:

```bash
node .kilo/skills/qa-review/scripts/browser-review.mjs \
  --base-url http://localhost:15173 \
  --route / --route /settings \
  --scope web --task-id BOARD-005 \
  --project apps/web
```

The script exits 0 when the capture completed, even when errors were found. Findings are your
job. It exits 2 on a fatal failure (browser launch, bad URL) — report that, do not fake a review.

### The script is the only way to capture UI evidence

The QA reviewer and the UI critic capture screenshots **only** through `browser-review.mjs`.
Ad-hoc `chromium`, `npx playwright screenshot`, `curl`-and-guess, or any other browser command
run from bash is **not acceptable evidence** for a UI review.

If the script cannot do something the review needs, **extend the script** — do not work around it
with another tool.

| Flag | What it adds |
|---|---|
| `--scope <name>` | Scope folder under `artifacts/`. Default: `factory`. |
| `--task-id <id>` | Task folder under `qa/<date>/`. Default: `adhoc`. |
| `--date <YYYY-MM-DD>` | Capture date folder. Default: today. |
| `--artifact-dir <dir>` | Optional override for the task directory. |
| `--scheme light\|dark\|both` | Capture in one colour scheme, or both. |
| `--component <css-selector>` | A cropped screenshot of each matched element. Repeatable. |
| `--compare <dir>` | A **before \| after** sheet against a previous capture, per scheme. |
| `--label <slug>` | Names the capture, so round 0, round 1 and round 2 can be compared. |

### Artifact layout

There is **one canonical artifacts folder**, at the repository root:

```
artifacts/
  <scope>/                    # web | api | mobile | factory
    qa/
      <YYYY-MM-DD>/
        <task-id>/            # BOARD-005
          <route-slug>/
            <viewport>/
              <scheme>/        # light | dark
                <screenshot>.png
                console.log
                page-errors.log
                network.json
                compare.png
          notes.md              # what was checked, expected vs actual
          summary.json
```

The script computes that path itself — `--scope`, `--task-id` and `--date` name the folders — so no
agent has to remember it. The artifacts folder belongs to the **main checkout**: a capture taken
from a worktree still lands in the same place.

**Review reports and the ledger are documents, not artifacts.** They stay where documents live:
`docs/reviews/<task-id>-qa.md`, `docs/reviews/<task-id>-ui.md`, and
`docs/reviews/<task-id>-ledger.md`.

Per route, viewport, and scheme:

    1440x900/light/1440x900-light.png   the screenshot
    1440x900/light/console.log            console errors
    1440x900/light/page-errors.log        uncaught page errors
    1440x900/light/network.json           failed responses and requests
    1440x900/light/compare.png            before | after, when --compare is used

`summary.json` sits in the task directory, with one entry per route, viewport, and scheme, each
carrying that scheme's own console, page-error, network, and overflow counts. The two schemes
never share a file. `notes.md` sits beside it and records the routes, viewports, schemes, the
command used, and the console/page/network counts per scheme. With `--label`, the captures go
into a label folder inside the task directory; `summary.json` and `notes.md` stay in the task
directory.

### Where Playwright comes from

The script uses the **project's own** Playwright when it has one. Otherwise it resolves the
global install the devcontainer provides:

    /usr/local/share/npm-global/lib/node_modules/@playwright/mcp/node_modules/playwright

The container sets `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` and installs system chromium, so the
script launches `/usr/bin/chromium` when Playwright has no downloaded browser. Override the
binary with `PLAYWRIGHT_CHROMIUM_PATH`.

### The interactive browser tool

`playwright-mcp` is configured in `kilo.jsonc`, so the Playwright MCP tools are available for
interactive exploration — navigating, snapshotting, clicking, reading the console. Use them to
*investigate*. Use `browser-review.mjs` to *capture evidence* for a verdict, because it produces
the artifact set, the per-scheme counts, and the summary the verdict depends on.

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

Then judge it for the **user**, not only for the spec. Answer every question in
`docs/UI-UX.md` §3.1 (user-centred, U1–U8) and §3.2 (modern, M1–M10), and the density rule in
§3.3. A screen that passes the acceptance criteria and fails §3 is still a FAIL — beautiful and
useless is not done.

Also check **reuse**: does the diff duplicate an existing function, component, or state instead of
expanding one? Name the existing code if it does.

---

## 5. Write the finding

One file per finding, in the scope you reviewed:

```
artifacts/<scope>/qa/<date>/<task-id>/finding-<n>.md
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
- Screenshot: artifacts/web/qa/2026-10-29/BOARD-005/settings/1440x900/light/1440x900-light.png
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
  --body-file artifacts/<scope>/qa/<date>/<task-id>/finding-<n>.md \
  --kind bug --priority medium --category functional --route /settings
```

Exit 0 → accepted. Exit 66 → the finding is too weak to act on; fix the body. A finding that
names no expected behavior, no repro, and no evidence is not a finding.

On acceptance the script prints the finding's **fingerprint** on stdout:

```
check-finding: body accepted
fingerprint: bug|functional|/settings/export-button-stays-enabled
```

The fingerprint is `kind|category|route|subject` — deterministic, so the same complaint about the
same thing produces the same value. Pass `--fingerprint <value>` to override the derived one.

---

## 6. File the findings on the board

A validated finding becomes a **board row of type `Fix`**:

- `Status: Ready` — or `Blocked` when the finding needs a product decision
- `Priority` from the severity: `high` → `P1`, `medium` → `P2`, `low` → `P3`
- `Risk` from the blast radius of the defect
- `Blocked by: BOARD-xxx` — the row that produced the finding
- `Fingerprint` — the value `check-finding.py` printed
- `Notes` — expected, actual, repro, evidence path

```bash
python3 .kilo/skills/board/scripts/board.py add \
  --id BOARD-006 --task "Export button stays enabled during the request" --type Fix \
  --status Ready --priority P2 \
  --risk "🟡 medium — one endpoint is unreachable while the request runs" \
  --blocked-by "BOARD-005" \
  --fingerprint "bug|functional|/settings/export-button-stays-enabled" \
  --note "Expected: button disabled during request. Actual: stays enabled, user can double-submit. Repro: /settings -> Export. Evidence: artifacts/web/qa/2026-10-29/BOARD-005/settings/1440x900/light/1440x900-light.png"
```

**A duplicate fingerprint is refused.** When the fingerprint is already open on another row, the
script refuses the add, names the existing row and its status, and prints the command that
updates it. A repeat finding updates the existing row's notes instead of opening a new row:

```bash
python3 .kilo/skills/board/scripts/board.py note BOARD-006 --value "<the new evidence>"
```

The same fingerprint filed twice escalates the existing row to `Blocked` rather than a new row
opening.

**The board is written by the orchestrator in the main checkout.** A reviewer working in a
worktree reports its findings; the orchestrator creates the rows.

---

## 6a. The bounded loop: rounds and the ledger

A row may go through **at most 3** QA↔fix rounds. Round 3 is the last.

Each round's state lives in one short file per row: `docs/reviews/<task-id>-ledger.md`. It holds
the round number, the findings filed in that round, the Fix row IDs created, the Fix rows merged
since, and the stop reason when it stops.

The ledger is the **only** thing carried between rounds. **Each round's review must be done by a
fresh reviewer** that reads the ledger and the current screenshots — not the previous reviewer's
reasoning.

```bash
python3 .kilo/skills/qa-review/scripts/ledger.py next-round --task-id BOARD-005
python3 .kilo/skills/qa-review/scripts/ledger.py finding  --task-id BOARD-005 \
    --fingerprint "bug|functional|/settings/export-button-stays-enabled" \
    --evidence artifacts/web/qa/2026-10-29/BOARD-005/finding-1.md --fix-row BOARD-006
python3 .kilo/skills/qa-review/scripts/ledger.py merged   --task-id BOARD-005 --fix-row BOARD-006
python3 .kilo/skills/qa-review/scripts/ledger.py stop     --task-id BOARD-005 --reason "..."
python3 .kilo/skills/qa-review/scripts/ledger.py status   --task-id BOARD-005
```

`next-round` refuses to open round 4.

**Stop conditions** — the loop stops at whichever comes first:

| Stop condition | What happens |
|---|---|
| Round cap reached (3 rounds, row still failing) | Row moves to `Blocked` with a summary of what was tried and the question the human must answer. No fourth round. |
| A critical path is red (money, data loss, auth, security) | Row is `Blocked` immediately. Never retried silently. |
| The same fingerprint is filed twice | The existing row is escalated to `Blocked` rather than a new one opening. |
| The human says stop | Row is `Blocked` with the reason recorded in the ledger's stop reason. |

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
