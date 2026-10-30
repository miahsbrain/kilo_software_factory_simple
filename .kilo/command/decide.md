---
description: Produce a decision sheet and get the user's approval before any implementation
---

Run the decision gate from `AGENTS.md` §A6.1 for the described feature or change.

1. **Read what exists first.** Check `DOMAIN.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`,
   `docs/API_CONTRACTS.md`, and the relevant code. A decision that is already approved must be
   followed, not reopened. A change that already exists should be reused, not re-invented (§B6).
2. **Draft the decision sheet.** Only the decisions that actually change the result. For each:
   - The decision — one sentence.
   - The recommendation — one option, marked, with why it is the right default.
   - The options — 2–3 alternatives, each with a one-line trade-off.
   - The consequence — what changes, and what it costs to reverse.
   - The default if unanswered — stated explicitly, marked `ASSUMPTION`.
3. **Batch the questions** into one message and ask. Offer "go with your recommendations" as a
   fast answer. Do not drip one question at a time.
4. **On approval**, record each decision in `docs/DECISIONS.md` (with the date), and add the
   board row with 2–5 checkable acceptance criteria, a risk level, and `Blocked by`.
   For a **Feature** row, include the reuse criterion — which existing code will be extended, or
   the reason there is none to extend. The builder cannot be asked to guess it later.
5. **Then** produce the implementation plan or delegate. No code before the decisions are settled.

If something remains unclear after the sheet is answered, ask again rather than assume. Silence
is not approval.
