---
description: Implement and verify one assigned board task
---

Read the row and relevant context. Use its assigned workspace and existing lifecycle tools; keep the board current through the coordinator. Implement the smallest sound solution, using specialists through short explicit assignments when useful. For new apps and user-facing features, get frontend-flow approval before backend work; fixtures must be labeled.

All FEATURE implementation uses an assigned linked worktree, never the primary checkout, regardless of optional maintenance policy. Explicitly assigned features may share the same worktree/branch with `worktree.py create --board NEW --reuse EXISTING --repo ID`; preserve scope/ownership and do not auto-switch branches or change permissions/mode. Project-tracked apps use control's worktree; separate apps use their mapped repo's worktree. Initial scaffolding/bootstrap is exempt: bootstrap makes the authorized initial commit only in new project/separate-service repositories it creates. Feature implementation then uses an assigned linked worktree; never auto-commit an existing repository.

Run focused checks appropriate to the change. For UI work, use `/ui` to share capture evidence with concurrent independent critique and read-only unslop tasks. Consolidate findings once, fix meaningful defects, and recheck affected behavior. Update essential docs and report changes, actual checks, and limitations. No unauthorized staging, commits, destructive operations, merge, or push. Use the lifecycle handoff when ready for human review.
