# Factory documentation

| Doc | What it answers |
|---|---|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Where does everything live? |
| [HANDOVER.md](HANDOVER.md) | What is this app right now? Entry points, functions, data, states, pure vs effectful. |
| [handover/](handover/) | What is the whole application? One memory map per application plus the global index. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How is it built and why? Domain, layers, decisions, roadmap. |
| [BUSINESS-LOGIC.md](BUSINESS-LOGIC.md) | How does it behave? Question → answer with rules and `file:line`. |
| [UI-UX.md](UI-UX.md) | What should it look like? References, anti-slop rules, component factory gate, Playwright QA spec. |
| [BOARD.md](BOARD.md) | What is in flight? One row per unit of work, with lanes and acceptance criteria. |
| [STACK.md](STACK.md) | What stack and commands do we use? |
| [PROJECT_STATE.md](PROJECT_STATE.md) | Where are we right now? |
| [DECISIONS.md](DECISIONS.md) | What was decided, and why? |
| [RISKS.md](RISKS.md) | What could bite us? |
| [API_CONTRACTS.md](API_CONTRACTS.md) | What shape is the API? |
| [ENVIRONMENT.md](ENVIRONMENT.md) | Which env vars and config keys exist? |
| [changelog/CHANGELOG.md](changelog/CHANGELOG.md) | What changed, and why? (engineering log) |

Skills (`.kilo/skills/`):

| Skill | Script | Does |
|---|---|---|
| `git-worktree` | `worktree.py`, `guard.py` | create/verify/cleanup the worktree; block deletes outside it |
| `board` | `board.py` | add rows, move lanes, set cells — never hand-edit the table |
| `qa-review` | `browser-review.mjs`, `check-finding.py` | Playwright evidence capture; finding validation |

Agents (`.kilo/agent/`): `frontend-dev`, `backend-dev`, `mobile-dev`, `qa-reviewer`, `ui-critic`, `docs-writer`.

Commands: `/decide` (decision sheet before implementation), `/board` (live board + next task),
`/run` (Build → QA → Review for one row), `/components` (component factory + gallery, user
approves), `/ui` (Playwright QA + UI/UX critique), `/handover` (read the codebase and write the application memory map), `/closeout`
(docs + changelog, then hand the worktree to the user).

Root-level: [AGENTS.md](../AGENTS.md) (rules), [DOMAIN.md](../DOMAIN.md) (product scope),
[ROADMAP.md](../ROADMAP.md) (planned work), [CHANGELOG.md](../CHANGELOG.md) (product-facing
changelog, user-approved only).

Everything here is maintained by the agent as part of the code change — see
[../AGENTS.md](../AGENTS.md). Templates live in this folder and are meant to be filled in,
not left as placeholders.
