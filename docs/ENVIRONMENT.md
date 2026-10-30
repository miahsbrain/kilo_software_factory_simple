# ENVIRONMENT

Environment variables and config keys only. Placeholders only — never real secret values.
The user populates real secrets.

| Variable | Where used | Required | Default | Notes |
|---|---|---|---|---|
| | | | | |

## Rules

- Builders may create or update `.env.example` files.
- Builders may create `.env` files only with empty values or dummy placeholders.
- Real secrets are never generated, requested, stored, or committed by an agent.
- Stack, commands, and ports belong in `docs/STACK.md`, not here.
