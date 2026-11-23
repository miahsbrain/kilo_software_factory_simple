---
description: Build or refine reusable components needed by the frontend flow
---

If an app has an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Develop reusable components before screens using Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme. Do not limit choices to libraries already installed; obtain authorization before new dependency installation. Reuse suitable components without preserving unwanted styling and cover relevant interaction/accessibility states.

Present the initial component gallery. Check `worktree.py reviews status` before delegating through `/ui`; specialists recheck. Run focused QA only if `qa` is enabled and critique only if `ui` is enabled. With QA off, critique existing evidence only; invalid policy means manual review. Fix meaningful findings and recheck within policy, then compose screens from those components. At completion link the manual QA/UI checklist for skipped scopes even without a blocker. Keep normal tests and frontend-flow approval before backend work; label fixtures clearly. Do not require a new gallery for every screen.
