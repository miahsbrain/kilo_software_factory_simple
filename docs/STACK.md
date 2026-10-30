# STACK

Approved stack, package managers, commands, and ports. This is the first source for any command
an agent needs. Do not guess commands. Do not read `docs/ENVIRONMENT.md` for stack information.

## How to run in development

```bash
# Board viewer (from the repo root)
python3 .kilo/skills/board/scripts/board_serve.py --port 15180

# Clone every microservice repository into apps/ (from apps/)
./clone_repos.sh

# Any microservice (from apps/<unit>/)
npm install
npm start
```

The board viewer is read-only: it serves the board and the live worktree state, and never writes
to either. It re-reads `docs/BOARD.md` on every request, so the page is always current.

## The microservice fleet

**75 microservices, each its own git repository under `apps/`.** The control repo does not track
them; `.kilo/repos.json` maps every repo id to its path.

- **Runtime:** Node.js. The declared engine is `>=12.0.0 <17.5.0` in most repos; the Dockerfiles
  are built on Node 16.4-alpine.
- **Framework:** Express 4.
- **Data:** Mongoose 7 over MongoDB.
- **Package manager:** npm. Only `functions_ms` and `inhouzio_app_ms/client` carry a lockfile.
- **Realtime:** Socket.IO with a Redis adapter (`websocket_ms`).
- **Cache:** Redis, in five services.
- **Tests:** **none.** Every `package.json` carries the placeholder
  `"test": "echo \"Error: no test specified\" && exit 1"`. There is no test suite in the fleet.

### Commands

| Command | What it does | Where |
|---|---|---|
| `npm start` | runs the service | `apps/<unit>/` |
| `npm test` | the placeholder that always exits 1 | `apps/<unit>/` |
| `npm run build` | builds the React client | `apps/inhouzio_app_ms/client/` |

**12 of the 75 services have no `start` script** while their `Dockerfile` runs `npm run start` —
the image cannot boot. The units are listed in the table below with `no \`start\` script`.

### Ports, services and images

Port is the ClusterIP service port. A worker has no ClusterIP service: it is reached by a
scheduler inside the cluster.

| Unit | Port | k8s service | Image | Start command |
|---|---|---|---|---|
| `account_termination_cron_ms` | — | `— (worker)` | `inhouz/account_termination_cron_ms` | node server.js |
| `account_termination_ms` | 5048 | `account-termination-ms-cluster-ip-service` | `inhouz/account_termination_ms` | node server.js |
| `api_service_ms` | 5010 | `api-service-ms-cluster-ip-service` | `inhouz/api_service_ms` | node server.js |
| `app_builder_ms` | 5016 | `app-builder-ms-cluster-ip-service` | `inhouz/app_builder_ms` | node --max-old-space-size=10000 server.js |
| `app_metrics_ms` | 5054 | `app-metrics-ms-cluster-ip-service` | `inhouz/app_metrics_ms` | node --max-old-space-size=8192 server.js |
| `app_version_manager_ms` | 5074 | `app-version-manager-ms-cluster-ip-service` | `inhouz/app_version_manager_ms` | node --max-old-space-size=10000 server.js |
| `app_viewer_ms` | 3000 | `app-viewer-ms-cluster-ip-service` | `inhouz/app_viewer_ms` | SET NODE_OPTIONS=--openssl-legacy-provider && razzle start |
| `appbuilder_multiplayer_ms` | 5019 | `appbuilder-multiplayer-ms-cluster-ip-service` | `inhouz/appbuilder_multiplayer_ms` | node --max-old-space-size=8192 server.js |
| `appviewer_log_ms` | 5046 | `appviewer-log-ms-cluster-ip-service` | `inhouz/appviewer_log_ms` | node server.js |
| `appviewer_password_ms` | 5040 | `appviewer-password-ms-cluster-ip-service` | `inhouz/appviewer_password_ms` | node server.js |
| `authentication_ms` | 5002 | `authentication-ms-cluster-ip-service` | `inhouz/authentication_ms` | node server.js |
| `churn_tracker_ms` | — | `— (worker)` | `inhouz/churn_tracker_ms` | node --max-old-space-size=8192 server.js |
| `contact_ms` | 5071 | `contact-ms-cluster-ip-service` | `inhouz/contact_ms` | no `start` script |
| `customer_portal_ms` | 5062 | `customer-portal-ms-cluster-ip-service` | `inhouz/customer_portal_ms` | no `start` script |
| `data_scanner_ms` | — | `— (worker)` | `inhouz/data_scanner_ms` | node --max-old-space-size=8192 server.js |
| `database_execution_ms` | 5021 | `database-execution-ms-cluster-ip-service` | `inhouz/database_execution_ms` | node --max-old-space-size=4000 server.js |
| `document_generation_parser_ms` | 5069 | `document-generation-parser-ms-cluster-ip-service` | `inhouz/document_generation_parser_ms` | node --max-old-space-size=10000 server.js |
| `document_scheduler_ms` | — | `— (worker)` | `inhouz/document_scheduler_ms` | node --max-old-space-size=8192 server.js |
| `file_operations_ms` | 5008 | `file-operations-ms-cluster-ip-service` | `inhouz/file_operations_ms` | node server.js |
| `flex_api_ms` | 5006 | `flex-api-ms-cluster-ip-service` | `inhouz/flex_api_ms` | node server.js |
| `flex_module_collection_ms` | 5004 | `flex-module-collection-ms-cluster-ip-service` | `inhouz/flex_module_collection_ms` | node server.js |
| `function_parser_ms` | 5035 | `function-parser-ms-cluster-ip-service` | `inhouz/function_parser_ms` | nodemon lib/index.js --exec babel-node --presets es2015,stage-2 |
| `functions_ms` | 5001 | `functions-ms-cluster-ip-service` | `inhouz/functions_ms` | node server.js |
| `general_task_parser_ms` | 5042 | `general-task-parser-ms-cluster-ip-service` | `inhouz/general_task_parser_ms` | node server.js |
| `general_task_scheduler_ms` | — | `— (worker)` | `inhouz/general_task_scheduler_ms` | no `start` script |
| `image_proxy_ms` | 5034 | `image-proxy-ms-cluster-ip-service` | `inhouz/image_proxy_ms` | node server.js |
| `inhouz_commerce_ms` | 5060 | `inhouz-commerce-ms-cluster-ip-service` | `inhouz/inhouz_commerce_ms` | node server.js |
| `inhouz_file_upload_ms` | 5053 | `inhouz-file-upload-ms-cluster-ip-service` | `inhouz/inhouz_file_upload_ms` | no `start` script |
| `inhouz_pay_metrics_ms` | 5064 | `inhouz-pay-metrics-ms-cluster-ip-service` | `inhouz/inhouz_pay_metrics_ms` | no `start` script |
| `inhouz_pay_ms` | 5058 | `inhouz-pay-ms-cluster-ip-service` | `inhouz/inhouz_pay_ms` | no `start` script |
| `inhouz_pay_recurring_stats_ms` | 5063 | `inhouz-pay-recurring-stats-ms-cluster-ip-service` | `inhouz/inhouz_pay_recurring_stats_ms` | node server.js |
| `inhouz_pay_scheduler_ms` | 5061 | `inhouz-pay-scheduler-ms-cluster-ip-service` | `inhouz/inhouz_pay_scheduler_ms` | node server.js |
| `inhouz_project_ms` | 5067 | `inhouz-project-ms-cluster-ip-service` | `inhouz/inhouz_project_ms` | node --max-old-space-size=8192 server.js |
| `inhouz_security_ms` | 5068 | `inhouz-security-ms-cluster-ip-service` | `inhouz/inhouz_security_ms` | no `start` script |
| `inhouz_sign_metrics_ms` | 5070 | `inhouz-sign-metrics-ms-cluster-ip-service` | `inhouz/inhouz_sign_metrics_ms` | no `start` script |
| `inhouz_sign_ms` | 5065 | `inhouz-sign-ms-cluster-ip-service` | `inhouz/inhouz_sign_ms` | node --max-old-space-size=8192 server.js |
| `inhouz_subscription_ms` | 5041 | `inhouz-subscription-ms-cluster-ip-service` | `inhouz/inhouz_subscription_ms` | node server.js |
| `inhouz_subscription_renewal_ms` | 5044 | `inhouz-subscription-renewal-ms-cluster-ip-service` | `inhouz/inhouz_subscription_renewal_ms` | node server.js |
| `inhouz_subscription_renewal_scheduler_ms` | — | `— (worker)` | `inhouz/inhouz_subscription_renewal_scheduler_ms` | node server.js |
| `inhouzio_app_ms` | 5000 | `inhouzio-app-ms-cluster-ip-service` | `inhouz/inhouzio_app_ms` | node server.js |
| `late_payment_ms` | 5051 | `late-payment-ms-cluster-ip-service` | `inhouz/late_payment_ms` | node server.js |
| `log_manager_ms` | — | `— (worker)` | `inhouz/log_manager_ms` | no `start` script |
| `module_transfer_ms` | 5078 | `module-transfer-ms-cluster-ip-service` | `inhouz/module_transfer_ms` | no `start` script |
| `module_transfer_parser_ms` | 5077 | `module-transfer-parser-ms-cluster-ip-service` | `inhouz/module_transfer_parser_ms` | node --max-old-space-size=20000 server.js |
| `multimedia_ms` | 5013 | `multimedia-ms-cluster-ip-service` | `inhouz/multimedia_ms` | node --max-old-space-size=8000 server.js |
| `payment_gateway_ms` | 5057 | `payment-gateway-ms-cluster-ip-service` | `inhouz/payment_gateway_ms` | node server.js |
| `payment_link_ms` | 5059 | `payment-link-ms-cluster-ip-service` | `inhouz/payment_link_ms` | node server.js |
| `payment_ms` | 5014 | `payment-ms-cluster-ip-service` | `inhouz/payment_ms` | node server.js |
| `payment_validation_ms` | 5050 | `payment-validation-ms-cluster-ip-service` | `inhouz/payment_validation_ms` | node server.js |
| `payment_validation_scheduler_ms` | 5049 | `payment-validation-scheduler-ms-cluster-ip-service` | `inhouz/payment_validation_scheduler_ms` | node --max-old-space-size=8192 server.js |
| `pdf_generator_ms` | 5072 | `pdf-generator-ms-cluster-ip-service` | `inhouz/pdf_generator_ms` | no `start` script |
| `push_notification_parser_ms` | 5076 | `push-notification-parser-ms-cluster-ip-service` | `inhouz/push_notification_parser_ms` | node --max-old-space-size=8192 server.js |
| `remote_network_request_ms` | 5045 | `remote-network-request-ms-cluster-ip-service` | `inhouz/remote_network_request_ms` | node server.js |
| `scheduled_launch_ms` | — | `— (worker)` | `inhouz/scheduled_launch_ms` | node --max-old-space-size=8192 server.js |
| `scheduled_task_function_parser_ms` | 5038 | `scheduled-task-function-parser-ms-cluster-ip-service` | `inhouz/scheduled_task_function_parser_ms` | nodemon lib/index.js --exec babel-node --presets es2015,stage-2 |
| `scheduled_task_ms` | 5007 | `scheduled-task-ms-cluster-ip-service` | `inhouz/scheduled_task_ms` | node server.js |
| `scheduled_task_parser_ms` | 5037 | `scheduled-task-parser-ms-cluster-ip-service` | `inhouz/scheduled_task_parser_ms` | node server.js |
| `scheduled_task_scheduler_ms` | — | `— (worker)` | `inhouz/scheduled_task_scheduler_ms` | node --max-old-space-size=8192 server.js |
| `subscriber_data_function_ms` | 5055 | `subscriber-data-function-ms-cluster-ip-service` | `inhouz/subscriber_data_function_ms` | node server.js |
| `subscription_authentication_ms` | 5030 | `subscription-authentication-ms-cluster-ip-service` | `inhouz/subscription_authentication_ms` | node server.js |
| `subscription_authorization_ms` | 5031 | `subscription-authorization-ms-cluster-ip-service` | `inhouz/subscription_authorization_ms` | node server.js |
| `subscription_metrics_ms` | 5011 | `subscription-metrics-ms-cluster-ip-service` | `inhouz/subscription_metrics_ms` | node server.js |
| `subscription_migration_parser_ms` | 5025 | `subscription-migration-parser-ms-cluster-ip-service` | `inhouz/subscription_migration_parser_ms` | node server.js |
| `subscription_migration_scheduler_ms` | 5024 | `subscription-migration-scheduler-ms-cluster-ip-service` | `inhouz/subscription_migration_scheduler_ms` | node --max-old-space-size=8192 server.js |
| `subscription_ms` | 5005 | `subscription-ms-cluster-ip-service` | `inhouz/subscription_ms` | node server.js |
| `subscription_payment_ms` | 5032 | `subscription-payment-ms-cluster-ip-service` | `inhouz/subscription_payment_ms` | node server.js |
| `subscription_renewal_ms` | 5027 | `subscription-renewal-ms-cluster-ip-service` | `inhouz/subscription_renewal_ms` | node server.js |
| `subscription_renewal_scheduler_ms` | 5026 | `subscription-renewal-scheduler-ms-cluster-ip-service` | `inhouz/subscription_renewal_scheduler_ms` | node --max-old-space-size=8192 server.js |
| `subscription_settings_ms` | 5033 | `subscription-settings-ms-cluster-ip-service` | `inhouz/subscription_settings_ms` | node server.js |
| `subscription_signup_ms` | 5023 | `subscription-signup-ms-cluster-ip-service` | `inhouz/subscription_signup_ms` | node server.js |
| `system_users_ms` | 5022 | `system-user-ms-cluster-ip-service` | `inhouz/system_user_ms` | node server.js |
| `view_builder_ms` | 5017 | `view-builder-ms-cluster-ip-service` | `inhouz/view_builder_ms` | node --max-old-space-size=8192 server.js |
| `webcomponent_ms` | 5039 | `webcomponent-ms-cluster-ip-service` | `inhouz/webcomponent_ms` | node server.js |
| `website_resource_ms` | 5056 | `website-resource-ms-cluster-ip-service` | `inhouz/website_resource_ms` | node server.js |
| `websocket_ms` | 5079 | `websocket-ms-cluster-ip-service` | `inhouz/websocket_ms` | no `start` script |

Ports `5000`-`5079` are the fleet range. Two exceptions: `inhouzio_app_ms` is `5000` and
`app_viewer_ms` is `3000` — the latter is the Razzle dev server, not the container port.

## The public surface

`apps/authentication_ms/k8s/inhouz-ingress-service.yml` is the only place the public route map is
declared: host paths mapped to sibling services and their ports.

## Web

Stack: the React client in `apps/inhouzio_app_ms/client/` (React 16, Redux, Razzle), served in
production by the Express server in `apps/inhouzio_app_ms/`.
Dev command: `npm start` in `apps/inhouzio_app_ms/client/`.
Verification command: none — the project has no test suite.
Port: 5000 (server), 3000 (app viewer dev server).

## Mobile

Stack: none. There is no mobile application in this repository. `apps/mobile/` holds only the
scope rules file.

## API and Services

Stack: Express 4 + Mongoose 7 (see "The microservice fleet" above).
Package manager: npm.
Dev command: `npm start` from `apps/<unit>/`.
Verification command: none — no test suite exists.
Ports: 5000-5079, see the table above.

## Database

Database: MongoDB, one shared cluster. 178 collections, 143 of them written by more than one
service. `User` is touched by 72 of the 75 services. Connection is `MONGO_URL`, read from the
secret file `mongourl` under `SECRETS_PATH` with an env fallback (`config/config.js:5-15`).

Redis is used by five services for caching, rate limiting and the Socket.IO adapter.

## Auth

Auth approach: session cookies. `checkLogin` reads the `SMPL` cookie or the `x-access-token`
header plus `x-csrfToken`, loads the session and the user from MongoDB, and slides the expiry 60
minutes. The permission chain is `User` -> `userRoles` -> `roles` -> `permissions`. Service-to-service
calls use an RSA-encrypted envelope instead. `authentication_ms` owns the cluster ingress.

## Playwright

Tool: the global install the devcontainer provides, plus the Playwright MCP
Library: `/usr/local/share/npm-global/lib/node_modules/@playwright/mcp/node_modules/playwright`
MCP server: `playwright-mcp` (on PATH), configured in `kilo.jsonc`
Browser: system chromium at `/usr/bin/chromium` — the container sets
`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`, so there is no downloaded browser

The QA capture script uses the project's own Playwright when it has one, and the global install
otherwise. It never installs anything.

Browser resolution, highest priority first:

1. `--chromium <path>`
2. `PLAYWRIGHT_CHROMIUM_PATH`
3. the browser Playwright downloaded
4. the system chromium: `/usr/bin/chromium`, `/usr/bin/chromium-browser`, `which chromium`

When no chromium is found, the capture script exits 2 and prints the list of places it searched
plus the commands that point it at a binary. It never installs a browser and never falls back to
another driver.

## Credential redaction

Every shell command the agent runs has its output scrubbed before the agent reads it.

- **File:** `.devcontainer/kilo-redact.sh`, installed to `/home/node/.kilo-redact.sh`.
- **How it loads:** `devcontainer.json` → `remoteEnv.BASH_ENV`. Kilo Code runs shell tools as
  `/bin/bash -c "<command>"`, and `$BASH_ENV` is the one startup file bash always reads for a
  non-interactive shell. Debian's `~/.bashrc` returns immediately for a non-interactive shell, so
  a function defined there never reaches the agent.
- **What it does:** redirects the shell's stdout and stderr through a `sed` filter that replaces
  GitHub tokens (`ghp_`, `ghs_`, `gho_`, `ghu_`, `ghr_`, `github_pat_`), the `x-access-token:`
  form, a URL with an inline password, a `KEY=`/`TOKEN=`/`SECRET=`/`PASSWORD=` assignment, and a
  bearer header with `<REDACTED_TOKEN>`.
- **What it leaves alone:** output with no credential is byte-identical, including binary output.
  The exit code, the stdout/stderr split, and the order of the output are all preserved.
- **Test:** `BASH_ENV=.devcontainer/kilo-redact.sh bash .devcontainer/test-kilo-redact.sh`
  — 14 checks.

The filter is a backstop. The credential itself belongs in `/home/node/.git-credentials` (mode
`600`), served by git's credential helper, never in a URL.

## Notes

- Update this file after the user approves a stack or after targeted discovery confirms values.
- Pass the relevant stack and command to builders instead of making them discover it.
- The fleet has no test suite. Any row that changes service behaviour has to state its own
  verification step; there is no `npm test` to fall back on.
