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

Before reporting, apply `AGENTS.md` §B11's handoff checkpoint policy: commit task changes locally
on the worktree branch, including a `wip` checkpoint when unfinished or blocked. Report the commit
SHA and diff command alongside the files you wrote, units documented and skipped, and mode used.
This checkpoint does not bypass verification or human-merge gates.
Apply §B11's merge-guidance gate: recheck the live worktree and board. Never provide a merge
command before finished, verified, reviewed, committed, clean `Pending Merge` work. Otherwise
provide only review/diff commands and blockers, with no manually added merge or teardown command.
