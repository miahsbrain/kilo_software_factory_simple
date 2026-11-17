---
name: plan
description: Plans and architects a product before any code is written — runs the discovery interview, writes the requirements and the specification, chooses the architecture, and turns the result into an ordered implementation plan. Use when the project is empty or new, when a large feature needs a plan before it is built, or when the user asks for a spec, a requirements workshop, an architecture design, a decision record, or an implementation plan. The output lands in the repository's own documents: DOMAIN.md, ROADMAP.md, docs/DECISIONS.md, docs/RISKS.md, docs/STACK.md and the board.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.0.0"
  domain: workflow
  triggers: plan, planning, requirements, specification, discovery, architecture, ADR, design
  role: specialist
  scope: design
  output-format: document
  upstream:
    - feature-forge
    - architecture-designer
  research:
    - obra/superpowers
---

# Plan

Plan and architect a product before a line of application code exists.

Merged from two upstream skills by Jeffallan (https://github.com/Jeffallan) — `feature-forge`
(requirements) and `architecture-designer` (architecture) — from
https://github.com/Jeffallan/claude-skills, MIT licensed, © 2025 Jeffallan. Their reference
material is kept intact in `references/`. The two research documents in `references/` are MIT
licensed, © Jesse Vincent, from obra/superpowers.

## Scope

**For:** an empty or new project, and a large feature that needs a plan before it is built.

**Not for:** writing application code, running the build, or a bug fix. A bug fix goes to the
worktree and the board like any other row; this skill is for the work that precedes a row.

## Where the output lands

This skill introduces **no new document type**. Every phase writes into a document the
repository already has.

| Phase | Output | Document |
|---|---|---|
| 1. Discover | Requirements and product scope | `DOMAIN.md` |
| 2. Requirements | Business rules, acceptance criteria | `docs/BUSINESS-LOGIC.md`, the spec inside `DOMAIN.md`, and the board rows when a criterion is checkable |
| 3. Architecture | Decisions, risks, stack | `docs/DECISIONS.md`, `docs/RISKS.md`, `docs/STACK.md` |
| 4. The plan | The implementation checklist | `ROADMAP.md` and one board row per unit of work |
| 5. The decision gate | The approved decisions | `docs/DECISIONS.md`, and the assumption register in the handover's Open Questions |

## The procedure

### 1. Discover

Interview the user as a senior technical co-founder. Ask **3–6 questions per batch**, grouped by
topic, and ask the highest-leverage and most ambiguous questions first — the ones that would
cause a costly rewrite. Never dump the whole set at once.

Use the `question` tool for a question with a finite set of likely answers, and open-ended
follow-ups when the answer is unbounded. `references/interview-questions.md` is the question
bank: PM-hat questions for value and scope, Dev-hat questions for feasibility and edge cases.

For a feature that spans several system layers, launch `Task` subagents **before** the
interview, so it starts from facts instead of assumptions
(`references/pre-discovery-subagents.md`).

Reflect the understood decisions in one or two sentences after each batch. Flag conflicts with
earlier answers instead of reconciling them silently. When the user does not know, propose a
labelled `ASSUMPTION`, record it, and continue.

**Output:** requirements and product scope → `DOMAIN.md`.

### 2. Requirements

Write user value, business goals, and acceptance criteria. Use
`references/specification-template.md` for the shape of the specification and
`references/ears-syntax.md` for the functional requirements — EARS is the syntax for the
requirements inside the specification document, not a separate artefact.

Every functional requirement is EARS:

```
When <trigger>, the <system> shall <response>.
Where <feature> is active, the <system> shall <behaviour>.
The <system> shall <action> within <measure>.
```

Acceptance criteria are checkable, in the Given/When/Then form of
`references/acceptance-criteria.md`. EARS stays inside the specification document; a board row
keeps this repository's own format — `- [ ] criterion — proof`, with the proof a command, a
`file:line`, or a sha.

**Output:** business rules → `docs/BUSINESS-LOGIC.md`; the specification → `DOMAIN.md`; the
acceptance criteria that are checkable → the spec and the board rows.

### 3. Architecture

Design the system: the component shape, the patterns, the data store, the failure modes, the
operational cost. `references/system-design.md` is the design template,
`references/architecture-patterns.md` compares monolith, modular monolith, microservices,
serverless and event-driven, and `references/database-selection.md` compares the data stores.

Every significant decision becomes one row in `docs/DECISIONS.md`, in this repository's ADR
format: `ADR-001`, `ADR-002`, … one line per decision, append-only, with the decision, the
context, the consequence and the date. `references/adr-template.md` holds the reasoning that
goes into that row — the upstream template is the narrative, this repository's row is the
record.

Non-functional requirements are a checklist, not an afterthought:
`references/nfr-checklist.md` covers scalability, performance, availability, security,
observability, cost, compliance and accessibility.

**Output:** decisions → `docs/DECISIONS.md`; non-functional risks → `docs/RISKS.md`; the stack
and its commands → `docs/STACK.md`.

### 4. The plan

Turn the approved design into an ordered checklist. The implementation checklist goes into
`ROADMAP.md`, and every unit of work becomes one board row on `docs/BOARD.md`, with
`Blocked by` carrying the dependency order — a shared contract, schema or file layout is
settled on the base branch before the rows that depend on it are opened.

Each row carries its acceptance criteria, its risk, and its `Blocked by`. The board has one
writer, the orchestrator, so the rows are created with the board script, never by hand.

**Output:** the checklist → `ROADMAP.md`; one board row per unit of work → `docs/BOARD.md`.

### 5. The decision gate

Before anything is built, put the implementation decisions in front of the user as one batched
decision sheet. Each decision names:

1. the decision — one sentence;
2. the recommendation — one option, marked, with why it is the default;
3. the options — two or three alternatives, each with a one-line trade-off;
4. the consequence — what changes if this is picked, and what it costs to reverse;
5. the default if unanswered — stated explicitly, marked `ASSUMPTION` until confirmed.

The user answers once, in one reply. Do not write code and do not open a worktree while a
decision is open. This skill assembles the sheet; `AGENTS.md` §A6 owns the rule.

**Output:** the approved decisions → `docs/DECISIONS.md`; the open assumptions → the handover's
Open Questions.

## Precedence

**Precedence.** Where this skill and `AGENTS.md` disagree, `AGENTS.md` wins: this skill is the
detail, `AGENTS.md` is the contract. The batched interview, the decision sheet and the rule that
nothing is assumed stay where `AGENTS.md` §A4 and §A6 put them.

The two research documents are background reading, not rules: `references/superpowers-research.md`
and `references/superpowers-research-findings.md` explain how another project ran its planning
work. Nothing in them overrides this repository's rules.

## Reference index

| File | What it holds |
|---|---|
| `references/interview-questions.md` | The question bank: PM-hat and Dev-hat questions, and when to use the `question` tool against open-ended follow-ups |
| `references/specification-template.md` | The shape of the specification: overview, functional and non-functional requirements, acceptance criteria, error handling, implementation checklist |
| `references/ears-syntax.md` | The EARS patterns for functional requirements |
| `references/acceptance-criteria.md` | Given/When/Then acceptance criteria, with happy-path, error-case and edge-case examples |
| `references/pre-discovery-subagents.md` | When to launch `Task` subagents before the interview, and what to ask them |
| `references/system-design.md` | The system design template: requirements, components, data flow, deployment |
| `references/architecture-patterns.md` | Monolith, modular monolith, microservices, serverless and event-driven, with trade-offs |
| `references/database-selection.md` | The data store types and what each is good for |
| `references/adr-template.md` | The ADR narrative, mapped onto this repository's one-line `docs/DECISIONS.md` row |
| `references/nfr-checklist.md` | The non-functional requirements checklist: scale, performance, availability, security, observability, cost, compliance |
| `references/superpowers-research.md` | Background research on obra/superpowers. Reading, not rules |
| `references/superpowers-research-findings.md` | The triage findings on that research. Reading, not rules |
