# general_task_parser_ms

## 1. Summary

A small utility service that executes a fixed set of "general task" operations for the task
framework: JWT sign/verify, JWK-to-PEM conversion, reCAPTCHA v3 validation, web-socket connection
key minting/refresh, and one domain task that emails a payment-method expiration notice. It holds
the shared Mongoose models for user, company, session, payment and subscription, but most of those
models are loaded only so routes can query them through `mongoose.model(name)`. It lives in its own
git repository at `apps/general_task_parser_ms/`; every `file:line` below is relative to that
repository.

## 2. Stack and commands

Runtime: Node.js, plain CommonJS (no build step). `package.json:5-7` declares
`"engines": { "node": ">=12.0.0 <17.5.0" }`. Framework: Express 4, Mongoose 7, `node-fetch` 2
(`package.json:15-40`).

Scripts quoted from `package.json:9-12`:

| Script | Command |
|---|---|
| `start` | `node server.js` |
| `test` | `echo "Error: no test specified" && exit 1` |

There is no build script and no linter script. Port: `PORT`, read at `server.js:92` and
`healthcheck.js:6`. k8s service `general-task-parser-ms-cluster-ip-service` maps port `5042`
(`k8s/general-task-parser-ms-cluster-ip-service.yml:4`, `:9-10`); image
`inhouz/general_task_parser_ms`, `replicas: 1`
(`k8s/general-task-parser-ms-deployment.yml:6`, `:17`).

**Package identity mismatch.** `package.json:2-3` still says `"name": "subscription_renewal_ms"`.
The repository folder and the k8s objects say `general_task_parser_ms`.

## 3. Entry points

| Entry point | Location | How it starts |
|---|---|---|
| Cluster bootstrap | `server.js:30-47` | Forks CPU count in production, `1` otherwise (`:31`); re-forks on exit (`:36-47`) |
| Express app + listener | `server.js:49`; `app.listen` at `:92` | `node server.js` |
| Route registration | `server.js:62` → `controller/generalRoutes/generalRoutes.js:9-17` | `require(...)(app)` installs 7 POST routes |
| Model registration (side-effect requires) | `server.js:13-28` | 16 `require("./model/...")` calls register schemas before any route runs |
| Mongo connect / reconnect | `server.js:64-90`, `:97-109` | `connectMongo()`; 5 s retry on `disconnected` (`:74-76`) |
| Health probe script | `healthcheck.js:1-21` | Standalone `node healthcheck.js`; probes `localhost:$PORT/healthz` |
| `setTimeout` retry timer | `server.js:74` | Mongo reconnect only |

Routes are registered as `app.post` handlers, not an Express `Router`. There is no `app.use` for a
router (matching the brief's "app.use mounts (0)").

## 4. Module inventory

49 JavaScript files in total.

| Name | file:line | Responsibility | Public API | Kind |
|---|---|---|---|---|
| `server.js` | `server.js:1-109` | Cluster, middleware, route wiring, Mongo lifecycle | process entry | effectful |
| `config()` | `config/config.js:18-67` | Memoised config object; secret files with env fallback; RSA key objects | `() => config` | effectful (filesystem, env) |
| `readSecret` | `config/config.js:5-15` | Reads `SECRETS_PATH/<name>` then env fallback | `(name, envFallback) => string` | effectful |
| `generalRoutes(app)` | `controller/generalRoutes/generalRoutes.js:9-17` | Registers the 7 POST endpoints | `(app) => void` | effectful (mutates app) |
| `jwtSign` | `services/jwt/jwtSign.js:8-78` | Decrypts envelope, `jwt.sign`, returns token | Express handler | effectful (crypto, clock) |
| `jwtVerify` | `services/jwt/jwtVerify.js:8-78` | Decrypts envelope, `jwt.verify`, returns decoded payload | Express handler | effectful |
| `jwkToPem` | `services/jwt/jwkToPem.js:9-66` | `jwk-to-pem` conversion, optional private | Express handler | pure for conversion; effectful for envelope |
| `validateRecaptcha` | `services/recaptcha/validateRecaptcha.js:6-94` | Posts token to Google siteverify, checks score and action | Express handler | effectful (HTTP) |
| `getWebsocketConnectionKey` | `services/websocket/getWebsocketConnectionKey.js:8-81` | Mints a 5-minute company-scoped connection key | Express handler | effectful (crypto, clock) |
| `refreshWebsocketClientKey` | `services/websocket/refreshWebsocketClientKey.js:8-125` | Validates connection key + client key, re-issues client key for 24 h | Express handler | effectful |
| `paymentMethodExpirationNotify` | `services/payment/paymentMethodExpirationNotify.js:10-295` | Looks up payment method, service, admins, users; emails each; increments counter | Express handler | effectful (DB, email, clock) |
| `encryptDecrypt` | `utils/cryptography/encryptDecrypt.js:3-26` | RSA encrypt/decrypt with configured client keys | `(data, encrypt, publicEncrypt, publicDecrypt) => string` | effectful (key material) |
| `recursiveSanitizer` | `utils/sanitizer/recursiveSanitizer.js` | Deep-sanitises request body | `(value, sanitizer) => value` | pure |
| `sendEmail` | `utils/email/sendEmail/sendEmail.js:4-29` | SendGrid send, text or html | `(to, from, subject, text, html) => {success}` | effectful (network) |
| `paymentMethodExpirationNoticeEmailTemplate` | `utils/email/paymentMethod/paymentMethodExpirationNoticeEmailTemplate.js` | Builds the notice HTML | `({user, paymentMethod, subscriptionService, daysToExpiration}) => {success, emailTemplate}` | pure |
| `successfulRenewalEmailTemplate` | `utils/email/subscriptions/successfulRenewalEmailTemplate.js` | Renewal email HTML | template fn | pure |
| `ownerSuccessfulRenewalEmail` | `utils/email/subscriptions/ownerSuccessfulRenewalEmail.js` | Sends owner renewal email | `(...)` | effectful |
| `subscriptionAdminEmail` | `utils/email/subscriptionService/subscriptionAdminEmail.js:1-90` | Resolves admins, sends mail | `(...)` | effectful |
| `checkLogin` middleware | `middlewares/login/checkLogin.js:1-140` | Session/company lookup; not mounted | `(req, res, next)` | effectful |
| `moduleAccessCheck` middleware | `middlewares/module/moduleAccessCheck.js:1-40` | Flex module access check; not mounted | `(req, res, next)` | effectful |
| `singleSubdomainValidation` | `middlewares/subdomain/singleSubdomainValidation.js` | Subdomain check; not mounted | `(req, res, next)` | effectful |
| `setSubscribedPackages` / `restoreSubscriptions` | `utils/subscribedPackage/setSubscribedPackages.js:8`, `utils/subscription/restoreSubscriptions.js:6` | Package/subscription helpers; not imported by any live route | `(...)` | effectful |
| `getUser` | `utils/user/getUser.js:18-130` | User + roles + permissions assembly | `(...)` | effectful |
| `createEditByObject` | `utils/user/createEditByObject.js` | Audit byline helper | `(...)` | pure |
| Pricing helpers | `utils/pricingCalculations/planPriceCalculation.js:100`, `addonPriceCalculation.js` | Plan/addon pricing | `(...)` | pure |
| `timeMaps`, `totalPingsCalculation` | `utils/apiFunctions/timeMaps.js`, `utils/apiFunctions/totalPingsCalculation.js:18` | Ping/time helpers | `(...)` | pure |
| `marketplaceTransaction` | `utils/payment/stripe/marketplaceTransaction.js:2-30` | Stripe payment-intent creation — **dead**: `config.stripeApiKey` does not exist in `config/config.js`, and nothing requires this module | `async (...)` | effectful (would throw at load) |
| `zeroDecimalCurrencies`, `transactionSplitMap` | `utils/payment/stripe/zeroDecimalCurrencies.js`, `utils/payment/transaction/transactionSplitMap.js` | Currency/split tables | literals | pure |
| Models (17) | `model/**/*.js` | Mongoose schemas; see §7 | `mongoose.model(...)` default export | effectful |

## 5. Side effects

| Effect | Where |
|---|---|
| MongoDB connect / reconnect | `server.js:64-78`, `:97-109` |
| MongoDB reads/writes | `services/payment/paymentMethodExpirationNotify.js:66-275` (payment method, subscription service, permission, roles, user roles, users, counter update) |
| Filesystem: secret files | `config/config.js:6-14` |
| HTTP out: Google reCAPTCHA siteverify | `services/recaptcha/validateRecaptcha.js:62-66` |
| Email out: SendGrid | `utils/email/sendEmail/sendEmail.js:6-23` |
| Stripe SDK | `utils/payment/stripe/marketplaceTransaction.js:2` (dead path; key missing from config) |
| Clock | `new Date().getTime()` at `services/jwt/jwtSign.js:31`, `jwtVerify.js:31`, `jwkToPem.js:32`, `validateRecaptcha.js:24`, `getWebsocketConnectionKey.js:34`, `refreshWebsocketClientKey.js:34`, `:69`, `:85`; `moment()` at `getWebsocketConnectionKey.js:60`, `refreshWebsocketClientKey.js:108` |
| Crypto (RSA) | `utils/cryptography/encryptDecrypt.js:5-20` |
| Symmetric crypto | `new Cryptr(config.sessionSecret)` at `getWebsocketConnectionKey.js:26`, `refreshWebsocketClientKey.js:26` |
| Logging | `console.log` / `console.error` in every handler, e.g. `server.js:69`, `jwtSign.js:71`, `validateRecaptcha.js:85` |
| Timers | `server.js:74` |

## 6. State and state transitions

No entity state machine is owned by this service. Every route is a stateless request pipeline over
an encrypted envelope, except `paymentMethodExpirationNotify`, which increments one counter.

Envelope lifecycle (all seven routes):

| Transition | Trigger | Guard |
|---|---|---|
| `Received → Rejected400` | `encryptedPayload` missing or not a string | `typeof === 'string'` (`jwtSign.js:15-24`, same in all six others) |
| `Decrypting → Rejected400` | envelope expired | `now <= expirationTimestamp` (`jwtSign.js:31-35`) |
| `Decrypting → Rejected400` | decrypt throws inside `encryptDecrypt` | that helper swallows the error and returns the input unchanged (`encryptDecrypt.js:22-25`), so `JSON.parse` throws and the outer catch returns 500 |
| `Valid → Success` | handler-specific work | see §8 |
| `Any → 500` | thrown error | per-handler `catch` |

Payment-method notice counter:

| Field | Transition | Trigger |
|---|---|---|
| `paymentMethods.expirationNoticeCount` | `n → n+1` | successful notice run (`paymentMethodExpirationNotify.js:270-280`); not incremented when any lookup returns 404/500 |

## 7. Data

17 schemas are declared; `server.js:13-28` requires 16 of them (the 17th,
`model/subscription/subscriptionService.js`, is required transitively by the notify service through
`mongoose.model(config.subscriptionServiceModel)` at `paymentMethodExpirationNotify.js:99`).
Collection names come from env vars, never from the code.

| Model file | Schema | Collection env var | Key fields / validation |
|---|---|---|---|
| `model/user/user.js:6-138` | `user` | `USER_MODEL` | `firstName`/`lastName` required; `userType` enum `enterprise\|nonEnterprise\|thirdParty`; `email` required, lowercased, `validator.isEmail` (`:22-33`); `companyId` required index; `key` unique required (`:49-53`); `ownerUser` default false; `sex` enum (`:58-60`) |
| `model/user/useRoles.js:6-51` | user roles | `USER_ROLES_MODEL` | role/permission lists |
| `model/rolesAndPermissions/roles.js:6-93` | roles | `ROLE_MODEL` | `permissionIdList` (used at `paymentMethodExpirationNotify.js:163`) |
| `model/rolesAndPermissions/permissions.js:6-91` | permissions | `PERMISSION_MODEL` | `permissionName`, `signupPermission` (used at `:134-136`) |
| `model/company/company.js:5-108` | company | `COMPANY_MODEL` | `stripeCustomerId` at `:52` |
| `model/session/session.js:5-28` | session | `SESSION_MODEL` | session token |
| `model/payment/paymentCharge.js:5-84` | payment charges | `PAYMENT_CHARGE_MODEL` | gateway enum `stripe` (`:33`) |
| `model/payment/paymentIntent.js:5-78` | payment intents | `PAYMENT_INTENT_MODEL` | intent record |
| `model/payment/paymentMethod.js:5-88` | payment methods | `PAYMENT_METHOD_MODEL` | `gatewayType` enum `braintree\|stripe` (`:32`), `stripePaymentMethodId` (`:34`), `linkedSubscriptionServices`, `assetOwnerCompanyId`, `isInhouzPaymentMethod`, `expirationNoticeCount` |
| `model/payment/payoutAccount.js:5-68` | payout accounts | `PAYOUT_ACCOUNT_MODEL` | gateway default `stripe` (`:20`) |
| `model/payment/exchangeRateCache.js:5-20` | exchange rates | `EXCHANGE_RATE_CACHE_MODEL` | rate cache |
| `model/subscription/subscription.js:6-214` | subscriptions | `SUBSCRIPTION_MODEL` | largest schema |
| `model/subscription/subscriptionPackage.js:6-122` | subscribed packages | `SUBSCRIBED_PACKAGE_MODEL` | package limits |
| `model/subscription/subscriber.js:6-73` | subscribers | `SUBSCRIBER_MODEL` | subscriber record |
| `model/subscription/subscriberActionLogs.js:6-96` | subscriber action logs | `SUBSCRIBER_ACTION_LOG_MODEL` | audit |
| `model/subscription/subscriberMigrationQueue.js:6-88` | migration queue | `SUBSCRIBER_MIGRATION_QUEUE_MODEL` | queue row |
| `model/subscription/subscriptionService.js:5-...` | subscription services | `SUBSCRIPTION_SERVICE_MODEL` | `subscriptionServiceId`, `serviceIsActive`, `environment` (query at `paymentMethodExpirationNotify.js:100-107`) |

**Shared collections.** These schemas describe collections other Inhouz services also read:
`users`, `company`, `session`, `roles`, `permissions`, `userRoles`, `paymentMethods`,
`paymentIntents`, `paymentCharges`, `payoutAccounts`, `subscriptions`,
`subscriptionServices`, `subscribers`. The env-var indirection means the actual collection name is
deployment state, not repository state. Consumers include `function_parser_ms` and
`scheduled_task_function_parser_ms` (both call this service per the brief).

## 8. Public interfaces

All routes accept `{ encryptedPayload, serverEncrypted? }` and decrypt to
`{ payload, expirationTimestamp }`. Success is `200`; the standard error is
`400 { error: { message: "Invalid request. Required fields are missing." } }`.

| Route | Payload (decrypted) | Success response |
|---|---|---|
| `POST /api/generaltaskparser/jwtsign` (`generalRoutes.js:11`) | `{ payloadObject, key, options }` | `{ token }` (`jwtSign.js:67-69`) |
| `POST /api/generaltaskparser/jwtverify` (`:12`) | `{ token, key, options }` | `{ decodedPayload }` (`jwtVerify.js:67-69`) |
| `POST /api/generaltaskparser/jwktopem` (`:13`) | `{ jwk, private }` | `{ PEM }` (`jwkToPem.js:57`) |
| `POST /api/generaltaskparser/getwebsocketconnectionkey` (`:14`) | `{ companyId }`; optional `serverEncrypted: true` | `{ wsConnectionKey, expirationTimestamp, companyId }` (`getWebsocketConnectionKey.js:68-72`), 5 min TTL |
| `POST /api/generaltaskparser/refreshwebsocketclientkey` (`:15`) | `{ wsConnectionKey, clientKey }` | `{ clientKey, expirationTimestamp, companyId }` (`refreshWebsocketClientKey.js:109-116`), 24 h TTL |
| `POST /api/generaltaskparser/validaterecaptchav3token` (`:16`) | `{ recaptchaToken, recaptchaSecretKey, recaptchaAction, minimumScore=0.5 }` | `{ success: true, message, score }`; failure `400 { success: false, message, score }` (`validateRecaptcha.js:71-83`) |
| `POST /api/generaltaskparser/paymentmethodexpirationnotice` (`:10`) | `{ companyId, paymentMethodId, daysToExpiration }`, `companyId` must be a valid ObjectId | `{ success: true }`; 404 for missing method/service/permission/roles/users (`paymentMethodExpirationNotify.js:77-250`) |

Outgoing HTTP: only `https://www.google.com/recaptcha/api/siteverify`
(`validateRecaptcha.js:62`). No calls to other Inhouz services, despite `FUNCTION_MS_URL`,
`FUNCTION_PARSER_MS_URL`, `PAYMENT_MS_URL`, `SCHEDULED_TASK_MS_URL` being set in k8s.
CLI: only `healthcheck.js`.

## 9. Configuration

Env var names only. Secret-file names in parentheses are the file names under `SECRETS_PATH`.

Secrets: `MONGO_URL` (`mongourl`), `SESSION_SECRET` (`sessionsecret`), `CLIENT_SECRET_KEY`
(`clientsecretkey`), `CLIENT_PUBLIC_KEY` (`clientpublickey`), `SENDGRID_API_KEY`
(`sendgridapikey`), `OPEN_EXCHANGE_RATES_API_KEY` (`openexchangeratesapikey`); plus `SECRETS_PATH`
(`config/config.js:5-64`).

Model names: `USER_MODEL`, `COMPANY_MODEL`, `ROLE_MODEL`, `PERMISSION_MODEL`, `USER_ROLES_MODEL`,
`SESSION_MODEL`, `SESSION_VALIDATOR_MODEL`, `AUTH_LOG_MODEL`, `PAYMENT_CHARGE_MODEL`,
`PAYOUT_ACCOUNT_MODEL`, `PAYMENT_METHOD_MODEL`, `PAYMENT_INTENT_MODEL`,
`EXCHANGE_RATE_CACHE_MODEL`, `SUBSCRIBED_PACKAGE_MODEL`, `SUBSCRIPTION_MODEL`,
`SUBSCRIBER_ACTION_LOG_MODEL`, `SUBSCRIBER_MODEL`, `SUBSCRIPTION_SERVICE_MODEL`,
`DATA_RULE_EXECUTION_RESULT_MODEL`, `FLEX_FORM_FILE_MODEL`, `FLEX_MODULE_MODEL`,
`FLEX_COLLECTION_MODEL`, `FORM_MODEL` (`config/config.js:21-54`).

Other: `PORT`, `NODE_ENV`, `COOKIE_DOMAIN`, `OPEN_EXCHANGE_RATES_BASE_URL`,
`SUBSCRIPTION_SERVICE_CHARGE_TYPE`, `INHOUZ_FROM_EMAIL`. Constant: `adminPermission = "admin"`
(`config/config.js:37`).

Set in k8s but never read here: `FUNCTION_MODEL`, `FUNCTION_MS_URL`, `FUNCTION_PARSER_MS_URL`,
`PAYMENT_MS_URL`, `SCHEDULED_TASK_MS_URL`, `COOKIE_NAME`, `SENDGRID_API_KEY` (read only through
the secret fallback), and ~25 other model env vars (see the deployment env block). No values are
reproduced.

## 10. Dependencies

| Dependency | Why |
|---|---|
| `express`, `body-parser`, `cors`, `helmet`, `hpp`, `cookie-parser` | Server and middleware (`server.js:2-8`, `:50-61`) |
| `mongoose` | 17 models and all domain queries |
| `jsonwebtoken` | `jwtSign`, `jwtVerify` |
| `jwk-to-pem` | `jwkToPem` |
| `node-rsa` | Envelope RSA in `encryptDecrypt` and key objects in config |
| `cryptr` | Symmetric connection-key decryption (`getWebsocketConnectionKey.js:5`) |
| `node-fetch` | reCAPTCHA siteverify |
| `@sendgrid/mail` | Expiration and renewal emails |
| `stripe` | `marketplaceTransaction` (unused, unconfigured) |
| `lodash` | `isEmpty`, `uniq` |
| `moment` | Key expiry timestamps |
| `validator` | Email validation in the user schema |
| `sanitizer` | Body sanitisation |
| `shortid`, `bcryptjs`, `crypto-js`, `request-ip`, `connect-mongo`, `express-session` | Present, used by models/helpers or carried over; no live route depends on them |
| `dotenv` | `server.js:1` |

## 11. Testing

No tests. `package.json:10` is the placeholder `test` script that exits 1. No test framework, no
fixtures, no mocks. Coverage: none. The service can only be verified by starting it with a Mongo
instance and a valid RSA envelope.

## 12. Known issues and risks

- **Healthcheck probes a route that does not exist.** `healthcheck.js:7` requests `/healthz`; no
  handler for `/healthz` is registered in `server.js` or `generalRoutes.js`, so the probe always
  gets 404 and exits 1.
- **`config.stripeApiKey` is undefined.** `utils/payment/stripe/marketplaceTransaction.js:2` calls
  `require('stripe')(config.stripeApiKey)` but `config/config.js` never defines `stripeApiKey`.
  Loading the module would throw; it is currently unreferenced.
- **CORS is pinned to a dev regex.** `origin: /inhouz.localhost/` (`server.js:52`) is evaluated
  against the deployed origin, so production callers are rejected unless their origin contains
  that string.
- **Envelope failure mode is ambiguous.** `encryptDecrypt` returns the input unchanged on error
  (`encryptDecrypt.js:22-25`), so a bad ciphertext reaches `JSON.parse` and surfaces as a 500
  rather than a 400.
- **No route-level auth.** Every handler trusts the encrypted envelope; there is no session,
  middleware, or server-validator check on any of the 7 routes (`generalRoutes.js:10-16`).
- **Arbitrary key material accepted.** `jwtSign` and `jwtVerify` take the signing `key` and
  `options` from the decrypted payload (`jwtSign.js:45-65`), so a caller holding the RSA keys can
  sign or verify with any key.
- **Arbitrary URL input to reCAPTCHA.** The secret and token are interpolated into a URL without
  encoding (`validateRecaptcha.js:62`); a token containing `&` or `#` corrupts the query.
- **`serverEncrypted` downgrade path.** Both websocket routes accept a plaintext flag that chooses
  between Cryptr and RSA (`getWebsocketConnectionKey.js:27-31`); the flag comes from the
  unauthenticated body.
- **Emails sent without awaiting.** `sendEmail(...)` is called in a loop with no `await`
  (`paymentMethodExpirationNotify.js:260-267`), so failures are invisible and the response returns
  before delivery.
- **Broad internal error echo.** `validateRecaptcha` returns `e.message` to the caller
  (`validateRecaptcha.js:90`).
- **Dead middleware and helpers** (`middlewares/**`, `utils/payment/stripe`, pricing helpers) are
  shipped in the image with no route using them.
- **Wide body limit.** 20 MB JSON (`server.js:58`) on routes whose payload is a small envelope.
- **Package name is wrong** (`package.json:2`), which confuses image/registry tooling and SBOMs.
- **N+1 style lookups.** The notice handler performs six sequential queries before sending email
  (`paymentMethodExpirationNotify.js:66`, `:100`, `:133`, `:162`, `:191`, `:245`).

No live-looking credential literal was found in the source; secrets are read from
`SECRETS_PATH` or env (`config/config.js:5-14`).

## 13. Module map

```mermaid
graph TD
    S[server.js] --> C[config/config.js]
    S --> R[controller/generalRoutes/generalRoutes.js]
    S --> M[model/* 17 schemas]
    R --> J1[services/jwt/jwtSign]
    R --> J2[services/jwt/jwtVerify]
    R --> J3[services/jwt/jwkToPem]
    R --> W1[services/websocket/getWebsocketConnectionKey]
    R --> W2[services/websocket/refreshWebsocketClientKey]
    R --> RC[services/recaptcha/validateRecaptcha]
    R --> PM[services/payment/paymentMethodExpirationNotify]
    J1 --> E[utils/cryptography/encryptDecrypt]
    J2 --> E
    J3 --> E
    W1 --> E
    W2 --> E
    W1 --> CR[cryptr]
    W2 --> CR
    RC --> E
    RC --> F[node-fetch: Google siteverify]
    PM --> E
    PM --> TM[utils/email/paymentMethod/...Template]
    PM --> SE[utils/email/sendEmail/sendEmail]
    SE --> SG[@sendgrid/mail]
    PM --> M
    E --> C
```

## 14. Open questions

- **Mode: full read of all 49 files?** No. Read in full: `server.js`, `config/config.js`,
  `controller/generalRoutes/generalRoutes.js`, `healthcheck.js`, all six `services/jwt` and
  `services/websocket` handlers, `services/recaptcha/validateRecaptcha.js`,
  `services/payment/paymentMethodExpirationNotify.js` (all 295 lines), `utils/cryptography/encryptDecrypt.js`,
  `utils/email/sendEmail/sendEmail.js` (first 40 lines), `model/user/user.js` (first 60 lines).
  The remaining ~22 model/util files were catalogued by directory listing plus targeted `grep`
  (`mongoose.model`, `new Schema`, `fetch(`, `stripe`, `sendEmail`, `healthz`). Each is cited by
  file; field-level detail is given only for the models the live routes read.
- **Note:** the brief said this repo has ~150 JS files. `find` shows 49. The inventory above is
  complete at the file level.
- **Which service calls these routes** cannot be confirmed from this repository (no caller code).
  The brief names `function_parser_ms` and `scheduled_task_function_parser_ms`; the latter does not
  call them in its own code (it uses `GENERAL_TASK_PARSER_MS_URL` only as a config value).
- **The real collection names** are deployment state (`*_MODEL` env vars). The brief's mapping
  (`USER_MODEL` → `User`, `PAYMENT_METHOD_MODEL` → `paymentMethods`, …) could not be verified in
  code and is not repeated as fact.
- **Whether `paymentMethodExpirationNoticeEmailTemplate` always returns `success`** was not
  verified; the handler silently skips a user when it returns false
  (`paymentMethodExpirationNotify.js:259-267`).
- **Why the Redis/Stripe/pricing helpers remain** in the repo is unexplained. They appear to be
  copied from a larger service (`subscription_renewal_ms`, per `package.json:2`).
