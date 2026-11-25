---
description: Review UI evidence or hand over a manual test checklist for a board or feature
argument-hint: [checklist] <board-id or feature>
---

Review or hand over $ARGUMENTS. Follow `.claude/skills/qa-review/SKILL.md`: its **Review switches** gate the work, its **Browser** section picks the integrated browser or `browser-review.mjs`, and its **Manual checklist** section is the handoff. Use the original assigned workspace and shared evidence; reviewers do not modify application source.

Delegate automated QA to the `qa-reviewer` subagent only when `qa` is true, and critique to the `ui-critic` subagent only when `ui` is true. Each rechecks the switches itself.

For `/factory-ui checklist <board ID or feature>`, follow the **Manual checklist** section and return an absolute workspace link to the validated guide without opening a browser. During a normal review, use that same handoff if any criterion is inaccessible, even if other checks passed.

Use the `engineering-practices` accessibility or performance guide for questions the evidence can actually answer; neither guide overrides the review switches. For a requested accessibility scan, use the runner's `--axe` flag and report failed or incomplete scans separately from observed violations. Do not turn a checklist-only request into a capture. Use `--human-requested-manual-capture` only for a capture the user explicitly requested.

A proven harmless development-only favicon failure is nonblocking; preserve raw evidence and do not ignore auth, script or API failures. Check the board for an explicit manual approval covering the same deliverable and revision before requesting that review again. Report independent defects to the coordinator; do not convert review evidence into a blanket QA pass.
