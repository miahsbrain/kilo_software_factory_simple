# A documentation agent owns the application memory map

**Board:** BOARD-002 · **Branch:** feat/add-a-documentation-agent-that-writes · **Date:** 2026-10-30

## What changed

A new agent, `docs-writer`, reads the codebase and writes the memory map of the whole
application. `/handover` routes to it, so one command has one owner. The map lives in
`docs/handover/`: `docs/handover/README.md` is the global index, `docs/handover/<unit>.md` is one
file per application. `docs/HANDOVER.md` stays as the factory's own handover.

## Why a dedicated agent

A handover written from memory of a system drifts: the writer re-derives what it already knew
instead of what the code says, and the drift is invisible to the reader. Giving the map one
owner — an agent whose job is to read the code and write it down — makes the map reproducible.
The same owner also means the map has one shape: every application gets the same fourteen
sections, and every unit appears in the index.

## Why the units come from `docs/PROJECT_STRUCTURE.md`

The deployable units are the `apps/<name>` scopes that own their own `AGENTS.md`. That list
already lives in `docs/PROJECT_STRUCTURE.md`, which the architect keeps current (§A1). The agent
reads the list from there instead of hard-coding one, so a fourth scope appears in the map the
moment it is added to the structure file. A unit missing from that file is a finding: the agent
adds it and says so.

## Why the first run reads everything

A map is only correct if it was built from the whole unit. The first run in a session reads every
file that defines behaviour — source, config, schema, migrations, tests, entry points — and lists
what it skipped and why. Later prompts refresh only what changed, found with `git log --oneline`
and `git diff` on the unit. The agent says which mode it used in its report, so a reader knows
whether the map is a full read or a refresh.

## Why pure / reactive / effectful

The classification that matters to a reader is not what a file is called but whether it can be
called without the outside world. `pure` means the same input gives the same output. `reactive`
means it reads or writes state — a signal, store, observable, context, cache. `effectful` means it
touches the outside world — database, network, filesystem, env, clock, randomness, logging, shared
state. A function that both holds state and does I/O is `effectful`, with the state noted in the
row. Where the kind is unclear, the row says why instead of guessing silently.

The three kinds are what make the map actionable: they mark the seams where a pure core meets an
effectful edge, so a reader can see where the boundaries of the system are without reading every
file.

## Impact

- `/handover` runs the `docs-writer` agent instead of the previous inline doc-refresh prompt.
- New folder `docs/handover/` holds the map: the global index and one file per unit.
- `AGENTS.md` records the agent in the §A7 team table, the `docs/handover/` folder in the §A10
  table, the per-application map in the §B1 documentation table, and the parallel in §B2.
- No change to the build, QA, review or merge lanes. `docs/BOARD.md` is still written by the
  orchestrator alone.
