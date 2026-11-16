# ENVIRONMENT

Environment variables and config keys only. Placeholders only — never real secret values.
The user populates real secrets.

| Variable | Where used | Required | Default | Notes |
|---|---|---|---|---|
| `QA_TEST_EMAIL` | QA navigation `fill.env` example | no | none | Authorized test account; user supplies outside CLI/evidence/commits. |
| `QA_TEST_PASSWORD` | QA navigation `fill.env` example | no | none | Name only; never print its value. Manual user MFA/SSO, never bypass. |

## Config keys

| Key | Where | Notes |
|---|---|---|
| `mode` | common Git directory `kilo-workspace.json` | Project-local required (default) / optional; regenerate permissions and restart Kilo. |
| `approved`, `login`, `authenticatedPath`, `authenticatedSelector`, `steps` | ignored local navigation JSON | Storage-state or login requires an app-specific visible signed-in marker checked after navigation settles; page-changing navigation declares final destination via waitForURL. No password-input heuristic. Storage state is also local/ignored. |

## Rules

- Builders may create or update `.env.example` files.
- Builders do not edit real `.env` files; use `.env.example` placeholders only.
- Real secrets are never generated, requested, stored, or committed by an agent.
- Stack, commands, and ports belong in `docs/STACK.md`, not here.
