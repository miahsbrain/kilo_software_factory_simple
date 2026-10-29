# RISKS

Active architectural and project risks. Short bullets only.

- **Documentation drift risk:** doc updates depend on the agent following AGENTS.md §B1 in the
  same change set as the code. Mitigation: every task ends with the Definition of Done checklist.
- **Bootstrapping the repo:** the first commit lands on `main` and must exist before any worktree
  can branch from it. After that, every change happens on a worktree branch (ADR-015).
- **Uncommitted board on `main`:** after each merge the orchestrator edits `docs/BOARD.md` to mark
  the row `Merged`, leaving one uncommitted change for the user to commit (§B3).
