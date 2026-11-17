## Summary

Below 640px the flow instrument clips the fourth stop mid-label and loses the panel's right frame edge, with no visible scroll affordance, so the "one framed instrument" reads as a broken strip on the 390px and 320px viewports.

## Repro steps

1. Open `/` at 390 × 844 in a fresh browser.
2. Look at the five-stop panel under the headline.
3. Observe `Pending Merge` wrapped to two lines and cut at the viewport edge, its bar truncated, and the panel frame's right border absent; at 320 × 800 only three stops are visible and nothing indicates two more exist.

## Expected behavior

BOARD-110 criterion 1: the five lane counts are one flow instrument, a single framed panel of five hairline-separated stops. At every viewport the frame should read as closed and each stop should be either fully visible or clearly continuable (scroll cue), per `docs/UI-UX.md` §3.1 U8 and §3.2 M9.

## Actual behavior

`@media (max-width: 640px)` turns `.flow` into `display: flex; overflow-x: auto` with `.flow-stop { flex: 1 0 104px; }` (`board_serve.py:495-497`). Five stops need 520px, so at 390px the container clips inside the fourth stop: the label breaks across lines, the bar is cut, and the frame's right edge is off-screen. The scrollbar is not visible in the capture, so nothing signals that `Pending Merge` and `Blocked` continue off-screen.

## Evidence

- Screenshot: `artifacts/factory/qa/2026-11-11/BOARD-110/qa/root/390x844/light/390x844-light.png`
- Screenshot: `artifacts/factory/qa/2026-11-11/BOARD-110/qa/root/320x800/light/320x800-light.png`
- Component crop: `artifacts/factory/qa/2026-11-11/BOARD-110/qa/root/320x800/light/component-1-light.png`
- CSS: `.kilo/skills/board/scripts/board_serve.py:495-497`
- Console: 0 errors, see `console.log`; the page-level overflow check passes, the clipping is inside the instrument's own scroll container

- Network: 0 failures, see artifacts/factory/qa/2026-11-11/BOARD-110/qa/root/1440x900/light/network.json
- Spec: docs/UI-UX.md §5 and the BOARD-110 acceptance criteria

## Acceptance criteria

- [ ] at 390px and 320px the instrument reads as one closed framed panel
- [ ] no stop label is cut mid-word
- [ ] if the stops overflow, a scroll cue makes the off-screen stops discoverable

## Risk

🟡 low — a dense factory tool is used on desktop, but an orchestrator on a narrow window loses sight of two lanes and sees a visibly broken panel.
Reversibility: two-way. Blast radius: the flow instrument only.
