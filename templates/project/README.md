# <Project name>

One paragraph: what this project is and who uses it.

## Quick start

Before the first commit, follow the factory README's **New project** commands from the factory
root: copy this skeleton, then `.kilo/agent`, `command`, `skills`, `policies`, `scopes`, `catalog`,
`.kilo/.gitignore` and the generated `kilo.jsonc`. Keep this project's `AGENTS.md` and
`.kilo/repos.json`; do not overwrite them with factory versions. The skeleton alone does not
contain the harness. No second harness tree is maintained in the template.

Bootstrap appends `/docs/BOARD.md` to the destination `.gitignore` before the first commit.
The skeleton cannot include that rule: it would also ignore the factory's blank template board,
overriding the factory's exception. The copied project's live board stays local and ignored.

```bash
# install
# run
# test
```

## Documentation

- `DOMAIN.md` — product scope, terminology, business rules.
- `docs/STACK.md` — the stack, the commands, the ports.
- `docs/HANDOVER.md` — what the application is right now.
- `docs/BOARD.md` — local, ignored live board, initialized from the factory's tracked blank template.
- `docs/ARCHITECTURE.md` — how it is built and why.
- `docs/BUSINESS-LOGIC.md` — how it behaves.
- `docs/API_CONTRACTS.md` — the API surface.
- `docs/RISKS.md` — what could go wrong.
- `docs/DECISIONS.md` — the decisions and why they were made.

This repository was created from the software factory's `templates/project/` skeleton. The harness
(`AGENTS.md`, `.kilo/`, the permission map) is a copy the project owns; see the factory's
`AGENTS.md` §A1.
