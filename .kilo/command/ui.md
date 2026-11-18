---
description: Capture UI evidence and run independent parallel reviews
---

Follow `.kilo/skills/qa-review/SKILL.md` for focused behavior checks and the existing `browser-review.mjs` capture. Use the original assigned workspace and shared evidence; reviewers do not modify application source.

After the initial component gallery, ask whether the user wants unslop; run QA regardless. Run `ui-critic` and any requested general read-only unslop task loading `.kilo/skills/unslop/SKILL.md` in parallel against the same capture. No new permanent agent is needed. The critic checks hierarchy, usability, accessibility, and product character; unslop identifies relevant generic-design defects, not an exhaustive audit. Consolidate findings once with QA results, have the builder fix meaningful issues and agreed polish, then recheck. A proven harmless development-only favicon failure is nonblocking; preserve raw evidence and do not ignore auth, script, or API failures. Report verified outcomes and unverified criteria honestly.
