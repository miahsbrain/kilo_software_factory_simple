# Business logic

## Board item lifecycle

- **Rule name:** Legacy status migration
- **Plain English:** Queued work stays queued, in-flight work stays active, merged work remains completed history, and dropped work remains cancelled history. A task has one lifecycle representation, not several competing status fields.
- **Technical detail:** `Backlog` maps to `planned_items.queue_position`; `Ready`, `In Progress`, `In Review`, `Pending Merge`, and `Blocked` map to one `active_work` row with `status`; `Merged` maps to `terminal_outcome='completed'`; `Dropped` maps to `terminal_outcome='cancelled'`. A compatibility Markdown view derives the old Status field.
- **Source:** `.opencode/skills/board/scripts/board.py` (`migrate_normalized`, `normalized_markdown`, `sync_normalized`)
- **Edge cases:** Queue positions may have gaps after promotion. Legacy `user_story` stays `NULL`; no story is inferred. Legacy Notes remain byte-content-equivalent text, and only explicit checklist/proof lines become criterion records.
- **Example:** BOARD-130 remains active with status `Blocked`; BOARD-131 is completed history; BOARD-132–BOARD-144 remain in ordered queue positions; BOARD-146 remains active and BOARD-147 remains `Ready`.

- **Rule name:** Explicit checklist extraction
- **Plain English:** Each checkbox in Notes is its own acceptance criterion; its checked state and proof belong to that criterion, while the original Notes text is unchanged.
- **Technical detail:** `criteria_from_notes()` recognizes multiple checkbox segments on one line separated by `; - [ ]` (or the corresponding checked checkbox). Inline `Proof:` is attached to its segment; a following proof line applies to the final checklist on that line. `sync_normalized()` replaces criterion rows from the parsed explicit checklist.
- **Source:** `.opencode/skills/board/scripts/board.py:314` (`criteria_from_notes`), `.opencode/skills/board/scripts/board.py:254` (`sync_normalized`)
- **Edge cases:** Plain prose and inferred stories are not criteria. A checkbox without explicit proof keeps `proof=NULL`; verified defaults to false unless `[x]` is present.
- **Example:** `- [x] First; Proof: alpha; - [ ] Second; Proof: beta` produces two criteria: verified `First` with proof `alpha`, and unverified `Second` with proof `beta`.

- **Rule name:** Removing normalized work cancels it
- **Plain English:** `board.py remove <ID>` takes work out of the queue or active work, but keeps it in history instead of deleting it.
- **Technical detail:** `cmd_remove()` writes the compatibility table; `sync_normalized()` deletes any active reference, clears `queue_position`, and sets `terminal_outcome='cancelled'` for omitted IDs. It retains the `planned_items` row, acceptance criteria and Notes; the compatibility projection renders cancelled history as `Dropped`.
- **Source:** `.opencode/skills/board/scripts/board.py:947` (`cmd_remove`), `.opencode/skills/board/scripts/board.py:572` (`write_atomic`), `.opencode/skills/board/scripts/board.py:254` (`sync_normalized`), `.opencode/skills/board/scripts/board.py:223` (`normalized_markdown`)
- **Edge cases:** Repeated removal is refused because the cancelled item remains visible as history, not as an absent row. Canonical planned items are never hard-deleted by this CLI path.
- **Example:** Removing active BOARD-146 leaves its planned item and criteria, with no `active_work` row or queue position and `terminal_outcome='cancelled'`.
