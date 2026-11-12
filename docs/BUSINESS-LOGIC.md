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
- **Technical detail:** `criteria_from_notes()` recognizes multiple checkbox segments on one line separated by `; - [ ]` (or the corresponding checked checkbox). Inline `Proof:` is attached to its segment; a following proof line applies to the final checklist on that line. Migration extracts these records once; later unrelated compatibility writes preserve structured criteria instead of reparsing Notes.
- **Source:** `.opencode/skills/board/scripts/board.py:314` (`criteria_from_notes`), `.opencode/skills/board/scripts/board.py:254` (`sync_normalized`)
- **Edge cases:** Plain prose and inferred stories are not criteria. A checkbox without explicit proof keeps `proof=NULL`; verified defaults to false unless `[x]` is present.
- **Example:** `- [x] First; Proof: alpha; - [ ] Second; Proof: beta` produces two criteria: verified `First` with proof `alpha`, and unverified `Second` with proof `beta`.

- **Rule name:** Removing normalized work cancels it
- **Plain English:** `board.py remove <ID>` takes work out of the queue or active work, but keeps it in history instead of deleting it.
- **Technical detail:** `cmd_remove()` writes the compatibility table; `sync_normalized()` deletes any active reference, clears `queue_position`, and sets `terminal_outcome='cancelled'` for omitted IDs. It retains the `planned_items` row, acceptance criteria and Notes; the compatibility projection renders cancelled history as `Dropped`.
- **Source:** `.opencode/skills/board/scripts/board.py:947` (`cmd_remove`), `.opencode/skills/board/scripts/board.py:572` (`write_atomic`), `.opencode/skills/board/scripts/board.py:254` (`sync_normalized`), `.opencode/skills/board/scripts/board.py:223` (`normalized_markdown`)
- **Edge cases:** Repeated removal is refused because the cancelled item remains visible as history, not as an absent row. Canonical planned items are never hard-deleted by this CLI path.
- **Example:** Removing active BOARD-146 leaves its planned item and criteria, with no `active_work` row or queue position and `terminal_outcome='cancelled'`.

- **Rule name:** Accept planned work atomically
- **Plain English:** A preview is not persisted until the user explicitly accepts it; accepting a subset keeps that subset's preview order and assigns IDs only then.
- **Technical detail:** `validate_plan_batch()` validates the full JSON array and resolves temporary `key` references in `blocked_by` to existing or newly assigned Board IDs without I/O. `accept_plan_batch()` runs under `BEGIN IMMEDIATE`, allocates after the largest retained numeric `BOARD-###` ID, inserts ordered `planned_items` and unchecked `acceptance_criteria`, and refreshes the compatibility projection in one transaction.
- **Source:** `.opencode/skills/board/scripts/board.py` (`validate_plan_batch`, `accept_plan_batch`, `persist_normalized_projection`)
- **Edge cases:** Empty/malformed batches, invalid items, repeated keys, duplicate/missing/unknown dependency references, and any invalid criterion refuse the entire batch. Failed acceptance rolls back all inserts and does not consume IDs.
- **Example:** Draft keys `core` then `client`, with `client` blocked by `core`, are accepted as consecutive Board IDs and the dependency is stored using the assigned `core` ID.

- **Rule name:** Promote and finish canonical planned items
- **Plain English:** Promotion makes queued work active; completing or cancelling removes it from Active but keeps the item and criteria in history.
- **Technical detail:** `transition_plan_item()` updates queue position and `active_work` transactionally. Promotion clears `queue_position` and inserts one `Ready` active reference. Completion sets `terminal_outcome='completed'`; cancellation sets `'cancelled'`; both delete the active reference. `plan complete` refuses rows with a recorded worktree or `Pending Merge`; the human finalizer alone completes those rows. Generic `set-status` allows active-to-active changes only. The finalizer's `Merged` transition is allowed only through its same-transaction board adapter.
- **Source:** `.opencode/skills/board/scripts/board.py` (`transition_plan_item`, `sync_normalized`, `write_connection_snapshot`); `.opencode/skills/git-worktree/scripts/worktree.py` (`clear_row_worktree`)
- **Edge cases:** Duplicate promotion and terminal reopening are refused. Completion cannot hide unmerged work. IDs remain consumed because canonical terminal records are retained. Queue positions may have gaps after promotion.
- **Example:** Promoting a queued item changes it to `Ready` with no queue position; completing it removes its active reference and preserves its criteria with outcome `completed`.

- **Rule name:** Active board views exclude plans and history
- **Plain English:** The traditional board shows only promoted active work after normalized migration; the planning CLI owns queue and history.
- **Technical detail:** `read_table(active_only=True)` filters to `active_work`; `cmd_show`, `cmd_lanes`, and `cmd_export` use that projection. `plan queue` orders by `queue_position`; `plan history` orders by immutable `display_position` and excludes active rows.
- **Source:** `.opencode/skills/board/scripts/board.py` (`read_table`, `normalized_markdown`, `plan_rows`, `cmd_show`, `cmd_lanes`, `cmd_export`)
- **Edge cases:** Pre-migration legacy Markdown remains readable; lifecycle commands refuse until explicit normalized migration has been applied.
- **Example:** Queued BOARD-143 and completed BOARD-131 appear in their dedicated views but not in `board.py show` or the active export.
