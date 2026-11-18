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

Plan new products or substantial features around the user's actual task. Read relevant existing requirements and decisions first. Ask concise, grouped questions only about missing choices with material consequences; do not turn routine details into approval gates.

1. Describe the user, outcome, scope, core flow, and checkable acceptance criteria.
2. For new apps and user-facing features, plan a frontend flow with clearly labeled fixtures for user approval before backend/API implementation. Backend-only maintenance skips unrelated frontend work.
3. Record material approved architecture, security, data, cost, and integration choices in `docs/DECISIONS.md`; keep unresolved decisions explicit. Define contracts when backend work is ready, informed by the approved flow.
4. Put a concise sequence in `ROADMAP.md` and checkable work units on the board through its script. Reuse assigned workspaces and suitable existing code; use short specialist assignments when useful.
5. Include the initial reusable-component gallery, focused QA and UI critique against shared evidence, meaningful fixes and rechecks before screen composition, and essential documentation updates. Do not require a new gallery for every screen.

Keep product requirements in the project's `DOMAIN.md` and relevant docs, never in the factory. Use reference material only when it helps the task, not as a compulsory template or separate policy. The root working agreement governs.

Reference material derives from Jeffallan's MIT-licensed `feature-forge` and `architecture-designer` skills (https://github.com/Jeffallan/claude-skills, copyright 2025 Jeffallan); research references derive from MIT-licensed obra/superpowers (Jesse Vincent).
