---
description: Implement and verify one assigned board task
argument-hint: <board-id>
---

Implement board task $ARGUMENTS. `CLAUDE.md` already governs the workspace boundary, worktree assignment and reuse, service registration and artifact locations; this command adds the task flow.

Use `engineering-practices` to select the applicable implementation, contract, testing or debugging guide. Pass the selected guide and the actual acceptance criterion to the assigned subagent; do not run a second autonomous workflow.

For a feature, read the shared implementation plan linked in the board Notes before starting or resuming. Resolve it against the owning primary control checkout, not the current service. Pass its absolute path, phase and acceptance criteria to every implementation subagent. If it is missing, resolve the plan with the coordinator instead of creating a second copy.

Read the row with `board.py show <ID>` and the relevant context, including any scoped manual review evidence, before asking the user to repeat a decision. Use its assigned workspace and existing lifecycle tools; keep the board current through the coordinator. Implement the smallest sound solution, using subagents through short explicit assignments when useful. For new apps and user-facing features, get frontend-flow approval before backend work; fixtures must be labeled.

Follow the exact approved service map from `/factory-plan`: full name, role, sibling `apps/<full-name>` root, responsibility/stack and separate/project ownership. Never infer unapproved services or collapse a planned multi-service product into one folder. Bootstrap with `bootstrap.py app <product-role> --role <role> --git separate|project`; verify the implementation assignment targets that service (control worktree for project ownership, full-name repo ID for separate). Metadata-only backend bootstrap (.gitignore/Git/manifest) may precede frontend-flow approval; backend framework source, dependencies, routes, persistence and integration may not, except backend-only maintenance.

Missing board linkage may be incomplete creation: `worktree.py resume --board ID --repo ID` validates metadata and retries initialization before linking; ambiguous candidates need user selection with `--worktree PATH`. For explicitly assigned current-checkout Fix/Chore/Docs work, check `worktree.py mode status` and run `worktree.py create --board ID --repo REPO --skip-worktree` from that checkout. This read-only preflight grants no permissions and creates no mergeable assignment. Required mode refuses it; adaptive mode still asks for primary edits and refuses primary commits, so use a linked worktree from the outset when the work needs a commit.

Run normal code tests appropriate to the change. Review follows the qa-review skill's **Review switches**; `/factory-ui` delegates to the `qa-reviewer` and `ui-critic` subagents. To see the running app yourself, Claude Code's built-in `run` skill can launch it; saved evidence still comes only from `browser-review.mjs`. Update essential docs and report changes, actual checks and limitations. No unauthorized staging, commits, destructive operations, merge or push. Use `worktree.py handoff --board <ID>` when ready for human review; a review marker clears neither unrelated blockers nor authorization requirements.
