# Unslop audit — BOARD-110 Fix the unslop signs in the board console

**Reviewed commit:** `6c3eeb8`   **Verdict:** **PASS**
**Source:** `.kilo/skills/board/scripts/board_serve.py` (1575 lines, server-rendered CSS + JS)
**Evidence:** `artifacts/factory/qa/2026-11-11/BOARD-110/after/` — 5 viewports × light/dark,
`compare.png` against BOARD-109. 0 console errors, 0 page errors, 0 network failures, no
horizontal overflow at 320px (`summary.json`).
**Round:** 1 of 3 (`docs/reviews/BOARD-110-ledger.md`, rounds used 0). Fresh reviewer.

This audit runs `.kilo/skills/unslop/SKILL.md` in order: direction, signs audit, nine passes,
checklist. Where the skill and `AGENTS.md` §B4.3 disagree, `AGENTS.md` wins; no such conflict
changed a verdict here.

---

## 1. Direction (approved, restated)

- **Product.** A read-only console for one architect to see factory work in flight and what
  needs a decision.
- **Character.** Calm, exact, instrument-like.
- **World.** A night-shift control room: graphite surfaces, one signal blue, status lamps.
- **Moments.** The flow instrument, and the parsed acceptance checklist inside a card.
- **Signature.** The single accent stop under the lane that has work.

Every pass below is judged against these five lines, not against a trend.

---

## 2. Signs audit (`references/signs.md`)

One line per sign that is **present**. Absent groups are stated as absent; no sign is invented.

### Surfaces and color
- None present. One neutral ramp (`#f5f6f7`/`#ffffff`/`#fbfbfc`; `#0f1113`/`#171a1d`/`#1c2024`),
  three ink roles (`--ink`, `--ink-soft`, `--ink-faint`), semantic colors confined to lane rails
  and risk chips, hairline borders at `--line`. No gradient, glow, blob or glass anywhere.
- No "every element highlighted": the accent appears on one flow stop, card IDs, selection and
  focus only.

### Type
- None present. Weights are 400/500/600 only (`grep` over the CSS: 500 at `:380`, `:438`; 600 at
  `:277`, `:299`, `:319`, `:360`, `:369`, `:373`, `:414`, `:437`).
- No `text-transform` anywhere in the file: the uppercase tracked lane/table labels are gone.
- Letter spacing appears once, `-0.02em` on the 28px `.headline` (`:299`) — large display text,
  which the type pass permits. No small text is negatively tracked.
- No italic, no mixed number formats: counts are mono (`.flow-count` `:319`, `.headline .num`
  `:300`, `.wt-table .num` `:379`, footer `:483`).

### Icons
- None present. One inline SVG mark, 1.8 stroke, 28px (`:1396`), no emoji in the interface.
  Board risk emoji (🟢🟡🔴) are stripped server-side and re-rendered as a CSS dot
  (`RISK_EMOJI`, `risk_class`, `render_risk` `:1059`–`:1082`). Carets are functional glyphs.

### Spacing
- **Arbitrary micro-values** — present at `.live` `gap: 6px` (`:291`), `.chip.risk` `gap: 6px`
  (`:443`), `.chip` `padding: 1px ...` (`:441`), `.kbd` `padding: 0 6px` (`:335`), `.flow-bar`
  `height: 3px` (`:322`). Lives in micro-detail only. The skill allows a 2px step for nudges
  inside small controls; these are 4+2 or optical, not layout values. **Not a finding.**
- No uneven sibling card padding, no unbalanced section gaps, no different row heights inside
  one list (lane headers 44px, card summaries 36px — consistent per type, `:405`, `:425`).

### Copy
- None present. No exclamation, no greeting, no hype, no unverified claims. Placeholder is
  factual ("Search id, task, branch", `:1327`). Empty states are lane-specific (`EMPTY_TEXT`
  `:47`–`:56`), e.g. "Nothing ready. Add a row with board.py add." Error copy names the recovery
  (`BOARD_READ_HINT` `:64`). Data is real (11 cards, 3 worktrees), not `[X]` or `123,456`.
- Two non-sign copy nits are recorded in the UI report: the lowercase `harness board` heading
  (`:1254`) and `card(s)` / `worktree(s)` pluralisation (`:1256`, `:1379`).

### Components
- **A 3px bar in every flow stop** — the closest listed sign is "sparklines, tallies or mini bars
  added to every stat card" (`:322`). Present in form. Judged as the instrument's scale, not
  decoration: it encodes each lane's count against the peak, four of the five bars are empty,
  and only the peak stop is accent. **Listed, not filed.**
- No glowing pills, no `PRO`/`New ✨` badges, no pill-everywhere (chip radius 4px `:441`,
  controls 6px, panels 10px), no rainbow charts, no gradient logo tile. Counts are quiet mono
  text in a 4px-radius chip (`.count` `:415`).

### Landing pages and heroes
- Not applicable: this is an app console with no hero and no marketing section. No sign can be
  present.

### Visuals
- None present. No imagery at all, which is correct for a dashboard. The two moments the
  direction asks for are built in code: the flow instrument (`:308`–`:323`) and the parsed
  checklist with proof lines (`render_notes` `:1000`–`:1040`).

### Motion
- **One looping pulse** — `.live-dot` runs `pulse 2s ease-in-out infinite` (`:292`–`:294`).
  This is the only loop. It is semantic (the dot is genuinely live, turns static when paused or
  stale via `.live.stale`, `:293`) and is fully disabled under `prefers-reduced-motion`
  (`:521`–`:523`). Not classified as the "pulse on something not live" sign. Recorded because it
  is the page's only looping motion.
- No `transition-all`, no `hover:scale`, no bouncy springs, no entrance animation. Transitions
  are named and 150ms (`:310` region, `:388`, `:348`), inside the 120–180ms token.

### Template look
- Does not fit another product after a name swap: the lane rails, the five-stop flow instrument,
  the single accent stop and the parsed acceptance checklist are specific to this factory. The
  signature appears once. **Pass.**

---

## 3. Nine passes (reviewed in order)

| # | Pass | Result | Evidence |
|---|---|---|---|
| 1 | Spacing | PASS — one 4px rhythm (`--s1`…`--s12`, `:203`), one padding per sibling type, lane rows 44 / card rows 36; only 1–6px optical nudges inside chips and the live dot | `:203`, `:291`, `:405`, `:425`; 1440 capture |
| 2 | Color | PASS — one neutral ramp, three text roles, one accent; semantic green/amber/red only on lane rails and risk dots; dark theme is designed, not inverted; hairlines, no shadow except the app bar | tokens `:187`–`:245`; 1440 light and dark captures |
| 3 | Icons | PASS — one SVG mark at one stroke, no emoji, no icon beside labels, carets only where they explain disclosure | `:1396`, `render_risk` `:1059`; captures |
| 4 | Copy | PASS with nits — names the job ("Factory Board", "what is in flight right now"), specific empty/error copy, no hype, no trailing periods on short strings; `harness board` is lowercase and counts use `(s)` | `:1379`–`:1395`, `:47`, `:64`, `:1254`, `:1256`; UI report |
| 5 | Type | PASS — 11/13/15/20/28 fixed steps, 400/500/600 only, sentence case, no uppercase tracking, no negative tracking below 28px, mono for figures | `:202`, `:277`–`:438`; compare.png |
| 6 | Layout | PASS — app shell fills the viewport, 1360px cap, left axis, meta pushed to the right rail; lane stack beneath; ≤640px the flow becomes a five-column grid with all five stops visible (superseded the earlier scroller in round 2) | `:302`, `:308`, `:496`–`:498`; 320/390/834/1920 captures |
| 7 | Details | PASS — nested radii add up (4 chip / 6 control / 10 panel), `/` rendered as a keycap, quiet mono counts, hover is a surface step, focus is a 2px accent ring, selected card is surface + outline | `:262`, `:317`, `:334`, `:435`, `:458`; captures |
| 8 | Visuals | PASS — no decoration; the moment is the flow instrument and the parsed checklist, both real product content, no placeholder slot | `:308`–`:323`, `render_notes` `:1000`; captures |
| 9 | Motion | PASS — one named 150ms transition, no layout properties animated; the single loop is the live dot and is reduced-motion aware | `:292`–`:294`, `:521`–`:523` |

---

## 4. Final checklist (`SKILL.md`)

- [x] The direction is written and every pass follows it
- [x] Every spacing value is on the 4px scale and equal things have equal sizes — layout values,
      yes; sub-8px optical nudges in chips/dot are the allowed exception
- [x] Icons, labels and numbers each sit in one aligned column
- [x] One tinted neutral ramp, three text roles, one accent with enough contrast (accent text
      `#1f5fd6` light / `#6f9dff` dark; darkest meta text ≥4.5:1, verified in BOARD-109 round 2)
- [x] No hue gradients, gradient text, glows, colored shadows or color blobs
- [x] No emoji left in the interface
- [x] One icon set at one size and stroke
- [x] Type chosen for the character, weights 400–600, no uppercase tracked labels, no italic,
      no negative tracking on small text
- [x] No exclamation marks, no trailing periods on short strings, no greeting headline, no
      unverified claims
- [x] Numbers in one format with tabular figures (mono stack)
- [x] Nested radii add up
- [x] Table row states read apart: header, main-row surface step, selection, keyboard focus
- [x] Buttons share the control radius, no square corners against the component style
- [x] ~~A hero has a real visual or a product preview~~ — not applicable: app console, no hero.
      The equivalent moment (flow instrument) is real, not filler
- [x] The first screen is composed as a whole with no dead empty band
- [x] No looping or bouncy motion, one easing curve, no animated layout properties — with the
      single exception of the live dot, which is semantic, stops when stale, and is disabled
      under reduced motion
- [x] Template check: swapping the product name would not fit another product

---

## 5. The four signs this round had to fix

| Sign | Verdict | Evidence |
|---|---|---|
| **Five equal stat cards** | **Resolved.** They are no longer five cards: one framed panel, hairline separators, no per-card border/shadow/gap, one accent stop. Five equal-width stops remain **by design**, as the approved flow instrument; the sign would return only if the stops regained individual card chrome | `.flow`/`.flow-stop` `:308`–`:323`, `render_pipeline` `:1288`; `compare.png` (before: five separate cards; after: one instrument) |
| **Uppercase tracked labels** | **Resolved.** No `text-transform` in the file; lane names, table headers and the wordmark are sentence case at normal tracking | `:277`, `:373`, `:414`; 1440 capture |
| **Negative small-text tracking** | **Resolved.** The only `letter-spacing` is `-0.02em` on the 28px headline; `.wordmark`, `.panel-head h2`, `.panel-title`, `.lane-name` had theirs removed | `:277`, `:299`, `:360`, `:369`, `:414`; compare.png |
| **Weights 650/700** | **Resolved.** Only 400 (body), 500 and 600 remain; `.card-id` 700 → 600, lane names 650 → 600, headline/wordmark 650 → 600 | `:277`, `:299`, `:414`, `:437`, `:438`; `grep` weight set |

---

## Verdict

**PASS.** The four required signs are resolved, no other sign on the list is present in a
form that should be fixed, the direction's moments (flow instrument, parsed checklist) are
carried by real product content, and the signature is visible exactly once. The only borderline
items are the semantic live-dot pulse and the micro spacing nudges; both are justified by the
skill's own allowances and neither is a finding.

---

## Round 3 — baseline alignment fix

**Round 2 finding (low, Spacing).** Below 640px a wrapped lane name pushed its count and 3px bar
about 13px below the other stops, so tied accent bars did not share a baseline. That broke the
checklist item "numbers each sit in one aligned column" and the spacing rule "rows in one list
with different heights".

**Fix:** `.flow-name { min-height: 2.4em; }` inside the `max-width: 640px` block
(`board_serve.py:498`), commit `a1ee295`.

**Re-verification:** `artifacts/factory/qa/2026-11-11/BOARD-110/round3/` — 5 viewports × light/dark,
0 console errors, 0 page errors, 0 network failures, no horizontal overflow. The `.flow` component
crops at 320 and 390 show every count and bar on one baseline, in both schemes.

**New signs:** none. The fix is spacing only; the direction, one-accent rule and the four resolved
signs are unchanged. **Verdict: PASS.**
