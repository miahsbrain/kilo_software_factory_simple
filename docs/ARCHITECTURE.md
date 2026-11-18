# Factory Lifecycle Architecture

## Scope

This document covers the factory's worktree lifecycle and policy boundary only. It does not
define product or application architecture.

## Shape

- `worktree.py` is the lifecycle entrypoint for board-linked worktrees: create, resume, discard,
  handoff, list, verify and cleanup.
- `env.py` delegates local-input provisioning to the same safe copier used by lifecycle creation.
  It handles ignored or untracked regular `.env*` files except `.env.example`, plus the ignored
  QA navigation input, without exposing values to agents.
- The control repository's main checkout owns board writes. A worktree branch holds application
  changes and scope documentation, but never edits the live board.
- `.kilo/policies/git-policy.json` is the source of truth for command permissions; generated
  configuration carries the enforcement map.
- Human approval separates review and merge from teardown. The lifecycle CLI performs teardown;
  raw Git worktree removal is not an alternate path.

## Lifecycle Invariants

- Resume reuses an existing linked worktree and does not recopy local inputs.
- Provisioning skips tracked sources, symlinks, non-regular files and existing destinations,
  preserves source modes, and records copied paths in shared Git excludes.
- Cleanup is for merged work and sets a row to `Merged` when run by board ID.
- Discard is human-only and requires `--apply --discard`; it permanently removes the selected
  worktree and branch without backups. The final linked row becomes `Dropped`.
- Refused teardown leaves both the worktree and board state unchanged.
