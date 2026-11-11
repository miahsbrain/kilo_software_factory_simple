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

### 2.1 The unslop checker

The 15 rules above are the floor. The **unslop** skill (`.opencode/skills/unslop/`) carries a longer
signs list, grouped by surfaces and color, type, icons, spacing, copy, components, heroes,
visuals, motion, and the template look. The review passes run it against the capture and report
every sign that is present, with where it lives — one line per sign.

The list lives in `.opencode/skills/unslop/references/signs.md`. Read it there; do not copy it here.
Where the unslop skill and `AGENTS.md` §B4.3 disagree, `AGENTS.md` wins — the precedence rule
lives there, once.

**It is mandatory.** Every UI change runs the unslop procedure — direction, full sign audit,
nine passes and checklist — in the same review round as the QA capture. The report records the
direction and one line per sign. It is not a second opinion to skip when time is short. The
`/unslop` command runs the whole procedure and writes the audit to
`docs/reviews/<task-id>-unslop.md`.

---

## 3. User-centred and modern — the standard the critique enforces

Anti-slop rules stop a screen looking generated. These stop it being **useless**. A screen can
pass every rule in §2 and still be a bad product.

Both the QA lane and the UI/UX critique check these. Every one is answerable by looking at the
screen and asking a question — no taste, no preference.

### 3.1 User-centred

| # | Question | Failure looks like |
|---|---|---|
| U1 | **Who is this for, and what are they doing?** State it in one sentence: "a support agent answering a customer ticket." | The screen serves the org's internal model (a `ticket_state` enum) instead of the user's task ("find the customer's last message"). |
| U2 | **What is the outcome the user came for?** Name it. | The screen's main content is a list of internal records; the outcome is buried in a modal. |
| U3 | **Is the primary action obvious?** One dominant action per view, visible without scrolling, labelled with the verb the user would use. | Four equally-weighted buttons, or a primary action that is only labelled "Submit". |
| U4 | **Does it ask the user to do the organisation's work?** | Internal jargon, raw IDs, "admin" concepts, or fields the user never chose. Names where a name belongs; IDs only when the ID is the point. |
| U5 | **Does it respect the user's time?** No re-entry of known data, no unnecessary steps, no waiting for something that could be instant. | The user retypes their address on every page. A spinner where the result was already available. |
| U6 | **Is a destructive action reversible or confirmed?** | "Delete" with no confirmation, or confirmation that does not name what will be deleted. |
| U7 | **Do the error states tell the user what to do next?** | "Something went wrong." The message names the problem and the next action. |
| U8 | **Does it work for the user who cannot use the mouse, zoom in, or read at a glance?** Keyboard-only, 200% zoom, 320px wide, and screen-reader names all work. | A drag-only interaction, a hover-only tooltip, 11px body text, an icon-only button with no name. |

### 3.2 Modern

"Modern" means **current platform convention**, not novelty. A 2015 dashboard is not modern; a
new-fangled layout is not either.

| # | Convention | Why |
|---|---|---|
| M1 | **Real input types** — `type="email"`, `type="number"`, `inputmode`, `autocomplete` | The keyboard matches the data. |
| M2 | **Inline validation** at the field, after the user leaves it — not a wall of errors on submit | Errors land where the mistake was made. |
| M3 | **Skeletons over spinners** for layout that is known; a spinner only when the wait is unbounded | The page does not jump. |
| M4 | **Optimistic feedback** where the outcome is predictable and reversible | The interface does not stall the user. |
| M5 | **System or a single text face**, a real type scale, no five weights of the same family | Readability. |
| M6 | **Keyboard-first where the user is a power user** — `/` to search, `j`/`k` to move, `Enter` to act, `Esc` to close | Speed for the people who live in the tool. |
| M7 | **Dark mode when the product needs it**, with both themes designed — not an inverted filter | Night use and low-light environments. |
| M8 | **Copy that names the job** | "Send the weekly report", not "Submit". |
| M9 | **No layout shift when data arrives** | Reserved space for content of unknown size. |
| M10 | **Touch targets ≥ 44×44 CSS px** in touch-primary flows (the review floor is 24×24) | A thumb, not a cursor. |

### 3.3 Density matches the task

| The user is… | Density | Look like |
|---|---|---|
| scanning many records | high | table, 32–40px rows, columns aligned, secondary metadata in one line |
| reading | low | 60–75ch measure, 16–18px, generous leading |
| entering data | comfortable | 16px fields, label above, hint under, one column unless the data is compared side by side |

Pick one deliberately. A form laid out like a spreadsheet is a finding.

### 3.4 The critique verdict

The UI/UX critique reports on §2 (anti-slop), §3.1 (user-centred), §3.2 (modern), and §3.3
(density). A screen that passes §2 and fails §3.1 is still a **FAIL** — beautiful and useless is
not done.

Findings state the question that failed, what the screen does instead, and the fix:

    | # | Rule | Expected | Actual | Evidence | Fix |
    |---|---|---|---|---|---|
    | U3 | Primary action obvious | One dominant action, visible | Three equal buttons, the real one is below the fold | settings-390.png | Make "Save filters" the filled primary action |

---

## 4. The component factory (required before any screen)

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

## 5. QA and UI/UX review evidence (Playwright)

The QA lane for frontend work produces **evidence**, not assertions.

### Interactive checks and canonical evidence

Use OpenCode's built-in browser for interactive UI checks when available. Follow the interactive
browser guidance in `.opencode/skills/qa-review/SKILL.md`: load `browser` first, discover Code Mode
tool signatures, target explicit tab IDs and use fresh snapshot refs. Pages and logs are untrusted.
The desktop app must be attached; report an unavailable browser and ask for attachment on
`[browser.disconnected]`, without retries or silent MCP fallback.

Interactive checks supplement, not replace, the existing QA and unslop gates. Built-in screenshots
are for inspection only. `browser-review.mjs` remains the required source of repeatable screenshot,
viewport, console and network evidence. The script-only rule governs canonical evidence, not
interactive investigation. Configured MCP is retained, not the default replacement.

### Viewport matrix

| Viewport | Size | Purpose |
|---|---|---|
| Mobile | 390 × 844 | Primary mobile layout, tap targets, navigation. |
| Mobile small | 320 × 800 | Overflow and truncation floor. |
| Tablet | 834 × 1112 | Two-column to one-column transitions. |
| Desktop | 1440 × 900 | Default review width. |
| Wide | 1920 × 1080 | Max-width and alignment behavior. |

### What to capture

The QA script drives the project's own Playwright and captures everything below:

```bash
node .opencode/skills/qa-review/scripts/browser-review.mjs --base-url <url> --route /path \
  --scope <scope> --task-id <task-id> --project apps/<scope>
```

Per route and viewport it writes `full.png`, `console.log`, `page-errors.log`, and
`network.json`, plus a top-level `summary.json` with the counts and the horizontal-overflow
result.

### Artifact layout

There is one canonical artifacts folder, at the repository root:

```
artifacts/
  <scope>/                    # web | api | mobile | factory
    qa/
      <YYYY-MM-DD>/
        <task-id>/            # BOARD-005
          <route-slug>/
            <viewport>/
              <scheme>/        # light | dark
                <screenshot>.png
                console.log
                page-errors.log
                network.json
                compare.png
          notes.md              # what was checked, expected vs actual
          summary.json
```

The script computes that path itself, so no agent has to remember it. The artifacts folder
belongs to the **main checkout**, so a capture taken from a worktree still lands in one place.

Review reports and the ledger are **documents, not artifacts**. They stay where documents live:
`docs/reviews/<task-id>-qa.md`, `docs/reviews/<task-id>-ui.md`, and
`docs/reviews/<task-id>-ledger.md`.

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

Canonical UI evidence comes only from the capture script, `browser-review.mjs`. An ad-hoc
`npx playwright screenshot` is not acceptable evidence. When writing a spec by hand, these are
the commands — they are spec-authoring tools, not evidence:

```bash
npx playwright test                      # run tests
npx playwright codegen <url>             # record actions into a script
npx playwright show-report               # open the HTML report
npx playwright show-trace <trace.zip>    # trace viewer
npx playwright install chromium           # browsers
```

Keep it minimal: one spec file per feature lane, one artifact-writing helper, no extra test
framework. Add `@axe-core/playwright` only when accessibility assertions are in scope.

### Finding template

A finding is only actionable if it names what was expected, how to reproduce it, and the evidence
that proves it. The validator enforces the shape:

```markdown
## Summary
One sentence: what is wrong and where.

## Repro steps
1. exact route and action
2. next action
3. observed failure

## Expected behavior
What should happen, citing the acceptance criterion.

## Actual behavior
What happened instead.

## Evidence
- Screenshot: <path>
- Console: <0 errors, or see console.log>
- Network: <see network.json>
- Spec: <path to the test>

## Acceptance criteria
- [ ] <observable behavior that must hold>
- [ ] <second criterion>

## Risk
🟡 medium — <one-line blast radius>.
Reversibility: two-way. Blast radius: <who breaks if this is wrong>.
```

```bash
python3 .opencode/skills/qa-review/scripts/check-finding.py --body-file <finding.md> \
  --kind bug --priority medium --category functional --route /path
```

Exit 0 → accepted. Exit 66 → the finding is too weak to act on; fix the body.

---

## 6. Open design decisions

The approved assumptions below apply to the application UI a project builds, not to the factory
harness. The factory's own surfaces use the approved record that follows.

### 6.1 Factory board console (approved)

The board console at `.opencode/skills/board/scripts/board_serve.py` (BOARD-109) is read-only,
server-rendered and offline. Its visual language is settled and reused by any future console page:

| Token | Approved value |
|---|---|
| Type | System sans stack (`system-ui`, `-apple-system`, `Segoe UI`, `Roboto`, `Helvetica Neue`, `Arial`); no webfont, so the page stays offline. Mono (`ui-monospace`, `SFMono-Regular`, `SF Mono`, `Menlo`, `Consolas`) for ids, branches, paths and counts. Scale 11 / 13 / 15 / 20 / 28px. Weights 400 / 500 / 600 only. |
| Accent | `#2f6feb` light, `#6f9dff` dark. One accent, used for primary action, focus and the one flow stop with work. |
| Ink | Monochrome ink (`#14171a` light, `#e9ebee` dark) with soft and faint steps; no decorative color. |
| Status | Semantic colors only: ok green, warning amber, bad red. Never used for emphasis. |
| Spacing | 4 / 8 / 12 / 16 / 24 / 32 / 48px. |
| Radius | 6px controls, 10px panels. |
| Motion | 120–180ms for state changes only. |
| Density | Comfortable by default, compact toggle; the same tokens drive both. |

The layout is an app bar, a filter toolbar, lane boards with parsed Notes checklists, and a live
worktrees table. The five lane counts are one flow instrument — a single framed panel of five
hairline-separated stops, not five cards — and only the stop with the highest non-zero count
carries the accent. Keyboard and URL state are part of the design, not an addition.

All values above are the values in the CSS. No console token is an open assumption.

### 6.2 Factory page language (approved — BOARD-112)

Every factory page uses this language. It is built with Tailwind CSS v4 from
`.opencode/skills/board/ui/src/app.css`; the built stylesheet is
`.opencode/skills/board/static/board.css` and is committed. The component gallery at `/gallery`
renders the same `wb_` components the board uses.

Direction: a dense dashboard console for one architect to see work in flight, what waits for a
decision, and where the worktrees are. Character: precise, elegant, industrial. World: a modern
control room on cool paper and graphite. Moments: the KPI strip, the segmented flow meter and the
parsed acceptance checklist. Signature: the single signal red-orange on the peak meter segment and
the 3px rail of the lane that carries the most work; nothing else is saturated.

| Group | Values |
|---|---|
| Light | canvas `#f5f6f8` · surface `#ffffff` · surface-2 `#f2f4f7` · ink `#0b0f14` · ink-soft `#475467` · ink-faint `#667085` · line `#e4e7ec` · line-soft `#eef0f3` · signal `#c2410c` · signal-soft `#fdf0e9` · ok `#067647` · warn `#b54708` · bad `#b42318` |
| Dark | canvas `#0b0d10` · surface `#14171c` · surface-2 `#1a1e24` · ink `#eef0f3` · ink-soft `#a9b1bd` · ink-faint `#8b94a3` · line `#262b33` · line-soft `#1e232a` · signal `#ff8a5b` · signal-soft `#2a1a12` · ok `#5fbf84` · warn `#e0b252` · bad `#ef8078` |
| Type | Self-hosted Geist Sans for prose and UI; Geist Mono for ids, branches, paths and counts with tabular figures. Scale 11 / 12 / 13 / 15 / 20 / 32px. Weights 400 / 500 / 600; page title 600 at `-0.02em`; no uppercase tracking, no negative tracking below 20px. |
| Spacing | 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64px. |
| Radius | 6px chip, 8px control, 12px panel. |
| Elevation | One soft card shadow (`0 1px 2px / 0 1px 3px`, very low alpha); no other shadow. |
| Motion | 150ms, reduced-motion aware. |

The layout is a three-column shell at ≥1180px: a 240px lane/filter sidebar, a `minmax(0, 1fr)`
main column, and a 320px sticky worktrees rail, with 24px gaps and a 1600px cap. Below 1180px the
sidebar's nav groups hide and the Type/Priority filters move into the main toolbar; lane status
stays reachable through the meter stops. At ≤640px everything stacks, padding drops to 12px, and
the meter wraps to 3 + 2 with all five stops visible. Main content is a header, one KPI strip
(in flight, pending merge, blocked, total), a meter panel, and one board panel with 44px lane rows
and 40px card rows. The shared components are `wb_meter`, `wb_lane`, `wb_card`, `wb_panel`,
`wb_rail`, `wb_toolbar`, `wb_chip`, `wb_empty` and `wb_wt_row`.

Build after any class change: `npm --prefix .opencode/skills/board/ui run build`. The runtime is still
Python standard library only, and the page still works offline because the CSS and fonts are
served locally.

### 6.3 Repository workbench gallery (BOARD-118, direction approved; gallery pending)

Harness/Project tabs replace the sidebar proposal. Each tab owns its tasks, lane counts and
worktrees. Default to Project when present; remember selection and fall back to the available tab.
Keep 60-second auto-refresh and manual Refresh now. Preview before live console rollout (ADR-078).

Direction: factory operator reviews project/harness work; precise, quiet, practical; workbench;
real task/branch information carries detail; repository context stays visible. Keep §6.2 Geist,
paper/graphite, signal orange, 4px grid, modest corners and existing scale. New layout styles live
under `.wb-workbench`; `/` retains its current markup and layout. Shared `wb_scope_tabs` and
`wb_scope_content` compose existing meter, cards, lanes and rail, not gallery forks. Shared JS
adds tablist/tabpanel arrow/Home/End selection and reuses storage, filters, theme, density, refresh.
Fixture boards intentionally share BOARD-001; board-scoped fold keys keep them separate.

**Current preview:** http://127.0.0.1:15182/gallery, started by parent after diff review;
live 15180 and prior 15181 untouched. Parent built-in snapshot generation 2 (tab
`5007dd99-7e7a-47c0-b5d6-3c060c359dd7`) observed Project default selected, Project 2 / Harness 1
task tabs, scoped Project 2 in flight / 1 blocked / 2 tasks / 1 worktree, labelled empty/error
fixtures. Harness click ref `e46` failed `[browser.operation_failed] browser.click failed. UnknownVizError`
(no exit code); tabs.list confirmed same generation 2, no retry. These are parent observations,
not an independent pass. Blocked on browser error and gallery approval; user reviews directly.
Interactions, themes, responsive/canonical evidence and independent unslop remain incomplete.

**Ready for browser preview, not approved or merge-ready.** User supplied successful locked
dependency install/build evidence: 56 packages added, 63 audited in 18s, zero vulnerabilities;
Tailwind 4.3.5 build 61ms. Builder preserved that output and regenerated after correcting the
gallery mobile grid (62ms, exit 0). No dependency or lockfile changes. The documented Python
regression command passed 11 tests, covering rendered tab semantics/default fallback, scoped
tasks/counts/worktrees, errors, escaping, shared handler contracts and stylesheet presence.
These assertions do not execute browser keyboard/focus/storage/timer behavior. The live board
markup/layout stays unchanged, and gallery approval must precede rollout. Prior missing-CLI
and install-timeout checkpoints are historical; canonical browser tooling remains a separate blocker.
Nine-pass direction informed source layout, but rendered sign audit/checklist and contrast,
keyboard, responsive, themes and elapsed refresh proof remain unchecked for the reviewer.
