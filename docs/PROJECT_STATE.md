# PROJECT STATE — software factory

- **Phase:** BOARD-116, parent docs review passed; reviewed change prepared for human review/local commit.
- **Active task:** `docs/use-opencode-browser-for-interactive-ui-reviews` in
  `.kilo/worktrees/use-opencode-browser-for-interactive-ui-reviews`, based on migration checkpoint
  `ec7501f` on `feat/port-factory-harness-to-opencode-v2`. Approved built-in interactive browser
  policy and derived instructions updated; canonical captures remain script-only and QA/unslop
  gates remain mandatory. No approval to merge the migration.
- **Migration:** BOARD-114 remains blocked during security verification; not resumed by BOARD-116.
- **Progress:** Native `.opencode/agents`, `commands`, `skills`, `catalog` and `opencode.jsonc`;
  architect primary plus six specialists; models inherit session selection. Existing Python/JS
  mechanics migrated, native ordered permission generator, factory base preference `opencode`.
- **Integration:** `opencode` receives this factory port; `main` retains Kilo. No merge or push.
- **In flight:** `feat/port-factory-harness-to-opencode-v2` in the unchanged bootstrap worktree
  `.kilo/worktrees/port-factory-harness-to-opencode-v2`. No board files edited by the builder.
- **Not complete:** security adapter implemented but not verified; container port, native
  runtime validation and independent review remain. This is not a security-complete or merge-ready port.
- **BOARD-116 verification:** Verification limited to file review because this was a low-risk visual/static change.
  Zero verification commands; no browser/runtime checks, builds or tests.
- **Earlier migration verification:** `python3 .opencode/skills/git-worktree/scripts/test_env.py`
  → exit 0, `all checks passed`; not rerun for BOARD-116.
- **Security check:** `node --test .opencode/plugins/factory-guard/guard.test.mjs` exited 1:
  two fixture tests hit `EACCES` creating directories under `/tmp/opencode`; policy/runtime merge
  test passed. No retry, dependency install or alternate fixture path attempted.
- **Next action:** human reviews the BOARD-116 task commit; parent approved all 12 file diffs
  and authorized a local docs-only commit through the existing Kilo bootstrap guard.
  BOARD-114 remains blocked and
  not merge-ready; it separately awaits user authorization of a
  writable fixture location or repair of temporary-directory access.
