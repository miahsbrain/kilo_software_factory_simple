---
description: Capture UI evidence and run independent UI critique
---

Follow `.kilo/skills/qa-review/SKILL.md` for focused behavior checks and the existing `browser-review.mjs` capture. Use the original assigned workspace and shared evidence; reviewers do not modify application source.

After the initial component gallery, run focused QA. Run `ui-critic` against the same capture to check hierarchy, usability, accessibility, and product character. Consolidate findings once with QA results, have the builder fix meaningful issues and agreed polish, then recheck. A proven harmless development-only favicon failure is nonblocking; preserve raw evidence and do not ignore auth, script, or API failures. Report verified outcomes and unverified criteria honestly.
