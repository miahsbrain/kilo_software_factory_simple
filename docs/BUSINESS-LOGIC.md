# Business logic

## Board item lifecycle

- **Rule name:** Legacy status migration
- **Plain English:** Queued work stays queued, in-flight work stays active, merged work remains completed history, and dropped work remains cancelled history. A task has one lifecycle representation, not several competing status fields.
- **Technical detail:** `Backlog` maps to `planned_items.queue_position`; `Ready`, `In Progress`, `In Review`, `Pending Merge`, and `Blocked` map to one `active_work` row with `status`; `Merged` maps to `terminal_outcome='completed'`; `Dropped` maps to `terminal_outcome='cancelled'`. A compatibility Markdown view derives the old Status field.
- **Source:** `.opencode/skills/board/scripts/board.py` (`migrate_normalized`, `normalized_markdown`, `sync_normalized`)
- **Edge cases:** Queue positions may have gaps after promotion. Legacy `user_story` stays `NULL`; no story is inferred. Legacy Notes remain byte-content-equivalent text, and only explicit checklist/proof lines become criterion records.
- **Example:** BOARD-130 remains active with status `Blocked`; BOARD-131 is completed history; BOARD-132–BOARD-144 remain in ordered queue positions; BOARD-146 remains active and BOARD-147 remains `Ready`.
