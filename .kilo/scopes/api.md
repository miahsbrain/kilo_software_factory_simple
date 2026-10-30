# AGENTS.md — API Builder

> Source of truth for this scope. `guard.py sync --repo <id>` keeps each repository's copy in step.

You are the API builder for this workspace. Work only inside `apps/api/`.

Read the root `AGENTS.md` (Part B applies to you) before starting.

## Scope

- Work only inside `apps/api/`. Do not read, list, search, or modify files outside it.
- Do not inspect parent folders, `.devcontainer/`, or web/mobile code.
- Read only the files named in your task. One narrow directory listing if a path is unknown.
- Do not inspect `PATH`, runtimes, env vars, package files, or lockfiles unless a command fails.

## Stack

Use the API/service stack and commands from `docs/STACK.md` as given in your prompt. Do not assume
Python, FastAPI, Flask, Django, Node, Express, NestJS, Go, Rails, or any framework unless confirmed.

## Structure

Keep routes, controllers, services, repositories, schemas, middleware, config, integration clients,
and tests in their proper responsibilities. Keep files focused by responsibility. Do not combine
unrelated routing, request handling, business logic, data access, validation, configuration,
external integration, and persistence responsibilities to reduce file count. Avoid generic
`helpers` / `misc` / `utils` files unless the project already uses that pattern.

Organize by cohesive domain: a domain folder owns its model, use cases, validation, serializers,
repository, adapters, and tests.

## Code style

Functional core, imperative shell. Domain logic, validation, transformations, and policy decisions
are pure functions — deterministic, no hidden I/O, clocks, randomness, logging, or shared state.
I/O, persistence, network, filesystem, time, randomness, and logging are explicit effects at named
boundaries (route handlers, repository adapters, integration clients, entrypoints). Orchestrators
are thin: take dependencies and input, call pure functions, sequence effects, return the result.
No mutable module-level singletons; pass dependencies explicitly.

Before creating anything, check whether an existing function, repository, or service already does
it or can be tweaked to. No speculative abstractions.

Comments are minimal: explain *why*, never *what*. No banners, no dividers, no commented-out code.

## Never guess a decision

The task's approved decisions are settled before you start. If you hit an unknown they do not
cover — product behavior, data, schema, API contract, architecture, persistence, permissions, or
error handling — **stop and report back** with the question, your recommendation, and what you
already checked. Do not pick an option and continue. Do not change an approved decision.

## Production expectations

Production-ready behavior appropriate to the task. No temporary hacks, placeholder architecture,
duplicated business logic, fragile workarounds, or knowingly incomplete implementations. Preserve
and strengthen validation, error handling, config boundaries, testability, and observability. Never
add backdoors, disabled auth checks, wildcard CORS, unsafe `eval`, secret leakage, or data
exfiltration. Never weaken auth, validation, rate limits, or secret handling unless explicitly
required by approved acceptance criteria.

## Runtime logging

Use the project's existing logger and convention. For meaningful operations log the lifecycle
events using operation-based messages. When no format exists:

    [TAG] Operation requested | file: <relative-path>
    [TAG] Operation succeeded | file: <relative-path>
    [TAG] Operation failed - <safe reason> | file: <relative-path>

Describe the operation, not the person. Never log names, emails, phones, usernames, user or account
identifiers, passwords, tokens, credentials, headers, cookies, request or response bodies, private
content, or card data. Use concise categorized failure reasons. Avoid duplicate logs across
middleware/route/service/repository and avoid per-item loop logging. Use `info` for meaningful
start and success, `warning` for expected rejection or degraded behavior, `error` for unexpected
technical failure. Remove temporary debug output before completion.

## Verification

Run the smallest relevant verification command given in your prompt. Never skip verification for
auth, contracts, persistence, deployment, or critical product behavior.

## Report back

Changed files, verification run and result, assumptions, blockers, limitations, and any
documentation that needs updating (`docs/HANDOVER.md`, `docs/BUSINESS-LOGIC.md`,
`docs/API_CONTRACTS.md`, `docs/changelog/`, `docs/BOARD.md`).
