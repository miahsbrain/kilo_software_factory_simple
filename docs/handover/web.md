# HANDOVER — `web` unit

Every claim below carries a `file:line` citation. A row without one was dropped.

Written by the `docs-writer` agent (`.kilo/agent/docs-writer.md:8`). Mode: **full read** of
`apps/web/`.

## 1. Summary

The web scope exists as a placeholder. The folder `apps/web/` holds exactly one file,
`apps/web/AGENTS.md:1`, the scope rules for the web builder. There is no source, no package
manifest, no build, no server and no test file. The unit is a rulebook for code that has not been
written yet, and nothing may be written into it before the decision gate and the discovery
interview have run (`AGENTS.md:145`).

## 2. Stack and commands

| Item | Value |
|---|---|
| Stack | `TBD` — `docs/STACK.md:25` |
| Package manager | `TBD` — `docs/STACK.md:28` |
| Dev command | `TBD` — `docs/STACK.md:29` |
| Verification command | `TBD` — `docs/STACK.md:30` |
| Port | `15173` — `docs/STACK.md:31` |

The stack is decided by the user at the decision gate (`AGENTS.md:214`); nothing is guessed. The
scope rules also say the stack comes from `docs/STACK.md` (`apps/web/AGENTS.md:14`).

## 3. Entry points

None yet. There is no executable, no dev server, no route and no script in this scope. The files
the scope will own once it is built are named by its own rules (`apps/web/AGENTS.md:19`):

- pages
- components
- services
- hooks
- stores/context
- lib
- styles
- assets
- tests

The web scope must build a component factory and a gallery route before any screen
(`apps/web/AGENTS.md:48`), and that gallery is approved by the user (`AGENTS.md:561`).

## 4. Module inventory

| Symbol | file:line | Responsibility | Public API | Kind |
|---|---|---|---|---|
| `apps/web/AGENTS.md` | `apps/web/AGENTS.md:1` | The scope rules for the web builder: scope, structure, code style, the component factory gate, visual quality, QA, production expectations, verification. | The rules themselves. | not code — a Markdown rules file, so it carries no pure/reactive/effectful kind |

There is no other file in this scope, so there is no other row.

## 5. Side effects

None. There is no code in this scope, so it touches no database, network, filesystem, env, clock,
randomness source or logger. The rules it will impose on the code that arrives are about
structure and quality (`apps/web/AGENTS.md:19`), not effects.

## 6. State and state transitions

None yet. The scope rules name `stores/context` as a place the future code will hold state
(`apps/web/AGENTS.md:19`), but no state, no store and no transition exists today.

```mermaid
stateDiagram-v2
    [*] --> NoCode : the scope holds only its rules file
    NoCode --> Built : the stack is approved and the first row is built
```

## 7. Data

None. No models, schemas, collections or migrations exist in this scope. The data contracts for
the application will live in `docs/API_CONTRACTS.md:1`, which is still a placeholder.

## 8. Public interfaces

None yet. No routes, events, queue topics or CLI commands are exposed by this scope. The future
HTTP routes of the web app are separate from the server-side routes of the `api` unit; the
contract between them is not written yet.

## 9. Configuration

None. No env var or config key is used by this scope. `docs/ENVIRONMENT.md:1` holds the empty
table for the whole repository. Names only would be recorded here; values are never written
(`AGENTS.md:1469`).

## 10. Dependencies

None yet. There is no `package.json` in this scope, so the unit has no direct dependency. The
scope rules forbid adding a dependency that the task does not justify
(`apps/web/AGENTS.md:19`).

## 11. Testing

None. There is no test runner, no test file and no CI in this scope. The scope rules require the
verification command from `docs/STACK.md` (`apps/web/AGENTS.md:123`), which is `TBD` today. Once
an interface exists, the QA lane captures Playwright evidence (`AGENTS.md:1208`).

## 12. Known issues and risks

- **The scope rules are written but no application has been built.** Every section of this
  handover is empty because the scope holds one rules file
  (`apps/web/AGENTS.md:1`). That is the truth, not a gap in the read.
- **The stack is `TBD`** (`docs/STACK.md:25`), so no command in this scope can be run, and the
  UI gate cannot be cleared.
- **The visual language is not decided.** Tokens, component factory and gallery route do not
  exist (`AGENTS.md:557`).

## 13. Module map

```mermaid
graph TD
    AGENTS["apps/web/AGENTS.md:1 — scope rules (not code)"]
```

One node, because the scope holds one file. When code arrives it will grow: a component factory
and a gallery first, then screens (`apps/web/AGENTS.md:48`).

## 14. Open questions

- What application will this scope build? `DOMAIN.md:1` is `TBD` and the discovery interview
  (`AGENTS.md:145`) has not run.
- Which framework, package manager and verification command? `docs/STACK.md:25` is `TBD`.
- Will the web scope be the first unit built, or the api or mobile scope? The order decides
  which builder agent is needed first.
