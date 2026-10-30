# PROJECT STATE

- **Phase:** Documentation — the fleet is mapped; no application change has been made.
- **Progress:** The control repo is a git repository with a seed commit on `main` (ADR-043). The 75
  microservice repositories under `apps/` are registered in `.kilo/repos.json`, and
  `guard.py check-repos` exits 0. The application memory map is complete: **75 handover files, one
  per microservice**, each with the 14 sections of the docs-writer contract and `file:line`
  evidence, plus a global index at `docs/handover/README.md` carrying the system map, the 86-edge
  HTTP call graph, the shared-collection map and the external-API matrix.
  `docs/ARCHITECTURE.md`, `docs/STACK.md`, `docs/API_CONTRACTS.md`, `docs/RISKS.md` and
  `docs/PROJECT_STRUCTURE.md` now describe the real system.
  A GitHub token that sat in the machine's global git config has been moved into a credential
  store behind git's credential helper, and every shell command the agent runs now has its output
  scrubbed by the container's `$BASH_ENV` redaction filter (ADR-049, ADR-050).
- **Active task:** BOARD-002 — the credential redaction filter, on branch
  `chore/redact-credentials-from-every-shell-command` in
  `.kilo/worktrees/redact-credentials-from-every-shell-command`.
- **Next step:** two things, both owned by the user. **Rebuild or reopen the dev container** so
  `remoteEnv.BASH_ENV` takes effect and the filter loads for every shell command. Then **rotate
  the GitHub token** at GitHub — it was printed in plaintext once, before the fix. After that the
  first defect row opens from the risk register in `docs/RISKS.md`, with the cross-tenant
  credential bleed in `payment_gateway_ms` first; it lives in that service's own repository, so
  the row names that repo in its `Repos` cell and the worktree is created there with
  `worktree.py create --board <id> --repo payment_gateway_ms`.

## The shape of the system, for the next agent

- 75 microservices, one Kubernetes cluster, one shared MongoDB, one tenant model (`company`).
- 178 collections, 143 written by more than one service. The service boundary is real at the HTTP
  layer and absent at the data layer.
- 86 HTTP call edges between distinct services. The public surface is declared in exactly one file:
  `apps/authentication_ms/k8s/inhouz-ingress-service.yml`.
- **No test suite exists.** Every `package.json` carries the placeholder `test` script. Any row
  that changes service behaviour has to state its own verification step.
- **No shared package.** The tenant model, the auth middleware, the crypto helper and the
  sanitizer are copied into every repository, and the copies have drifted.
