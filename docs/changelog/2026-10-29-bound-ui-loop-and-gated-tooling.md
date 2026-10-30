# Bound the UI critique loop and gate the UI tooling

**Date:** 2026-10-29
**Branch:** `feat/live-board-viewer-html-dashboard-with`
**Boards:** BOARD-008, BOARD-009

## The loop that was not a loop

The UI critique → fix cycle had no stop condition and no way to recognise a repeat. A critic could
raise the same complaint, the builder could "fix" it, and the next round could raise it again,
forever.

Three rules close it:

- **The loop is capped at 3 rounds.** Round 3 is the last. When it still fails, the row moves to
  `Blocked` with what was tried and the question the human needs to answer.
- **A repeat finding is not a new finding.** Every finding carries a fingerprint. `board.py add`
  refuses a second row with a fingerprint that is already open and names the existing row, so the
  repeat escalates the existing row to `Blocked` instead of opening another.
- **A ledger carries the state.** `docs/reviews/<task-id>-ledger.md` records the round, the
  findings, the Fix rows, the merges, and the stop reason. It is the only state carried between
  rounds — each round is reviewed by a **fresh** reviewer, because a reviewer that watched the last
  edits grades intent, not pixels.

`ledger.py` enforces all of it: `next-round` refuses past the cap, `finding` records a filed
finding, `merged` records a landed fix, `stop` records why it stopped.

## The Playwright that was already there

The previous pass concluded Playwright was missing and hand-built its own browser client to
drive a browser. That was built on a false premise.

The devcontainer installs `@playwright/mcp` globally, which brings `playwright` and
`playwright-core` with it, plus system chromium at `/usr/bin/chromium` and
`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`. Playwright was installed the whole time — the check that
said otherwise resolved from a directory with no `package.json`, and Node does not search inside
another package's nested `node_modules`.

Two fixes:

- **`browser-review.mjs` resolves Playwright properly** — the project's own copy first, then the
  global install (via `NODE_PATH`, `npm root -g`, and the well-known path), then it exits 2 with a
  message naming both places it searched. It launches `/usr/bin/chromium` when Playwright has no
  downloaded browser. The hand-rolled browser client is gone.
- **The Playwright MCP is configured in `kilo.jsonc`**, so agents get the interactive browser tools
  — navigate, snapshot, click, read the console. They were installed but never wired up, which is
  why the agent reached for bash.

The rule is now explicit: **the MCP for investigation, `browser-review.mjs` for evidence.** The
script produces the artifact set, the per-scheme counts, and the summary the verdict depends on.
Ad-hoc browser commands are not acceptable evidence. If the script cannot do something a review
needs, extend the script.

## What the script gained

- `--scheme light|dark|both` — and each scheme gets **its own directory**, so the dark pass no
  longer overwrites the light pass's console log.
- `--component <selector>` — cropped element screenshots.
- `--compare <dir>` — before/after sheets, matched per scheme, never light against dark.
- `--label <slug>` — round 0, 1, 2 naming, so rounds can be compared.

## Verification discipline

The reason the loop ran for an hour was not the loop rules — it was three habits:

1. **A verification must yield a binary signal.** A check that cannot return pass or fail in one
   attempt is not a check. Report it as a limitation; do not iterate on a measurement.
2. **Two attempts per check, then report the blocker.** A third attempt at the same failing check
   is a loop, not diligence.
3. **Never mutate the subject of a verification.** Test data goes in a copy or a temp directory.

These are now in `AGENTS.md` §A7, for the architect and every builder.

## Known

The board viewer serves a 404 for `/favicon.ico`, which the QA capture reports as a console error.
It is a dev tool and the finding is accepted as cosmetic.
