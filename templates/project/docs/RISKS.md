# RISKS

Active architectural and project risks. Short bullets only.

- **Documentation drift risk:** doc updates depend on the agent following AGENTS.md §B1 in the
  same change set as the code. Mitigation: every task ends with the Definition of Done checklist.
- **Bootstrapping the repo:** the first commit lands on `main` and must exist before any worktree
  can branch from it. Required mode uses worktrees; optional permits assigned nonprotected checkouts.
- **Partial lifecycle operations:** multi-repo merge is non-atomic. Preserve progress/conflicts;
  the human completes/retries. Mark Merged only when every required surface completes.
- **Explicit discard loses work:** preview first; user-approved --apply --discard can remove
  selected dirty/unmerged mapped linked worktrees/feature branches. Never discard unasked.
- **Authenticated evidence:** known credentials/session masking does not remove arbitrary
  sensitive page content. Use authorized test access, ignored local JSON and inspect evidence.
- **Target permissions:** required-mode edit permissions may block conflicted targets outside
  linked worktrees. Stop for an approved permission decision rather than bypass the guard.
- **Optional lifecycle coverage:** optional checkout edits/commits do not imply lifecycle
  handoff/merge/discard accept nonlinked source checkouts; current commands validate linked worktrees.
