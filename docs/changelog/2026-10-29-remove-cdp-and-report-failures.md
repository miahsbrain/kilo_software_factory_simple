# Remove CDP from the capture path and report failures instead of routing around them

**Date:** 2026-10-29
**Branch:** `chore/remove-cdp-and-report-failures`
**Boards:** BOARD-012

## One driver owns the evidence

`browser-review.mjs` drives Playwright. It never opened a second driver, and now no document
offers one either: `AGENTS.md` §B4.2, `.kilo/command/ui.md`, `.kilo/agent/qa-reviewer.md`, and
`.kilo/agent/ui-critic.md` described a `--chromium` fallback "over CDP" that the script did not
have. The wording is now the behaviour: a binary path handed to Playwright's launch.

`--chromium <path>` is a plain path to a chromium binary. It overrides `PLAYWRIGHT_CHROMIUM_PATH`.

## The browser resolution order

Highest priority first:

1. `--chromium <path>`
2. `PLAYWRIGHT_CHROMIUM_PATH`
3. the browser Playwright downloaded
4. the system chromium: `/usr/bin/chromium`, `/usr/bin/chromium-browser`, `which chromium`

The order changed. The downloaded browser used to win over the env var, while `SKILL.md` and
`docs/STACK.md` said the env var overrides. The new order makes the docs true. A working
environment is unaffected: the container sets `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` and installs
`/usr/bin/chromium`, so the same binary is launched either way.

## A missing browser is reported, not installed

When no chromium is found, the script exits 2 and prints where it looked:

```
browser-review: no chromium browser was found.

Searched:
  - the browser Playwright downloaded for /path/to/project
  - $PLAYWRIGHT_CHROMIUM_PATH
  - --chromium /nonexistent/chromium
  - /usr/bin/chromium
  - /usr/bin/chromium-browser
  - `which chromium`

This script does not install a browser and does not fall back to another driver.
Ask the user to install one or to point at an existing binary, then re-run:
...
```

A binary that exists but fails to start gets its own message: the path, the underlying error,
and the same instruction. Exit code 2 in both cases.

The script never runs an install command, and it never falls back to another driver. Installing a
browser is the user's decision.

## The report-first rule

`AGENTS.md` §B6.2, the five agent files, and the QA skill now carry the same rule:

1. The exact command, the exact error, and the exit code.
2. What the failure means, in one line.
3. Your recommendation, with the options and their trade-offs.
4. Then stop, and let the user or the architect decide.

No script, helper, or tool to work around a failure. No installing a missing dependency — a
browser binary, a package, a system tool — on your own initiative. No switching tools unless the
user says so. A missing browser, package, or system tool is reported, not installed, replaced, or
emulated.

`AGENTS.md` §A6.2 gained the matching trigger: a command, capture, or test that failed for an
environmental reason is a question for the user.

## The story behind the rule

An agent needed browser automation and built its own browser client while Playwright sat
installed in the global npm tree. It never checked and never asked. That is why §B6.1 exists.

The story stays, reworded. The five agent files, `AGENTS.md`, and ADR-038 described the client
with a protocol name; they now say "its own browser client". The point is the failure, not the
protocol.

## One change to the review rule

`AGENTS.md` §B4.2 used to say "if the script cannot do something the review needs, extend the
script". That let a reviewer patch a project tool mid-review, with nobody reviewing the patch.
It now says: say what is missing and propose the change — a change to a project tool is a
reviewed change, not a silent patch mid-review. The same line in `.kilo/command/ui.md`,
`.kilo/command/run.md`, `.kilo/agent/qa-reviewer.md`, `.kilo/agent/ui-critic.md`, and the QA
skill matches.

## Verification

```
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:9 --route / \
  --project /tmp/kilo/no-such-project --chromium /nonexistent/chromium
```
Exit 2, with the message above and `--chromium /nonexistent/chromium` in the searched list.

```
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:18099 --route / \
  --scope factory --task-id BOARD-012 --project /tmp/kilo/no-such-project --viewports 1440x900
```
Exit 0, artifacts under `artifacts/factory/qa/2026-10-29/BOARD-012/`, `browser_executable`
`/usr/bin/chromium`.

## Known

- `docs/BOARD.md` still describes the removed CDP client on the BOARD-009 row. The board has one
  writer — the orchestrator — so that wording is left for it to correct.
