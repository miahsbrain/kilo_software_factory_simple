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

## Shared feature checklist

After ideation, turn the agreed feature scope into one implementation checklist before delegating work. The coordinator keeps it at `docs/implementation_plans/<lead-board-id>-<feature>.md` in the **owning primary control checkout**, beside its live board. For factory work use the factory control; for product work use the product control. Do not resolve this path against a service or linked worktree. Create the directory on first use; first confirm the destination is within the control root, has no symlink components, is ignored by Git, and `git ls-files -- docs/implementation_plans` is empty. Do not force-add, copy into each repo, or overwrite an existing plan on resume.

Use the maintained writer for all plan creation and updates, not direct file edits. From the owning control Git root or its linked control worktree root, pass the complete Markdown on stdin. Use a stable key, not a path or extension. Feature plans use the lead board ID; other plans can use a descriptive key without a board ID. Use the printed absolute path for assignments. Read the current file before updating so existing decisions, checks and evidence are preserved. A refused write is not permission to save elsewhere.

```bash
python3 .kilo/skills/plan/scripts/plan.py create BOARD-123-order-cancellation < draft.md
python3 .kilo/skills/plan/scripts/plan.py update BOARD-123-order-cancellation < revised.md
python3 .kilo/skills/plan/scripts/plan.py create rollout-audit < audit.md
```

Use only the phases the feature needs. For example:

```markdown
# BOARD-123: Order cancellation
Outcome: Customers can cancel their own pending orders. Shipped orders are out of scope.
## Phase 1: Frontend (web, BOARD-123)
- [ ] Show Cancel on a pending-order fixture. Verify the approved confirmation and error states.
## Phase 2: API (orders-api, BOARD-124; after flow approval)
- [ ] Allow only the owner to cancel a pending order. Verify that a shipped order stays unchanged.
## Final verification (web + orders-api)
- [ ] Cancel a disposable pending order from the UI. Reload and confirm it still shows Canceled.
```

Include dependencies, affected repo IDs, linked board IDs, acceptance criteria, and unresolved decisions. Put the same control-relative plan path in each involved board row's Notes. Give each implementer its resolved path, assigned phase and scope. Specialists read it before work and on resume, then report results or blockers. The coordinator alone updates it, recording evidence next to each verified checkbox. At closeout reconcile every phase and cross-repo outcome; keep unverified items open. A plan is not approval, a board transition, or a replacement for durable decisions or the manual tester checklist in `artifacts/reviews/`. Ignored plans are local to this clone, not shared by Git across machines.

Plan new products or substantial features around the user's actual task. Read relevant existing requirements and decisions first. Ask concise, grouped questions only about missing choices with material consequences; do not turn routine details into approval gates.

1. Describe the user, outcome, scope, core flow, and checkable acceptance criteria.
2. For new apps and user-facing features, plan a frontend flow with clearly labeled fixtures for user approval before backend/API implementation. Backend-only maintenance skips unrelated frontend work.
3. Record material approved architecture, security, data, cost, and integration choices in `docs/DECISIONS.md`; keep unresolved decisions explicit. Hand off an approved service map in product docs before bootstrap: each full NAME, explicit ROLE, `apps/<full-name>` root, responsibility/stack and separate/project Git ownership. Ask actual unknown decisions. Check that a multi-service product is not collapsed into one product-named folder: a planned React frontend plus Python API uses sibling `apps/camera-shop-frontend` and `apps/camera-shop-api`, not nested role folders. An approved single runtime can use one role-named service; never infer extra services from technology or names alone. Bootstrap each exact approved name with `bootstrap.py app <product-role> --role <role> --git separate|project`; roles are arbitrary safe kebab-case, including multiword roles. Metadata-only backend bootstrap (.gitignore/Git/manifest) may precede flow approval, but not backend framework source, dependencies, routes, persistence or integration (except backend-only maintenance). Define contracts when backend work is ready, informed by the approved flow.
4. Put a concise sequence in `ROADMAP.md` and checkable work units on the board through its script. Reuse assigned workspaces and suitable existing code; use short specialist assignments when useful.
5. Include the initial reusable-component gallery, meaningful fixes and rechecks before screen composition, and essential documentation updates. Plan review according to `worktree.py reviews status` at execution, checked before delegation and in the specialist: QA and UI critique are independent. With QA off, critique uses existing evidence only; invalid policy means manual review. Keep normal code tests and plan a linked manual QA/UI checklist at completion for every skipped scope, not a pass or lane transition. Do not require a new gallery for every screen.

Keep product requirements in the project's `DOMAIN.md` and relevant docs, never in the factory. Use reference material only when it helps the task, not as a compulsory template or separate policy. The root working agreement governs.

Reference material derives from Jeffallan's MIT-licensed `feature-forge` and `architecture-designer` skills (https://github.com/Jeffallan/claude-skills, copyright 2025 Jeffallan); research references derive from MIT-licensed obra/superpowers (Jesse Vincent).
