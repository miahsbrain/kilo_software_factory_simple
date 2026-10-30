# RISKS

Active architectural and project risks. Short bullets only.

## Platform risks found while documenting the fleet

Each of these was verified against the source during the BOARD-001 documentation pass. The full
list, with `file:line` and the affected services, is in each service's handover file, section 12.

### 🔴 Critical — money, data loss and auth

- **Cross-tenant credential bleed in the payment distribution worker.** `STRIPE_KEY` is assigned
  without a declaration, so it is an implicit global. Two concurrent requests for different
  tenants can overwrite it, and one tenant's decrypted Stripe secret key can then be used to
  create a transfer for another tenant's distribution.
  `payment_gateway_ms/services/paymentDistribution/runDistribution.js:269`, `:273`
- **Payout approval accepts any status.** Every value other than `rejected` falls into the approve
  branch and increments `approvedCount`, so a caller can approve a payout with an arbitrary
  status. `payment_gateway_ms/services/paymentDistribution/approvalHandler.js:56-59`
- **Double charge risk in the late-payment worker.** The charge is created before the intent is
  marked paid, with no database transaction, so a retry passes the paid guard.
  `late_payment_ms/services/payment/latePaymentParser.js:535`
- **Caller-supplied SQL with no allow-list.** Four adapters execute the query string they are
  handed, and the `/webtransaction` route lacks the `serverValidator` its `/servertransaction`
  sibling carries. `database_execution_ms/utils/database/transactions/mySqlTransaction.js:113`,
  `database_execution_ms/controller/executionRoutes.js:11`
- **Unrestricted outbound request proxy.** The service forwards a caller-supplied URL with no
  allow-list, which is a server-side request forgery primitive.
  `remote_network_request_ms/server.js:192`
- **Per-tenant Stripe secrets encrypted with the session secret.** The decryption key is derived
  from `SESSION_SECRET` plus the company id, so compromising one service's session secret exposes
  every tenant's Stripe key. `payment_gateway_ms/model/payment/paymentGateway.js:21-33`
- **Unauthenticated routes that move money or write tenant data.** Named routes, with the
  evidence, are in `docs/API_CONTRACTS.md` §6. The worst are `payment_ms/controller/paymentRoutes.js:21`,
  `inhouz_pay_ms/controller/payment/paymentRoutes.js:43-79`, and
  `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:66`, `:79`.
- **Open proxies.** The image proxy forwards a caller-supplied URL
  (`image_proxy_ms/services/imageProxy.js:60`) and the app viewer's function parser runs
  user-authored expressions in-process with `safe-eval`
  (`view_builder_ms/utils/syncFunctionParser/simpleScript/expressionParser/resolveExpression.js:96`).

### 🟡 High — the architecture itself

- **One shared database, 143 collections with multiple writers.** A schema change in one service
  can break another with no signal. There is no migration tool in the fleet.
  `docs/handover/README.md` §5
- **`$lookup` stages hardcode the wrong collection names.** The models register `company` and
  `User`; the aggregations ask for `companies` and `users`. Every company-name projection is
  empty. `payment_ms/services/transactions/getPaymentIntents.js:90`
- **The tenant model, the auth middleware and the crypto helper are copied, not shared.** The
  copies have drifted, and the drift is already producing wrong results.
  `app_version_manager_ms.md` §7, `subscription_authorization_ms.md` §7
- **`recursiveSanitizer` is a no-op in every copy.** It reassigns a local primitive, so the
  sanitised value is discarded and the original is returned.
  `payment_ms/utils/sanitizer/recursiveSanitizer.js:13`
- **Authorization failures return HTTP 200.** `checkLogin` answers `res.send({error: ...})`
  without a status, so callers cannot tell a denial from a success by status code.
  `payment_ms/middlewares/login/checkLogin.js:14`
- **No overlap guard on any scheduler.** `setInterval` with no lock, so a slow run overlaps the
  next tick and a job can run twice.
  `scheduled_task_scheduler_ms/server.js:58-69`
- **No test suite anywhere in the fleet.** Every `package.json` carries the placeholder
  `"test": "echo \"Error: no test specified\" && exit 1"`. No change can be verified by anything
  but inspection.

### 🟡 High — operations

- **12 services cannot boot.** Their Dockerfile runs `npm run start` and their `package.json` has
  no `start` script: `contact_ms`, `customer_portal_ms`, `general_task_scheduler_ms`,
  `inhouz_file_upload_ms`, `inhouz_pay_metrics_ms`, `inhouz_pay_ms`, `inhouz_security_ms`,
  `inhouz_sign_metrics_ms`, `log_manager_ms`, `module_transfer_ms`, `pdf_generator_ms`,
  `websocket_ms`. `inhouz_pay_ms/package.json:6-8`, `inhouz_pay_ms/Dockerfile:11`
- **The health check can never pass.** 71 `healthcheck.js` files request `/healthz` and no service
  registers that route. `payment_ms/healthcheck.js:7`
- **Logging is `console.log` with raw error objects.** No structured logger, no correlation id. A
  Mongo error prints the failing filter and the document shape.
- **Configuration is mostly dead.** The k8s deployments set 40-80 environment variables per
  service and most are never read. `inhouz_commerce_ms/config/config.js` reads six variables its
  deployment does not define.
- **The public surface is declared in one file.** `authentication_ms/k8s/inhouz-ingress-service.yml`
  maps every host path to a service and a port. Nothing else records what is public.

### 🟢 Medium — hygiene

- **An encrypted Google service-account blob is committed to every repository** as
  `service-account.json.enc`. Nothing in the runtime path reads it, so it is a stale credential
  whose key is unknown.
- **`SESSION_SECRET` is overloaded.** It is the cookie secret, the payload-encryption key, the
  email-token key and the key under which per-tenant Stripe secrets are stored.
- **Package names are template leftovers.** `micro_service_template` appears in many
  `package.json` files, so the package name does not identify the service.
- **The cluster forks one worker per CPU** and each worker opens its own Mongo pool, against
  `maxPoolSize: 1`. `payment_ms/server.js`
- **CORS is pinned to `/inhouz.localhost/` in production**, and `function_parser_ms` allows any
  origin. `function_parser_ms/lib/index.js:52`

## Project risks

- **Documentation drift risk:** doc updates depend on the agent following AGENTS.md §B1 in the
  same change set as the code. Mitigation: every task ends with the Definition of Done checklist.
- **Bootstrapping the repo:** the first commit lands on `main` and must exist before any worktree
  can branch from it. After that, every change happens on a worktree branch (ADR-015).
- **Uncommitted board on `main`:** after each merge the orchestrator edits `docs/BOARD.md` to mark
  the row `Merged`. That edit is committed alongside the merge (§B3).
- **The control repo does not track the 75 microservice repositories.** A change to a service is
  invisible to the control repo's history and must be made in that service's own repository. This
  is the intended design (ADR-019), but it means the board's `Repos` cell is the only place the
  relationship between a row and its repository is recorded.
- **A GitHub personal access token sits in the machine's global git config.** The 75 repositories'
  own remotes are clean, but `/home/node/.gitconfig` defines a
  `url.https://<token>@github.com/.insteadOf https://github.com/` rewrite, so `git remote -v`
  prints the token. It is not committed to any repository, but it lands in every log and agent
  transcript that echoes a remote. Rotating it and dropping the rewrite is the user's call — the
  user chose to report it rather than have it remediated (ADR-048).
