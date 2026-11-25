---
description: Plan a product or substantial feature around the user flow
argument-hint: <product or feature>
---

Plan $ARGUMENTS. Use `engineering-practices` for discovery or task-breakdown guidance when useful; keep the factory plan skill and its writer as the sole planning workflow. Claude Code's plan mode is fine for researching read-only before you propose, but its plan is not a substitute for the documents, board rows and shared checklist this command produces.

Publish the approved working checklist through the plan skill's `scripts/plan.py` writer. Pass a stable key and Markdown on stdin; link the returned path rather than writing a second plan in a service worktree.

Load `.claude/skills/plan/SKILL.md`. Read relevant existing context, resolve material unknowns, and produce an ordered plan with checkable outcomes. For new apps and user-facing features, start with the frontend flow and user approval, then backend/API implementation and integration. Keep product documents in the project repository, not the factory.

Before bootstrap, hand off the approved service map in product docs: each full NAME, explicit ROLE, sibling `apps/<full-name>` root, responsibility/stack and separate/project Git ownership. Ask actual unknown decisions; check that a multi-service product has not collapsed into one product-named folder. A planned React frontend plus Python API means, for example, `apps/camera-shop-frontend` and `apps/camera-shop-api`, not nested role folders. Do not infer services from technology alone or force splits for an approved single runtime. Metadata-only backend bootstrap may precede flow approval; backend framework source, dependencies, routes, persistence and integration may not (except backend-only maintenance).
