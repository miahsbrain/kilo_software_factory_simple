# Document the microservice fleet

**Date:** 2026-10-30
**Board:** BOARD-001
**Branch:** `docs/document-all-75-microservices-and-their`

## What changed

The Inhouz Cloud AI platform is 75 microservices, each its own git repository under `apps/`. The
control repo had no git repository at all, no board row for the platform, and an application memory
map that described the empty scope folders rather than the fleet.

This change does four things.

**1. It gives the control repo a history.** `git init -b main`, a `.gitignore` that ignores
`apps/*/` (nested repositories are not tracked by their parent) and re-includes the three scope
folders, and one seed commit. That commit is the only commit on `main`; everything after it lands
on a worktree branch. Without it there was no worktree, no board branch and no merge gate.

**2. It registers every repository.** `.kilo/repos.json` now maps `control`, the three scope
folders and all 75 microservice repositories, each under an id equal to its folder name.
`guard.py check-repos` exits 0.

**3. It writes the memory map.** 75 handover files under `docs/handover/`, one per microservice,
each with the 14 sections of the docs-writer contract and `file:line` evidence on every claim.
Plus a global index at `docs/handover/README.md` carrying the domain-level system map, the
86-edge HTTP call graph between distinct services, the 178-collection shared-database map and the
external-API matrix.

**4. It rewrites the governance documents to describe the real system.** `docs/ARCHITECTURE.md`,
`docs/STACK.md`, `docs/API_CONTRACTS.md`, `docs/RISKS.md`, `docs/PROJECT_STRUCTURE.md`,
`docs/PROJECT_STATE.md` and `docs/DECISIONS.md`.

## How the relationship map was derived

Not from a written diagram. From the code and the manifests:

- **The call graph** — every `http://<service>-ms-cluster-ip-service:<port>` literal in every
  repository, with the first `file:line` where each appears. The target is resolved through the
  k8s ClusterIP service name, so the edge names a real service, not a hostname.
- **The port registry** — each repository's `k8s/*-cluster-ip-service.yml`, which declares the
  service name and the port. The `targetPort` of the ingress was read from the same place.
- **The shared-collection map** — each deployment's `*_MODEL` environment variables, whose *values*
  are the MongoDB collection names. This is the only place the collection-to-service mapping is
  written down, and it is why 143 of the 178 collections have more than one writer.
- **The external-API matrix** — the provider is an npm dependency, an HTTP call in the code, or a
  k8s secret reference.

The extraction was a one-off analysis over the source, run outside the repository. It added no
tool to the project (AGENTS.md §B6.1).

## Why the agents were fanned out and how they were bounded

75 services and 1.32M lines of JavaScript is more than one agent can read. The first fan-out had
each agent read its whole cluster before writing anything; six agents ran out of step budget with
**no file on disk**.

The fix was to change the order, not the budget:

- A script extracted a per-service **skeleton** — the route table with `file:line`, the mongoose
  registrations, the timers, the env vars read, the external requires — into one 150-line file per
  service. The agent verifies the skeleton instead of re-deriving it.
- The instruction became **write-first**: read one service's brief, verify it, write that service's
  file, then move to the next. A partial file that follows the template beats a missing file.
- Clusters were cut to 3-6 services.

Every service ended up with a file. The clusters that still ran out of budget were re-dispatched
with the evidence already gathered, so the second pass only had to write.

## What the documentation found

The map is not only a map. It surfaced defects that the next rows will fix:

- A **cross-tenant credential bleed** in the payment distribution worker: `STRIPE_KEY` is assigned
  without a declaration, so it is an implicit global and two concurrent tenants can overwrite each
  other's Stripe secret key.
- A **payout approval handler** that treats every status other than `rejected` as an approval.
- A **double-charge risk** in the late-payment worker: the charge is created before the intent is
  marked paid, with no transaction.
- **Unrestricted outbound request proxies** in the remote network request service and the image
  proxy, and **caller-supplied SQL** with no allow-list in the database execution service.
- **`$lookup` stages hardcode `companies` and `users`** while the models register `company` and
  `User` — every company-name projection is empty.
- **12 services cannot boot**: their Dockerfile runs `npm run start` and their `package.json` has
  no `start` script.
- **The health check can never pass**: 71 `healthcheck.js` files request `/healthz` and no service
  registers it.
- **No test suite anywhere.** Every `package.json` carries the placeholder `test` script.

The full ranked list is in `docs/RISKS.md`; the per-service detail is in each handover file,
section 12.

## A correction

The first pass reported the GitHub token as embedded in each repository's `.git/config`. That was
wrong. The repositories' remotes are clean — `git config --get remote.origin.url` returns a plain
`https://github.com/Inhouz-Cloud-AI/<repo>.git`. The token comes from the machine's **global** git
config, which defines a `url.https://<token>@github.com/.insteadOf https://github.com/` rewrite,
so `git remote -v` prints it even for a clean remote. Six handover files carried the wrong claim
and were corrected. The consequence is the same either way — the token reaches logs and agent
transcripts — but the location matters for the fix.

## Impact

No application behaviour changes. No microservice repository is touched. The control repo gains a
history, a populated board and a documentation set that describes the platform it holds.
