---
description: Read assigned units and write their application memory map
agent: docs-writer
---

Write the application memory map.

1. Read assigned local `AGENTS.md` and explicitly permitted shared governance/contracts. Reuse
   the original repo-specific workspace set, never create a documentation worktree. Optional
   mode changes workspace requirements only, not assignment or secret protections.
2. **First run:** read the assigned units, not every unit by default. Later prompts refresh the
   changed files unless the user explicitly requests a full assigned-unit re-read.
   Write `docs/handover/<unit>.md` for assigned units and update `docs/handover/README.md`
   without removing unassigned inventory, in the structure the agent file specifies.
3. Update `docs/PROJECT_STRUCTURE.md` only if a unit is missing from it.

Report the files you wrote, the units you documented and skipped, and the mode you used.
