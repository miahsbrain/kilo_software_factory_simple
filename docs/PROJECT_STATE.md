# PROJECT STATE — software factory

- **Phase:** BOARD-115, docs-only review passed; local task commit prepared for human review.
- **Active task:** `docs/require-committed-worktree-handoff-checkpoints` in
  `.kilo/worktrees/require-committed-worktree-handoff-checkpoints`, based on migration checkpoint
  `bc3ca6c` on `feat/port-factory-harness-to-opencode-v2`. Approved rule and derived instructions
  updated; parent approved the local task commit through the existing Kilo bootstrap guard.
  File review only; no builds or tests. No approval to merge the migration.
- **Migration:** BOARD-114 remains blocked during security verification; not resumed by BOARD-115.
- **Progress:** Native `.opencode/agents`, `commands`, `skills`, `catalog` and `opencode.jsonc`;
  architect primary plus six specialists; models inherit session selection. Existing Python/JS
  mechanics migrated, native ordered permission generator, factory base preference `opencode`.
- **Integration:** `opencode` receives this factory port; `main` retains Kilo. No merge or push.
- **In flight:** `feat/port-factory-harness-to-opencode-v2` in the unchanged bootstrap worktree
  `.kilo/worktrees/port-factory-harness-to-opencode-v2`. No board files edited by the builder.
- **Not complete:** security adapter implemented but not verified; container port, native
  runtime validation and independent review remain. This is not a security-complete or merge-ready port.
- **Verification:** `python3 .opencode/skills/git-worktree/scripts/test_env.py` → exit 0,
  `all checks passed`. This was the only verification command.
- **Security check:** `node --test .opencode/plugins/factory-guard/guard.test.mjs` exited 1:
  two fixture tests hit `EACCES` creating directories under `/tmp/opencode`; policy/runtime merge
  test passed. No retry, dependency install or alternate fixture path attempted.
- **Next action:** human reviews the BOARD-115 local task commit. BOARD-114 remains blocked and
  not merge-ready; it separately awaits user authorization of a
  writable fixture location or repair of temporary-directory access.
