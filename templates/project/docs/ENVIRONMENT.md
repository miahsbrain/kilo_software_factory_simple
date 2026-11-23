# ENVIRONMENT

Environment variables and config keys only. Placeholders only — never real secret values.
The user populates real secrets.

| Variable | Where used | Required | Default | Notes |
|---|---|---|---|---|

## Config keys

| Key | Where | Notes |
|---|---|---|
| `mode` | common Git directory `kilo-workspace.json` | Project-local required (default) / optional; regenerate permissions and restart Kilo. |
| `.kilo/local/qa-auth.json`, `.kilo/local/qa-storage-state.json` | standalone QA capture | Human prepares ignored, private state for this project. See the installed [setup and renewal](../.kilo/skills/qa-review/SKILL.md#authentication); no login environment variables required. |

## Rules

- Builders may create or update `.env.example` files.
- Builders do not edit real `.env` files; use `.env.example` placeholders only.
- Real secrets are never generated, requested, stored, or committed by an agent.
- Stack, commands, and ports belong in `docs/STACK.md`, not here.
