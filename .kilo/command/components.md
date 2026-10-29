---
description: Build the component factory and its gallery page, then ask the user to approve the visual language
---

This is the **frontend UI gate** from `AGENTS.md` §A7. Run it before building any screen.

1. **Read** `docs/UI-UX.md` §1–§4 and the app scope's `AGENTS.md`. Confirm the approved visual
   language from the decision sheet (typography, accent, radius, spacing, density, tone). If it
   is not settled, run the decision gate first (`/decide`).
2. **Build the base components** in the app scope: Button, Input, Select, Checkbox, Dialog,
   Table, Card, Badge, Tabs, Toast, Navigation — plus the design tokens. One clear responsibility
   per file; named by domain/layer.
3. **Build the gallery route** that renders every component, every variant, and every state
   (default, hover, focus, active, disabled, loading, error) — plus edge-case content: longest
   realistic label, empty label, long email, numeric overflow. Light and dark when dark mode is
   in scope. Exclude the route from production builds.
4. **The gallery imports the same module paths the screens use.** No forked copy. The registry
   is strictly typed against the component props so an unlisted variant fails type-checking.
5. **Verify**: the gallery renders, the verification command from `docs/STACK.md` passes, and
   the screenshots cover desktop (1440×900) and mobile (390×844).
6. **Ask the user to look at the gallery.** Give the local URL or the path to open. Wait for
   approval or requested changes. Do not build screens in the same pass.
7. **Record the approval** in `docs/UI-UX.md` §6 (replace the assumptions with the approved
   values) and in the changelog. Then screens may be built, using only approved components.
