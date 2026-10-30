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
- **Active task:** BOARD-001 — documented on branch `docs/document-all-75-microservices-and-their`
  in `.kilo/worktrees/document-all-75-microservices-and-their`, waiting for the user to merge.
- **Next step:** the user merges `docs/document-all-75-microservices-and-their` into `main`. Then
  the first defect row is opened — the risk register in `docs/RISKS.md` already carries the ranked
  list, with the cross-tenant credential bleed in `payment_gateway_ms` first.

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
