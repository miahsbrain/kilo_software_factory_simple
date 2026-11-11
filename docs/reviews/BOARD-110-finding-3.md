## Summary

When two lanes share the highest count, `render_pipeline` accents only the first one in `ACTIVE_LANES` order, so equal work is shown unequally.

## Repro steps

1. Put the board in a state where two active lanes both hold the maximum count (the board at review time had `In Review 1` and `Pending Merge 1`).
2. Open `/`.
3. Observe `In Review 1` carries the accent count and blue bar, while `Pending Merge 1` has the same count and a full-width bar but stays neutral.

## Expected behavior

The changelog and `docs/UI-UX.md` §6.1 state that only the stop with the highest non-zero count carries the accent. When several stops tie for the highest count, the rule should be applied consistently: accent every tied maximum, or document the tie-break so the emphasis is not arbitrary.

## Actual behavior

`render_pipeline` picks `active = next((lane for lane in ACTIVE_LANES if counts.get(lane, 0) == peak), None)` (`board_serve.py:1288-1290`), so `Ready`, `In Progress`, `In Review`, `Pending Merge` order decides the winner. Two lanes with one card each render as one emphasised lane and one neutral lane, which misreads as "In Review has the most work".

## Evidence

- Screenshot: `artifacts/factory/qa/2026-11-11/BOARD-110/qa/root/1440x900/dark/1440x900-dark.png` — both counts are `1`; only `In Review` is accent blue.
- Served HTML `curl -s http://127.0.0.1:15181/` — `In Review` has `data-active="true"`, `Pending Merge` has the same count without it.
- Code: `.kilo/skills/board/scripts/board_serve.py:1288-1290`, CSS `board_serve.py:318-323`
- Console: 0 errors, see `console.log`

- Network: 0 failures, see artifacts/factory/qa/2026-11-11/BOARD-110/qa/root/1440x900/light/network.json
- Spec: docs/UI-UX.md §5 and the BOARD-110 acceptance criteria

## Acceptance criteria

- [ ] when two lanes tie for the highest non-zero count, accent treatment is either applied to both or the documented tie-break matches the rendered result
- [ ] the screen does not imply one of two equal lanes is busier

## Risk

🟡 low — a wrong emphasis cue in a read-only console; no data or action is affected.
Reversibility: two-way. Blast radius: the accent on the flow instrument.
