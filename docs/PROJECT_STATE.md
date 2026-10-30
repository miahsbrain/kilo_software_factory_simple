# PROJECT STATE

- **Phase:** Setup — factory scaffold complete, repository bootstrapped, no application yet.
- **Progress:** Documentation, orchestration rules, the agent team (`.kilo/agent/`), the command
  surface (`.kilo/command/`), and the CLI-only worktree skill (`.kilo/skills/git-worktree/`) are
  in place. The QA capture path drives Playwright only, and a missing browser is reported rather
  than installed (`AGENTS.md` §B6.2). The guard-rail policy (`.kilo/policies/git-policy.json`) is
  in place and feeds two layers: the generated `permission` map in `kilo.jsonc` and
  `guard.py check-git`, which adds the context checks a keyword list cannot make. The repo is now
  a starter: root `README.md` in place, test capture removed, board empty.
- **Active task:** BOARD-001 in progress on branch `feat/add-a-permission-file-and-git`.
- **Next step:** the user merges `feat/add-a-permission-file-and-git` into `main`, then the
  discovery interview (`/decide`) runs for the first project in this checkout and the first board
  row is added with `board.py add`.
