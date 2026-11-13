# HANDOVER — <Project name>

> **Session Notes** (keep at the very top, updated every session)
> - **Last session:** —
> - **In flight:** none.
> - **Next action:** run the discovery interview (`/decide`) and fill `DOMAIN.md`.

## 1. Overview

- **What it is:** TBD
- **Who uses it:** TBD
- **Tech stack:** see `docs/STACK.md`.
- **How to run it:** see `docs/STACK.md`.

## 2. Directory map

| Path | Contents |
|---|---|

## 3. Entry points

| Entry point | What it does |
|---|---|

## 4. Modules, classes and functions

| Symbol | File | Responsibility | Pure or effectful |
|---|---|---|---|

## 5. Data

The live `docs/BOARD.md` is local, Git-ignored workspace state. Tooling creates it when absent in the control repo’s main checkout. Never overwrite an existing board or copy it into task worktrees. Only the orchestrator edits its rows through `board.py`.

The factory's `templates/project/docs/BOARD.md` is a tracked, non-runtime starter. Its bytes are
retained for historical context; root `AGENTS.md` owns the current board rules. After copying the
skeleton, the project's `.gitignore` excludes its runtime board from the initial Git add.

| Model or table | Where | Fields and validation |
|---|---|

## 6. States and state transitions

| State | Valid next states | Trigger | Guard |
|---|---|---|---|

## 7. Public API and interfaces

| Route or event | Method | Request | Response | Auth |
|---|---|---|---|---|

## 8. Configuration and environment

| Variable | Where used | Required | Default |
|---|---|---|---|

## 9. Dependencies

| Dependency | Why it is used |
|---|---|

## 10. Testing

- **How to run the tests:** see `docs/STACK.md`.
- **What is covered:**
- **What is not covered:**

## 11. Known issues and risks

## 12. Open questions

## 13. Document map

- [DOMAIN.md](../DOMAIN.md) — product scope and terminology.
- [ROADMAP.md](../ROADMAP.md) — planned work not in progress.
- [AGENTS.md](../AGENTS.md) — the rules.
