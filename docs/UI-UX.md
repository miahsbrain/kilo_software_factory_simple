# UI-UX

The visual language of this project: references, anti-slop rules, the component factory gate,
and the QA/UI-review evidence spec.

This document is the source of truth for anything visual. `AGENTS.md` states the rules; this
document holds the detail. Update both when the visual language changes.

---

## 1. Reference galleries

Look at these before inventing a look. They are references, not templates to clone.

### Design systems and component references

| URL | Learn from it |
|---|---|
| https://ui.shadcn.com/ | Code-owned composable components; you own the styling. |
| https://www.radix-ui.com/themes | Accessible primitives + a token/theming example. |
| https://primer.style/product/components/ | Enterprise patterns: data tables, menus, empty states, skeletons. |
| https://polaris.shopify.com/ | Dense admin UI done well. |
| https://m3.material.io/ | Motion, elevation, state layers, tonal color. |
| https://ant.design/ | Component depth, theme algorithm, design values. |
| https://chakra-ui.com/ | Token / recipe / typography model. |
| https://mantine.dev/ | Wide component set, dark mode, RTL, styles API. |
| https://base-ui.com/ | Unstyled, accessible primitives (WCAG 2.2 aligned). |
| https://ark-ui.com/ | Headless state-machine components across frameworks. |
| https://www.untitledui.com/react | Figma-scale component library for app + marketing sections. |
| https://www.designsystems.com/ | Typography, iconography, grid, content strategy guides. |
| https://linear.app/method | Density, tone, restraint — the closest thing to a written design language. |

### Sites with excellent UI (visual reference only — do not copy)

| URL | Learn from it |
|---|---|
| https://linear.app/ | Information density, keyboard-first affordances, restrained color. |
| https://vercel.com/ | Grid discipline, monochrome + one accent, sharp micro-typography. |
| https://stripe.com/ | Layered gradients, generous whitespace, confident type scale. |
| https://www.notion.so/product | Content-first layout, real product screenshots. |
| https://www.raycast.com/ | Dark UI, motion in the hero, product-shot sequencing. |
| https://attio.com/ | Dense CRM UI shown honestly. |
| https://superhuman.com/ | Typographic scale and tone. |
| https://framer.com/ | Canvas and component gallery. |
| https://resend.com/ | Code-first hero, minimal chrome. |
| https://clerk.com/docs · https://supabase.com/docs | Docs information architecture and component references. |

### Imagery and pattern galleries

| URL | Learn from it |
|---|---|
| https://mobbin.com/ | Real shipped product screens and flows — the best pattern source. |
| https://land-book.com/ | Curated site gallery with style/typography filters. |
| https://www.awwwards.com/ | Web craft, motion, typography extremes. |
| https://www.siteinspire.com/ | Editorial selection of the best of the web. |
| https://recent.design/ | Minimal / clean sites. |
| https://flowbite.com/blocks/ | Dashboard, table, and auth block examples. |
| https://daisyui.com/docs/themes/ | Theme token sets (primary/secondary/accent/semantic). |

### Typography

| URL | Learn from it |
|---|---|
| https://vercel.com/font | Geist Sans / Geist Mono — the reference pairing. |
| https://fonts.google.com/specimen/Inter | Neutral UI sans, wide weight axis. |
| https://fonts.google.com/specimen/Manrope | Geometric grotesk with more character than Inter. |
| https://fontshare.com/ | General Sans, Satoshi, Switzer — a Söhne-tier free alternative. |
| https://typescale.com/ | Modular scale builder: ratio, min/max, responsive sizes. |

---

## 2. Anti-"AI-generated UI" rules

Every rule here is checkable in review. A screen that trips several of them reads as generated.

1. **No purple/indigo gradient hero with centered text.** Use a solid surface, one accent, a
   left-aligned heading. At most one gradient, and never behind text.
2. **No meaningless hero copy.** Name the actual job — "Ship a schema migration with a rollback
   plan", not "Welcome to our platform".
3. **No three identical stat cards.** One primary metric in context; a real table or list with
   row density; numbers carry units, timeframes, and a comparison basis.
4. **One accent color, used sparingly.** Accent for primary action and focus; semantic colors
   only for status.
5. **A real type scale.** A documented ratio (1.2–1.333), fixed steps, a line-height per step, and
   a measure of 60–75ch. No ad-hoc `text-2xl` / `text-sm` / `text-xs`.
6. **Two or three radius steps and one elevation scale.** Border beats shadow at low elevation.
   No `rounded-2xl` and `shadow-lg` on everything.
7. **Asymmetry over centered symmetry.** Varied column widths, a clear primary axis, deliberate
   whitespace. Not a `max-w-4xl mx-auto` centered stack.
8. **Real data density.** Tables with sortable columns, secondary metadata, timestamps, and
   empty/loading/error states shown next to the populated state.
9. **Say something specific in empty, loading, and error states.** "No invoices in this range —
   widen the date filter", not "No data".
10. **Icons are functional.** Icon-only controls and recognizable objects only. Consistent stroke
    width and optical size. No icon beside every label.
11. **Not every shape is a pill.** Pills for status and counts, rectangles for controls, sharp
    edges for table cells.
12. **No synthetic imagery or fake testimonials.** Real product screenshots and real quotes with
    role and company, or no testimonials section.
13. **Motion is functional and brief.** 120–200ms for state changes; content appears immediately;
    motion only where it explains a spatial change.
14. **Spacing comes from a scale.** 4/8/12/16/24/32/48/64, one vertical rhythm per section type.
15. **Contrast, focus, and target size are part of the visual language.** Body text ≥ 4.5:1, a
    visible 2px focus indicator, interactive targets ≥ 24×24 CSS px.

---

## 3. The component factory (required before any screen)

**A frontend project builds a component factory before it builds screens.**

### What it is

A set of reusable base components — Button, Input, Select, Checkbox, Dialog, Table, Toast, Card,
Badge, Tabs, Navigation — plus the design tokens they use. Each component is authored once and
reused everywhere.

### The gate

1. Build the base components in a `components/ui` area owned by the app scope.
2. Build a **gallery route** that renders every component, every variant, and every state.
3. Serve it locally (or on a preview URL) and **ask the user to look at it**.
4. Wait for the user's approval. Adjust if they want changes.
5. Only then build the actual screens, using only approved components.

No screen is built before the gallery is approved.

### Gallery structure

```
apps/<scope>/src/<app>/__gallery__/     # route: /__gallery__ (dev and preview only)
├── page.tsx        # renders every section
├── registry.ts     # the single source of truth for components, variants, states
└── sections/       # one file per component
```

- The gallery imports the **same module path the screens use**. No forked copy, no duplicate
  markup.
- The registry is strictly typed against the component's props, so adding a variant to a
  component without adding it to the registry fails type-checking. That is the sync mechanism.
- The gallery is excluded from production builds (guard the route on environment).
- Gallery files live with the component's domain folder, not in one central dumping ground.

### What the gallery must show

- **Variants** — every variant of each component.
- **States** — default, hover, focus, active, disabled, loading, error, read-only. Render them
  explicitly; do not ask the reviewer to hover.
- **Edge-case content** — the longest realistic label, an empty label, a long email, a long
  filename, numeric overflow. Content edge cases matter more than variant count.
- **Light and dark** for every section, when dark mode is in scope.
- **Accessibility states** — error + hint text, disabled vs. read-only, loading with a visible
  label.

### What approval means

Approval records the decisions: radius, border, type scale, accent color, spacing scale, and the
approved states. Those go into the design tokens and into this document. A screen that deviates
from the approved gallery is a **review finding**, not a new decision.

### When Storybook is justified

Adopt Storybook only when two or more teams consume the components, components need isolated
interaction/a11y tests in CI, designers work from a formal Figma handoff, or there are 30+
components with a variant matrix too large for one hand-written gallery. Otherwise a typed
registry plus one route is cheaper and enforces the same sync rule.

---

## 4. QA and UI/UX review evidence (Playwright)

The QA lane for frontend work produces **evidence**, not assertions.

### Viewport matrix

| Viewport | Size | Purpose |
|---|---|---|
| Mobile | 390 × 844 | Primary mobile layout, tap targets, navigation. |
| Mobile small | 320 × 800 | Overflow and truncation floor. |
| Tablet | 834 × 1112 | Two-column to one-column transitions. |
| Desktop | 1440 × 900 | Default review width. |
| Wide | 1920 × 1080 | Max-width and alignment behavior. |

### What to capture

- Full-page screenshot per route per viewport: `await page.screenshot({ path, fullPage: true })`.
- Component screenshots for each changed component, at desktop and mobile.
- Console errors and failed network requests.
- Accessibility findings (only when `@axe-core/playwright` is already a dependency).

### Artifact layout

```
apps/<scope>/artifacts/qa/<YYYY-MM-DD>/<task-id>/
├── desktop/<route>.full.png
├── mobile/<route>.full.png
├── components/<component>.<viewport>.png
├── console.log
├── network.json
└── notes.md          # what was checked, expected vs actual
```

Commit `notes.md` and small component shots. Keep full-page captures out of git unless the team
wants a visual record — they are large and churn.

### Checks

- **Keyboard focus** — tab through the page, assert a visible focus ring, confirm focus is trapped
  in dialogs and returns to the trigger on close.
- **Contrast and semantics** — body text ≥ 4.5:1; accessible names on every control.
- **Tap target size** — ≥ 24×24 CSS px (prefer 44×44 for touch-primary UI).
- **Console errors** — none during the flow.
- **Network errors** — no unexpected 4xx/5xx.
- **Responsive** — no horizontal overflow at 320px; layout collapses correctly.
- **Visual language** — the screen matches the approved gallery: tokens, states, density.

### Playwright entry points

```bash
npx playwright test                      # run tests
npx playwright screenshot <url> <file>    # one-shot screenshot
npx playwright codegen <url>             # record actions into a script
npx playwright show-report               # open the HTML report
npx playwright show-trace <trace.zip>    # trace viewer
npx playwright install chromium           # browsers
```

Keep it minimal: one spec file per feature lane, one artifact-writing helper, no extra test
framework. Add `@axe-core/playwright` only when accessibility assertions are in scope.

---

## 5. Open design decisions

| Decision | Status | Notes |
|---|---|---|
| Font family | ASSUMPTION | Geist Sans + Geist Mono, unless the user picks another |
| Accent color | ASSUMPTION | One accent, defined as a token, chosen with the user |
| Radius steps | ASSUMPTION | 4px and 8px only |
| Type scale ratio | ASSUMPTION | 1.25 |
| Dark mode | ASSUMPTION | In scope unless the user says otherwise |

Every assumption here is confirmed with the user during the decision gate (`AGENTS.md` §A6) and
then replaced with the approved value.
