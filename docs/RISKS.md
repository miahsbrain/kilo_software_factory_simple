# Factory Lifecycle Risks

- **Permanent discard:** `discard --apply --discard` removes dirty or unmerged work without a
  recovery backup. The explicit human-only consent flags and default preview are the control.
- **Local input provenance:** cleanup must not remove files that were not provisioned by the
  lifecycle. Provenance tracking and skipped existing destinations limit accidental deletion.
- **Documentation drift:** lifecycle behavior spans scripts, policy, generated configuration and
  governance docs. ADRs, handover, skill guidance and focused lifecycle tests must change together.
- **Shared board state:** board-linked teardown writes the control repository's main checkout;
  partial multi-worktree discard can leave linked rows active until each is handled.
