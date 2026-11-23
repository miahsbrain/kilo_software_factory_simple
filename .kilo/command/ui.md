---
description: Review UI evidence or hand over a manual test checklist for a board or feature
---

Follow `.kilo/skills/qa-review/SKILL.md` for focused behavior checks and the existing `browser-review.mjs` capture. Use the original assigned workspace and shared evidence; reviewers do not modify application source.

For `/ui checklist <board ID or feature>`, follow the skill's **Manual checklist** section and return the artifact link without launching the browser. During a normal review, use that same handoff if any criterion is inaccessible, even if other checks passed.

Before delegating and in each specialist, check `worktree.py reviews status` from the assigned Git root. Run automated QA only if `qa` is true; independently delegate critique only if `ui` is true. With QA off, use existing evidence only for critique, never fresh capture. Invalid or unreadable policy means both scopes are manual. At completion link the manual checklist for every skipped scope, even without a blocker; no implied pass or lane change.

For authorized saved evidence, run only `browser-review.mjs` from the assigned Git root into its ignored `artifacts/`. Playwright MCP is disabled by default; no alternate ad-hoc saving. Use `--human-requested-manual-capture` only for a capture explicitly requested by the user. After the gallery, consolidate findings from enabled reviews once, fix meaningful defects and recheck within policy. A proven harmless development-only favicon failure is nonblocking; preserve raw evidence and do not ignore auth, script, or API failures. Report verified outcomes and unverified criteria honestly.
Check the board for an explicit manual approval covering the same deliverable and revision before requesting that review again. Report independent defects to the coordinator; do not convert review evidence into a blanket QA pass.
