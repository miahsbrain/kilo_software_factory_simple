# Factory changelog

## Unreleased

- The factory now runs on Claude Code. The harness lives in `.claude/`, the working agreement is `CLAUDE.md`, and the workflow commands are `/factory-plan`, `/factory-run`, `/factory-ui` and friends. A guard hook enforces the existing policy on every tool call, so a workspace-mode change takes effect immediately with no restart. Interactive QA uses Claude Code's integrated browser; saved evidence still comes from the browser runner.
- Frontend reviews trace the selected component library from export to screen; all seven specialists now report evidence appropriate to their role.
- The standalone QA reviewer can reuse a dedicated, exact-origin browser session from ignored local files.
- Manual review acceptance resolves the corresponding review blocker without erasing unrelated work. Duplicate findings no longer move a row to Blocked.
- Adaptive mode supports an explicit eligibility check for maintenance in the current checkout without creating a worktree. Feature assignments and protected branches retain their safeguards.

Factory changes do not migrate existing independent projects or switch their saved workspace mode.
