---
description: Read the whole codebase and refresh the handover documentation set
---

Do the "First action on entering a project" flow from `AGENTS.md`:

1. Enumerate every file in the repository and read all files that define behaviour.
   List what you skipped and why.
2. Write/refresh, in `docs/`:
   - `HANDOVER.md` — overview, directory map, entry points, modules/classes/functions with
     **pure vs effectful** markers, data model, state machines and transitions, public API,
     config/env, dependencies, testing, known issues, open questions, document map.
   - `ARCHITECTURE.md` — domain, bounded contexts, mermaid system shape, layers and
     boundaries, key decisions table, cross-cutting concerns, Now/Next/Later roadmap.
   - `BUSINESS-LOGIC.md` — question→answer pairs; each with rule name, plain English,
     technical detail, `file:line` source, edge cases, example.
   - `BOARD.md` — one row per unit of work, current statuses.
3. Update the **Session Notes** at the top of `docs/HANDOVER.md`.
4. Report to the user: what the app is, its entry points, and every file you changed in
   `docs/`. Do not modify application code in this command.
