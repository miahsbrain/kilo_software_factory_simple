---
description: Read the whole codebase and write the application memory map
agent: docs-writer
---

Write the application memory map.

1. **First run in a session:** read the entire codebase of every unit listed in
   `docs/PROJECT_STRUCTURE.md`. Later prompts: refresh what changed, unless the user asks for a
   full re-read.
2. Write `docs/handover/<unit>.md` for each unit and `docs/handover/README.md` as the global
   index, in the structure the agent file specifies.
3. Update `docs/PROJECT_STRUCTURE.md` only if a unit is missing from it.

Report the files you wrote, the units you documented and skipped, and the mode you used.
