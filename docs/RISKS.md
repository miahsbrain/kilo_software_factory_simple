# RISKS

Active architectural and project risks. Short bullets only.

- **Documentation drift risk:** with no commits and no PRs, doc updates depend on the agent
  following AGENTS.md §B1 in the same change set. Mitigation: every task ends with the
  Definition of Done checklist.
- **Not yet a git repository:** the workspace has no `.git`, so Agent Manager worktrees cannot be
  created and the worktree workflow (§B4) cannot run. Mitigation: `git init` + a first commit
  by the user is required before the first feature worktree.
- **Bootstrapping the repo:** the first commit lands on `main` and must be made before any
  worktree can branch from it. After that, every change happens on a worktree branch (ADR-015).
- **Uncommitted board on `main`:** after each merge the orchestrator edits `docs/BOARD.md` to mark
  the row `Merged`, leaving one uncommitted change for the user to commit (§B3).
