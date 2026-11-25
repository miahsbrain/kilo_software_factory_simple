---
description: Build or refine reusable components needed by the frontend flow
---

Use `engineering-practices` for the frontend component and accessibility guides. Apply the relevant checks to the chosen library and actual flow; keep the existing gallery and human approval gates.

If an app has an existing style, ask whether to keep it or do a complete redesign unless the user already specified the direction. Develop reusable components before screens using Tailwind CSS or a supported, stack-compatible UI library such as shadcn/ui, styled to the chosen visual language and theme. Do not limit choices to libraries already installed; obtain authorization before new dependency installation. Reuse suitable components without preserving unwanted styling and cover relevant interaction/accessibility states.

Present the initial component gallery, then review it through `/factory-ui`, which applies the qa-review skill's **Review switches**. Fix meaningful findings and recheck within policy, then compose screens from those components. Keep normal tests and frontend-flow approval before backend work; label fixtures clearly. Do not require a new gallery for every screen.
