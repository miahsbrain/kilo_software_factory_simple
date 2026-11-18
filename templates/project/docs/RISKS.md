# RISKS

Active architectural and project risks. Short bullets only.

- **Documentation drift:** keep affected essential docs current with changes, without exhaustive inventories.
- **Bootstrap:** worktrees need an existing commit. Initialize Git after the full harness copy,
  but obtain explicit authorization before staging or making an initial commit.
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
