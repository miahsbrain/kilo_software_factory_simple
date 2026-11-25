---
description: Refresh concise documentation for the assigned change
argument-hint: <board-id>
---

Delegate this to the `docs-writer` subagent with the board ID ($ARGUMENTS), the assigned workspace path and the changed areas, then relay its report.

The subagent reads the changed areas in the assigned workspace and refreshes relevant handover notes, run instructions, decisions and known limitations. It preserves unrelated documentation, updates the directory map when paths change, and describes current reality without exhaustive symbol inventories. It reports changed files and what was not checked.

For every tester handoff, follow the qa-review skill's **Manual checklist** format (board ID, one `Changed:` sentence, then `- [ ]` tester actions with expected results), run its `--manual-guide` check, and return an absolute workspace link to the validated file in the owning project's primary control `artifacts/reviews/`. Do not substitute an inline checklist or a status narrative. Link it for every skipped review scope too; a checklist is not a pass or a lane transition.
