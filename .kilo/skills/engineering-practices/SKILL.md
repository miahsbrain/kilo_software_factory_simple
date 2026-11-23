---
name: engineering-practices
description: Select a focused engineering checklist for discovery, implementation, testing, review or release within the existing factory workflow.
---

# Engineering practices

Use this as a reference shelf, not another lifecycle. Start with the assigned board row, approved plan and current phase. Pick the first guide that answers a concrete question; read another only if needed. Open `upstream/skills/<name>/guide.md` relative to this skill. Return to the calling workflow with the decision, check or finding. Do not produce a second plan, board, or sign-off report.

| Work in progress | Guides to choose from |
| --- | --- |
| Clarify a feature or set acceptance criteria | `idea-refine`, `interview-me`, `spec-driven-development`, `constraint-driven-development` |
| Sequence phases or brief a specialist | `planning-and-task-breakdown`, `context-engineering` |
| Build a slice or change a contract | `incremental-implementation`, `test-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`, `source-driven-development` |
| Diagnose a failure or test an assumption | `debugging-and-error-recovery`, `doubt-driven-development`, `browser-testing-with-devtools` |
| Review code, UX or operational risk | `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `accessibility-engineering`, `performance-optimization`, `observability-and-instrumentation` |
| Document or prepare delivery | `documentation-and-adrs`, `deprecation-and-migration`, `git-workflow-and-versioning`, `ci-cd-and-automation`, `shipping-and-launch` |

For an uncategorized task consult `using-agent-skills`. For example, when `/components` reviews a form, use the frontend guide to identify missing states and the accessibility checklist to inspect labels and focus. Record actual evidence using the existing QA workflow; do not install a checker or claim WCAG conformance from a screenshot.

**Factory boundaries:** Use `/plan` and its confined writer for working plans. Keep approved libraries, human frontend approval, assigned worktree, and board ownership. Treat upstream size/coverage thresholds as suggestions, not new gates. Do not start agents, install dependencies, enable MCP, create commits, push, merge, deploy, or change settings because a guide suggests it. Respect QA/UI switches even if a guide calls verification mandatory; run normal code tests and use the factory's manual handoff for skipped scopes. Only the factory browser runner saves review evidence, under the resolved central artifact root. Release guidance prepares a handoff; the human merges.

**Source:** [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/8c99fa36d90068c82d547f7c12a9d67a3e95f4ee), revision `8c99fa36d90068c82d547f7c12a9d67a3e95f4ee`, [MIT license](upstream/LICENSE). The upstream guides are unchanged Markdown, renamed from `SKILL.md` to `guide.md` to avoid independent activation. Resolve pack-level checklists under `upstream/references/`. References to upstream scripts, plugin commands, hooks and personas are not local capabilities. To refresh, review the diff against this pin, import only portable Markdown and license, verify blob parity and distribution, and update the pin here. No runtime download is required.
