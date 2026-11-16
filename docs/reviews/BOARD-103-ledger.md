# Ledger — BOARD-103
Round cap: 3. The ledger is the only state carried between rounds.

## Round 1
- Findings: bug|functional|/factory|attached-git-directory — docs/reviews/BOARD-103-review.md, bug|functional|/factory|committed-merge-cleanup — docs/reviews/BOARD-103-review.md, bug|functional|/factory|conflict-resume — docs/reviews/BOARD-103-review.md, bug|functional|/factory|mode-map-consistency — docs/reviews/BOARD-103-review.md, bug|functional|/factory|workspace-incarnation — docs/reviews/BOARD-103-review.md, bug|functional|/factory|saved-base-verification — docs/reviews/BOARD-103-review.md, bug|functional|/factory|review-final-destination — docs/reviews/BOARD-103-review.md, bug|functional|/factory|authenticated-ready-marker — docs/reviews/BOARD-103-review.md, bug|functional|/factory|template-work-surface-pointer — docs/reviews/BOARD-103-review.md
- Fix rows: BOARD-104, BOARD-105, BOARD-106, BOARD-107, BOARD-108, BOARD-109, BOARD-110, BOARD-111, BOARD-112
- Fix rows merged: -
- Stop reason: -

## Round 2
- Findings: bug|functional|/factory|attached-git-directory — docs/reviews/BOARD-103-review.md, bug|functional|/factory|mode-map-consistency — docs/reviews/BOARD-103-review.md
- Fix rows: BOARD-104, BOARD-107
- Fix rows merged: -
- Stop reason: Repeat fingerprints escalated BOARD-104/107 and parent to Blocked. User explicitly approved both focused corrections and a third/final review; no fourth round.

## Round 3
- Findings: bug|functional|/factory|mode-map-consistency — docs/reviews/BOARD-103-review.md
- Fix rows: BOARD-107
- Fix rows merged: -
- Stop reason: BLOCKED at final round: inherited permission dict equality ignores rule order and may weaken secret denies. BOARD-107 repeat; no fourth round. Final reviewer discovered zero tests; no independent31-test proof. Template edit also requires permission reload. Human follow-up decision required.
