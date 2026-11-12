---
description: Plan a product or a large feature before any code is written — discovery interview, requirements, architecture, ordered plan, decision gate
---

Run the plan skill. This command is a shortcut for the procedure in
`.opencode/skills/plan/SKILL.md`; the rules in `AGENTS.md` §A4, §A6 and §B4 are the contract.

**Load the discoverable `plan` skill**, or read it by path:
`.opencode/skills/plan/SKILL.md`, plus only the reference files a phase needs, all under
`.opencode/skills/plan/references/`: `interview-questions.md`, `specification-template.md`,
`ears-syntax.md`, `acceptance-criteria.md`, `system-design.md`, `architecture-patterns.md`,
`database-selection.md`, `adr-template.md`, `nfr-checklist.md`.

**Where it applies.** The plan skill plans a *product*: an empty or new project, or a large
feature that needs a plan before it is built. It writes into documents a project owns —
`DOMAIN.md`, `ROADMAP.md`, `docs/BUSINESS-LOGIC.md`, `docs/DECISIONS.md`, `docs/RISKS.md`,
`docs/STACK.md` — and into the board. A project that does not have them yet gets them from
this run. In the factory repository those product documents do not
exist; a harness change goes through the decision gate instead (`/decide`), and the rows it
produces are built in a worktree.

1. **Read the current state first.** `DOMAIN.md`, `ROADMAP.md`, `docs/DECISIONS.md`,
   `docs/STACK.md`, `docs/RISKS.md` and the board. A decision that is already approved is
   followed, not reopened; existing code is reused, not reinvented (§B6).
2. **Phase 1 — Discover.** Interview the user as a senior technical co-founder. Ask 3–6
   questions per batch with the `question` tool, grouped by topic, highest-leverage and most
   ambiguous first. Reflect the understood decisions in one or two sentences after each batch.
   Flag conflicts instead of reconciling them silently. When the user does not know, propose a
   labelled `ASSUMPTION`, record it, and continue. For a feature that spans several layers,
   launch `subagent` subagents before the interview so it starts from facts.
   **Output:** requirements and product scope → `DOMAIN.md`.
3. **Phase 2 — Requirements.** Write the user value, the business goals and the acceptance
   criteria. Every functional requirement is EARS (`When <trigger>, the <system> shall
   <response>` and its siblings); acceptance criteria are Given/When/Then and checkable.
   **Output:** business rules → `docs/BUSINESS-LOGIC.md`; the specification → `DOMAIN.md`;
   checkable criteria → the spec and the board rows.
4. **Phase 3 — Architecture.** Design the component shape, the patterns, the data store, the
   failure modes and the operational cost. Every significant decision becomes one append-only
   row in `docs/DECISIONS.md` in this repository's ADR format. Run the NFR checklist — scale,
   performance, availability, security, observability, cost, compliance, accessibility.
   **Output:** decisions → `docs/DECISIONS.md`; risks → `docs/RISKS.md`; stack and commands →
   `docs/STACK.md`.
5. **Phase 4 — The plan.** Turn the approved design into an ordered checklist. A shared
   contract, schema or file layout is settled on the base branch before the rows that depend on
   it open. Each row carries acceptance criteria, a risk level and `Blocked by`, and is created
   with the board script — never by hand.
   **Output:** the checklist → `ROADMAP.md`; one row per unit → local SQLite via `board.py`.
6. **Phase 5 — The decision gate.** Put the implementation decisions in front of the user as one
   batched decision sheet: the decision, the recommendation, the alternatives with a one-line
   trade-off, the consequence, and the default marked `ASSUMPTION`. One reply answers all of
   them. Nothing is built and no worktree opens while a decision is open. `/decide` runs this
   gate on its own.
   **Output:** the approved decisions → `docs/DECISIONS.md`; the open assumptions → the
   handover's Open Questions.
7. **Hand off.** With the decisions approved, the rows are built in the normal loop: a worktree
   per row, the builder delegated with the decisions stated verbatim, QA plus the UI/UX critique
   (`/ui`), the unslop pass (`/unslop`), then the human's merge.

Report in this order: what was done, what is proven, what is not done and why, next action.
