# UI/UX review — BOARD-110 Fix the unslop signs in the board console

**Reviewed commit:** `6c3eeb8`   **Verdict:** **PASS**
**Evidence:** `artifacts/factory/qa/2026-11-11/BOARD-110/after/root/`
`1440x900/{light,dark}/1440x900-*.png`, `390x844/light/390x844-light.png`,
`320x800/light/320x800-light.png`, `834x1112/light/834x1112-light.png`,
`1920x1080/dark/1920x1080-dark.png`, `1440x900/light/compare.png` (vs BOARD-109),
`../summary.json` — 5 viewports × 2 schemes, 0 console errors, 0 page errors, 0 network
failures, no horizontal overflow at 320px.
**Unslop audit:** `docs/reviews/BOARD-110-unslop.md` (PASS).
**Round:** 1 of 3; fresh reviewer.

---

## Gallery conformance

Matches the approved record in `docs/UI-UX.md` §6.1 (one accent `#2f6feb` / `#6f9dff`, one stop
with work; monochrome ink; semantic status only; system sans + mono; scale 11/13/15/20/28;
weights 400/500/600; spacing 4–48; radius 4/6/10; 150ms named transitions; comfortable default
with a compact toggle).

The only gallery change in this commit is the §6.1 record itself: the five lane counts are now
described as one flow instrument instead of a pipeline of cards, and the assumption table was
replaced with the values that are actually in the CSS. The CSS matches that record exactly
(`.flow`/`.flow-stop` `board_serve.py:308`–`:323`; tokens `:187`–`:245`). No deviation.

---

## Anti-slop findings (§2)

**No violations.** Rules 1–15 all hold on the capture:

| Rule | Observation |
|---|---|
| 1 no gradient hero | No hero; no gradient on any surface |
| 2 meaningful copy | "Factory Board — Lanes, cards and live worktrees — what is in flight right now" |
| 3 no identical stat cards | The five stops are one framed instrument with one accent, not five cards; the primary metric is the 28px headline |
| 4 one accent | Accent on one flow stop, card IDs, selection and focus; green/amber/red only as status rails and risk dots |
| 5 real type scale | 11/13/15/20/28, documented, 65ch measure |
| 6 radii and elevation | 4/6/10; one shadow on the app bar only |
| 7 asymmetry | Left axis, meta right-aligned, lane stack; no centered stack |
| 8 real density | 11 real cards with type/priority/risk; 9 merged; live worktree count |
| 9 specific states | Lane-specific empty text (`EMPTY_TEXT` `:47`); error banner names the recovery (`BOARD_READ_HINT` `:64`) |
| 10 functional icons | One 1.8-stroke mark; no icon beside labels; risk emoji stripped and replaced by dots |
| 11 not every shape a pill | Chips 4px, controls 6px, panels 10px |
| 12 no synthetic imagery | None |
| 13 brief motion | 150ms named color/border/transform transitions; the live dot pulse is the one loop and is semantic |
| 14 spacing scale | 4/8/12/16/24/32/48; 1–6px optical nudges only |
| 15 contrast, focus, targets | Meta text ≥4.5:1 (fixed in BOARD-109 round 2), 2px accent focus ring `:262`, ≥24px targets, 44px at ≤480px `:503` |

### Low observations (non-blocking)

| # | Rule | Expected | Actual | Evidence | Fix |
|---|---|---|---|---|---|
| O1 | §3.1 U2 / §2 rule 4 | The accent marks the outcome that needs the architect: a decision lane | The accent stop is the **first** lane in `ACTIVE_LANES` order with the peak count. Live board has In Progress 1 and Pending Merge 1, so In Progress is blue and Pending Merge — the lane "waiting for approval" — gets a faint bar. Blocked can never win a tie because it is last | `board_serve.py:1290`; `1440x900/light/1440x900-light.png` (blue under In Progress, grey under Pending Merge) | Order the tie-break by decision urgency (Blocked > Pending Merge > In Review > In Progress > Ready), or accent every non-zero stop |
| O2 | Unslop type pass / sentence case | Section heading in sentence case | `harness board` renders lowercase, straight from the board label token | `board_serve.py:1254` (label from `discover_boards` `:127`); `1440x900/light/1440x900-light.png` | Capitalise the heading only: `Harness board` |
| O3 | Copy polish | `11 cards`, `3 worktrees` | `11 card(s)`, `3 worktree(s)` — developer pluralisation leaking to the user | `board_serve.py:1256`, `:1379`; `1440x900/light/1440x900-light.png` | Pluralise properly, or drop the counts from the meta line |

**Fix rows:** none. O1 is the only one with a product consequence; it is a low-severity polish
item on an internal read-only console and does not block merge. O2/O3 are cosmetic and can ride
with O1 if the row is touched again. The orchestrator may file O1 as a `Fix` row if it wants the
signature corrected before merge.

---

## User-centred (§3.1)

| # | Question | Result |
|---|---|---|
| U1 | Who is this for, what are they doing? | **Pass.** One architect or orchestrator checking what factory work is in flight and what needs a decision. Stateable in one sentence from the header and the lane model |
| U2 | What outcome did they come for? | **Pass.** The 28px first line ("2 active · 1 pending merge · 0 blocked") plus the flow instrument answer "what is in flight and what needs me". O1 weakens the accent's signal on ties but does not hide the outcome |
| U3 | Is the primary action obvious? | **Pass, with the read-only caveat.** There is no write action by design. The dominant affordances are the flow stops (filter by lane) and search — visible without scrolling, labelled with the user's words. Acceptable for a read-only console |
| U4 | Does it ask the user to do the org's work? | **Pass.** IDs, branches and absolute paths are the point in this tool; every row also names the task in words. No raw enum leaks into user-facing copy |
| U5 | Does it respect the user's time? | **Pass.** One request renders the whole board; filters are instant client-side; `/` focuses search; state is in the URL; refresh is 10s and pausable; auto-refresh is skipped while a card is open or a filter is active |
| U6 | Destructive actions confirmed/reversible? | **N/A.** Read-only. The only copy button copies a branch name |
| U7 | Do errors name the problem and the next action? | **Pass.** A read failure renders the exception plus "Check that the board path (--file or docs/BOARD.md) exists and is a valid board table." (`:64`); per-lane empties name the next step |
| U8 | Keyboard-only, 200% zoom, 320px, screen-reader names? | **Pass (static).** `/`, `j`/`k`, `Enter`, `Esc`; 2px focus ring; `sr-only` labels on search and selects; `aria-pressed` on flow stops; `role="group"` with a name; native `<details>`; no 320px overflow; 44px targets at ≤480px. Interaction itself is not captured — see Limitations |

---

## Modern (§3.2)

| # | Convention | Result |
|---|---|---|
| M1 | Real input types | **Pass.** `type="search"`, `autocomplete="off"`, real `<select>` filters |
| M2 | Inline validation | **N/A.** No form; filters are non-validating |
| M3 | Skeletons over spinners | **Pass.** Server-rendered HTML; no spinner and nothing to skeleton |
| M4 | Optimistic feedback | **Pass.** Filtering is immediate; density and theme apply on click and persist |
| M5 | One text face, real scale, few weights | **Pass.** System sans + mono for ids/paths/counts; 400/500/600 |
| M6 | Keyboard-first for power users | **Pass.** `/`, `j`/`k`, `Enter`, `Esc`, URL-encoded state |
| M7 | Dark mode designed | **Pass.** Separate dark token set and dedicated dark captures; hairlines carry depth, not shadows |
| M8 | Copy names the job | **Pass.** "Factory Board", "Refresh now", "Pause", "Pending Merge — Green, waiting for approval" |
| M9 | No layout shift | **Pass.** Fixed lane/card heights per type; no async content injection |
| M10 | Touch targets ≥44px | **Pass at ≤480px** (`.btn`, `.copy`, `.more`, summaries, search clear); desktop 28–44px, above the 24px review floor |

---

## Density (§3.3)

**Scanning.** The user scans 11 cards across 8 lanes. The layout matches: 44px lane summaries,
36px card summaries, one-line meta, secondary detail (type, priority, risk) inline on the card
row, real counts per lane, compact toggle for a denser pass. The overview stays spacious because
it is read once, not scanned. Correct choice.

---

## Interaction-dependent points (stated, not faked)

The capture script does not click, type, scroll or press keys. These were judged from source,
not from a capture: flow-stop filtering (`:813`–`:818`, `:744` sets `aria-pressed`), theme
tri-state and persistence (`:630`–`:640`, `:900`), density toggle (`:642`–`:648`), keyboard
handlers (`:908`–`:932`), URL state (`:661`–`:676`), expanded card/checklist (native
`<details>` + `render_notes`), and the all-clear state (`:1352`–`:1362`). None is claimed as
visually verified.

No scrolled capture exists, so the sticky lane header under the app bar is confirmed only by
CSS (`--appbar-h` measured `:620`–`:629`; static bar at ≤480px `:504`), as in BOARD-109 round 2.

---

## Overall impression

**Works:** the screen now reads as an instrument — one framed flow of five stops with a single
accent, quiet graphite chrome, sentence-case labels, and real card density; the four slop tells
named for this round are gone in the pixels, not just in the diff.
**Weak:** the signature can point at the wrong lane when counts tie, so the one colored element
is not always the one that needs the architect; two small copy details (`harness board`,
`card(s)`) still read as machine output.
**Highest-impact change:** make the accent follow the decision lane — on a tie, Blocked then
Pending Merge outranks In Progress — so the single accent always means "this needs you".

**Verdict: PASS.** No §2 violation, §3.1 and §3.2 pass, density is right, and the round's four
required signs are resolved. The three observations are low-severity polish on an internal tool;
none is a merge blocker.

---

## Round 3 — baseline alignment fix

Round 2 found one low craft regression: at ≤640px a wrapped lane name dropped its count and bar
below the others, so the two accented tie values did not read as a pair.

**Fixed** at `a1ee295` with `.flow-name { min-height: 2.4em; }` for the mobile flow
(`board_serve.py:498`). The round-3 capture proves the alignment: `round3/root/320x800/light/component-1-light.png`
and `390x844/light/component-1-light.png`, with dark matching.

No numbered §2 rule is broken, §3.1 and §3.2 still pass, and gallery conformance is unchanged.
The round-1 "make the accent follow the decision lane" suggestion is superseded by the approved
tie rule: every lane tied for the peak count is accented, so the color never implies an arbitrary
order. **Verdict: PASS.**
