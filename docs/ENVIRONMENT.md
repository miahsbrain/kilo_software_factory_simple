# ENVIRONMENT — software factory

Environment variables and config keys only. Placeholders only — never real secret values.
The user populates real secrets.

| Variable | Where used | Required | Default | Notes |
|---|---|---|---|---|
| `BASH_ENV` | the whole dev container | no | `/home/node/.kilo-redact.sh` | Points bash at the startup file that scrubs credentials from command output and refuses any `bash -c` command that names a protected file. Set by `devcontainer.json` → `remoteEnv`. If the file is missing bash ignores it. |
| `KILO_CONFIG` | the whole dev container | no | `${containerWorkspaceFolder}/kilo.jsonc` | Loads the permission map in every folder and every nested repository, so the protected-file denies apply without a copied config. Set by `devcontainer.json` → `remoteEnv`. |
| `REMOTE_CONTAINERS_IPC` | VS Code Dev Containers | no | set by VS Code | The socket the VS Code credential helper talks to. Not set by hand. |
| `OPENROUTER_API_KEY` | the agent's model provider | no | — | Value lives in the host environment and is passed through `remoteEnv`. |
| `DEEPSEEK_API_KEY` | the agent's model provider | no | — | Value lives in the host environment and is passed through `remoteEnv`. |
| `CARGO_BUILD_JOBS` | Rust builds | no | `2` | Passed through `remoteEnv` from `FACTORY_CARGO_JOBS`. |
| `QA_TEST_EMAIL` | approved QA navigation `fill.env` example | no | none | User supplies authorized test access outside CLI/evidence/commits. |
| `QA_TEST_PASSWORD` | approved QA navigation `fill.env` example | no | none | Name only; never read or print the value. MFA/SSO is manual user login. |

## Config keys

| Key | Where | Notes |
|---|---|---|
| `/home/node/.kilo-redact.sh` | the whole dev container | The startup file. It scrubs credentials from command output and refuses `bash -c` commands that name a protected file. Installed by `postCreateCommand` from `.devcontainer/kilo-redact.sh`. |
| `/home/node/.git-credentials` | the whole dev container | The git credential store, mode `600`. Never commit it and never read it into a transcript. |
| `/home/node/.gitconfig` | the whole dev container | Holds `credential.helper`, `user.*` and `safe.directory`. It must not hold a `url.*.insteadOf` rewrite that embeds a credential. |
| `mode` | control repo common Git directory `kilo-workspace.json` | Project-local `required` (default) or `optional`; regenerate permissions and restart Kilo after changing. |
| `approved`, `login`, `authenticatedPath`, `authenticatedSelector`, `steps` | ignored local QA navigation JSON | Storage-state or login requires an app-specific visible signed-in marker checked after navigation settles; page-changing navigation declares final destination via waitForURL. No password-input heuristic. Never commit credential/session JSON. |

## Rules

- Builders may create or update `.env.example` files.
- Builders do not edit real `.env` files; use `.env.example` placeholders only.
- Real secrets are never generated, requested, stored, or committed by an agent.
- Stack, commands, and ports belong in `docs/STACK.md`, not here.
- A credential never goes in a URL, a command line, a config value that a command prints, or a
  document. The redaction file scrubs it from command output; that is the backstop, not the plan.
