# flex_api_ms

## 1. Summary

`flex_api_ms` is the control plane for Inhouz Flex APIs: the user-defined HTTP APIs an Inhouz
customer builds from functions. It creates, edits, versions, deploys, undeploys and documents an
API; it materialises deployed endpoints into a runtime collection, keeps a per-environment version
tracker, deletes the API cache on every deploy, and publishes a Redis cache-invalidation message so
the API gateway stops serving stale endpoints. It lives in the separate repository
`/workspaces/kilo_inhouz_ai/apps/flex_api_ms/`.

## 2. Stack and commands

- Node.js `>=12.0.0 <17.5.0` (`package.json:5`).
- `package.json:7-10` — `start` = `node server.js`; `test` = the npm-init placeholder that exits 1.
- Port `PORT` (`server.js:92`); k8s pins `5006` (`k8s/flex-api-ms-cluster-ip-service.yml`).
- Image `inhouz/flex_api_ms`, 1 replica (`k8s/flex-api-ms-deployment.yml`).
- Health probe: `node healthcheck.js` against `/healthz` (`healthcheck.js:3-8`).
- Build/deploy scripts: `build_ga.sh`, `build_ga_prod.sh`, `deploy.sh`, `Dockerfile`,
  `docker-compose.yml`.

## 3. Entry points

| Entry point | Location | How it starts |
|---|---|---|
| HTTP server | `server.js:48`, `:92` | `npm start` |
| Cluster master + workers | `server.js:29-46` | production forks one worker per CPU (`:30`) |
| Route registration | `server.js:62` → `controller/flexApiController/flexApiRoutes.js:25-42` | at boot |
| Mongo connect + 5 s reconnect | `server.js:64-66`, `:71-78`, `:97-109` | at boot and on disconnect |
| Redis publisher (module side effect) | `utils/cacheManager/cacheInvalidationPublisher.js:11-26` | on first require of the module, i.e. when `deployFlexApi.js:14` loads it |
| Healthcheck binary | `healthcheck.js:1-20` | container probe |

No cron, no queue consumer, no websocket handler.

## 4. Module inventory

| Module | Location | Owns | Public API | Kind |
|---|---|---|---|---|
| server bootstrap | `server.js:1` | 15 model registrations (`:13-27`), cluster, middleware stack | none | effectful |
| config factory | `config/config.js:17` | secrets via `readSecret` (`:5-14`), model names, permission names, default domains | `() => config` | effectful (fs, env, cached module state) |
| route module | `controller/flexApiController/flexApiRoutes.js:25` | maps 16 POST routes to middleware chains | `(app) => void` | effectful |
| `createFlexApi` | `services/flexApi/createFlexApi.js:8` | create API doc (`:28`) then tracker doc (`:53`); rolls back the API on tracker failure (`:71-79`) | `(req,res)` | effectful |
| `editFlexApi` | `services/flexApi/editFlexApi.js:8` | update an API version | `(req,res)` | effectful |
| `deleteFlexApi` | `services/flexApi/deleteFlexApi.js:6` | delete API, cache, service registration, endpoints, tracker, deployment log, delete log | `(req,res)` | effectful |
| `deployFlexApi` | `services/flexApi/deployFlexApi.js:17` | materialise endpoints for one environment, update tracker, clean stale endpoints, log | `(req,res)` | effectful |
| `undeployApiEndpoint` | `services/flexApi/undeployApiEndpoint.js:7` | remove one deployed endpoint | `(req,res)` | effectful |
| `undeployApiEnvironment` | `services/flexApi/undeployApiEnvironment.js:7` | remove all endpoints for one environment, reset tracker field (`:63-90`, `:159-203`) | `(req,res)` | effectful |
| `rebuildDeployedEndpoints` | `services/flexApi/rebuildDeployedEndpoints.js:11` | re-materialise all endpoints | `(req,res)` | effectful |
| `setFlexApiVersion` | `services/flexApi/setFlexApiVersion.js:8` | switch the active version | `(req,res)` | effectful |
| `mergeEndpointDeployments` | `services/flexApi/mergeEndpointDeployments.js:12` | merge deployments and ask the view builder to rebuild (`:273-274`) | `(req,res)` | effectful |
| `getFlexApis` / `getFlexApi` | `services/flexApi/getFlexApis.js:8`, `getFlexApi.js:7` | list and read APIs | `(req,res)` | effectful |
| `getApiTracker` | `services/flexApi/getApiTracker.js:7` | read version tracker | `(req,res)` | effectful |
| `getApisDocumentation` / `getApiDocumentation` | `services/flexApi/getApisDocumentation.js:8`, `getApiDocumentation .js:6` (note the space in the file name) | generate documentation payloads | `(req,res)` | effectful |
| `getDynamicSeoApis` | `services/flexApi/getDynamicSeoApis.js:7` | public SEO endpoint list | `(req,res)` | effectful |
| `getDeployedEndpoints` | `services/flexApi/getDeployedEndpoints.js:7` | list deployed endpoints | `(req,res)` | effectful |
| `invalidateApiServiceEndpoint` | `utils/cacheManager/cacheInvalidationPublisher.js:28` | publish `{type:'endpoint', flexApiId}` on channel `api-service:cache-invalidate` (`:4`, `:30`) | `(flexApiId)` | effectful |
| `handleCachedEndpoints` | `utils/flexApi/deployment/handleCachedEndpoints.js` | restore or prune previously deployed endpoints (`deployFlexApi.js:9`) | `(cached, ...)` | effectful |
| `deleteNewEndpoints` | `utils/flexApi/deployment/deleteNewEndpoints.js` | roll back endpoints created in a failed deploy (`deployFlexApi.js:10`) | `(newEndpoints, cachedKeys)` | effectful |
| `parseEnvironmentVariables` | `utils/environmentVariable/parseEnvironmentVariables.js` | resolve env values for the target environment (`deployFlexApi.js:13`, `:167`) | `(params)` | pure |
| `functionExtractor` | `utils/functions/functionExtractor.js` | load a function for deployment | `(params)` | effectful |
| `createEditByObject` | `utils/user/createEditByObject.js` | build the audit sub-object stamped on writes | `(user, timestamp)` | pure |
| `checkLogin` | `middlewares/login/checkLogin.js:24` | session + company resolution | `(req,res,next)` | effectful |
| `lightLoginCheck` | `middlewares/login/lightLoginCheck.js:20` | cheaper session check for read routes | `(req,res,next)` | effectful |
| `companyAccountCheck` | `middlewares/company/companyAccountCheck.js` | active-account gate | `(req,res,next)` | effectful |
| `isApiDeveloper` | `middlewares/permissions/isApiDeveloper.js` | `apiDeveloper` permission gate (`config/config.js:44`) | `(req,res,next)` | pure |
| `hasDeletePermission` | `middlewares/permissions/hasDeletePermission.js` | `deleteApiPermission` gate (`config/config.js:71`) | `(req,res,next)` | pure |
| `subdomainValidator` / `singleSubdomainValidation` | `middlewares/subdomain/subdomainValidator.js:16`, `singleSubdomainValidation.js` | subdomain/company match | `(req,res,next)` | effectful |
| `moduleAccessCheck` | `middlewares/module/moduleAccessCheck.js:29` | module entitlement check | `(req,res,next)` | effectful |
| `flexApi` model | `model/api/flexApi.js` (`mongoose.model` at `:233`) | API definition: name, version, endpoints, security policies | mongoose model | effectful |
| `flexApiVersionTracker` | `model/api/flexApiVersionTracker.js:71` | per-environment deployed versions and version history | mongoose model | effectful |
| `deployedEndpoints` | `model/api/deployedEndpoints.js:91` | runtime endpoint rows | mongoose model | effectful |
| `flexApiDeploymentLog` / `flexApiDeleteLog` | `model/api/flexApiDeploymentLog.js:45`, `model/api/flexApiDeleteLog.js` | audit logs | mongoose models | effectful |
| `apiServiceCache` | `model/api/apiServiceCache.js` | cache rows deleted on deploy | mongoose model | effectful |
| foreign models | `server.js:13-27` | user, roles, permissions, session, company, functions, subscription service | mongoose models | effectful |

## 5. Side effects

| Effect | Location |
|---|---|
| Secret files (`sendgridapikey`, `mongourl`, `sessionsecret`, `clientsecretkey`, `redishost`, `redispassword`, `clientpublickey`) | `config/config.js:5-14`, `:26-41`, `:53-64` |
| Env vars | `config/config.js:20-71`, `server.js:30`, `:92` |
| Mongo connect, pool 1 | `server.js:97-109` |
| Redis client connect (`redis` v4) | `utils/cacheManager/cacheInvalidationPublisher.js:11-26` |
| Redis publish | `utils/cacheManager/cacheInvalidationPublisher.js:30` |
| HTTP POST to the view builder | `services/flexApi/mergeEndpointDeployments.js:273-274` (`${config.viewBuilderUrl}/api/viewbuilder/generalsystemrebuild`) |
| Cache deletion on deploy | `deployFlexApi.js:121-127` |
| Endpoint writes and deletes | `deployFlexApi.js:186` (rollback), `:379`, `undeployApiEnvironment.js:159` |
| Tracker update per environment | `deployFlexApi.js:355-370`, `undeployApiEnvironment.js:63-90` |
| Deployment log insert (not awaited) | `deployFlexApi.js:391-408` |
| API and tracker insert | `createFlexApi.js:28`, `:53` |
| Delete across 7 collections | `deleteFlexApi.js:26-232` |
| Clock: `new Date().getTime()` | `createFlexApi.js:26`, `deployFlexApi.js:21` |
| Randomness: `new mongoose.Types.ObjectId().toHexString()` | `createFlexApi.js:25` |
| Compression: `shrink-string` for stored payloads | `deployFlexApi.js:6`, `rebuildDeployedEndpoints.js:6` |
| Logging: `console.log` | throughout, e.g. `server.js:36`, `cacheInvalidationPublisher.js:15` |

## 6. State and state transitions

API versions and deployment state live in two documents.

| State | Field | Where |
|---|---|---|
| Version exists, active | `flexApi.activeVersion: true` | set at create `createFlexApi.js:33`; switched by `setFlexApiVersion.js` |
| Not deployed | `flexApi.deployed: false` | `createFlexApi.js:34` |
| Deployed to development / test / production | `<env>DeployedVersion` on the tracker | `deployFlexApi.js:357-369` |
| Deploy date | `<env>DeployDate` | same update |
| Undeployed | tracker version reset to `0` and endpoints deleted | `undeployApiEnvironment.js:63-90`, `:159` |
| Deleted | documents removed from 7 collections | `deleteFlexApi.js:26-232` |

Guards:

- Production deploy requires `apiProductionDeploymentPermission` (`deployFlexApi.js:36-42`, 403).
- Delete requires `hasDeletePermission` on the route (`flexApiRoutes.js:30`).
- Deploy requires `environment` to be one of `development|test|production`
  (`config/config.js:51`).
- A failed endpoint deploy rolls back: cached endpoints are re-materialised and new ones deleted
  (`deployFlexApi.js:343-352`).
- A failed tracker update also rolls back (`deployFlexApi.js:373-383`).

```mermaid
stateDiagram-v2
    [*] --> Defined: create
    Defined --> Defined: edit / setFlexApiVersion
    Defined --> DeployedDev: deploy(development)
    Defined --> DeployedTest: deploy(test)
    Defined --> DeployedProd: deploy(production) [permission]
    DeployedDev --> Defined: undeploy(development)
    DeployedTest --> Defined: undeploy(test)
    DeployedProd --> Defined: undeploy(production)
    Defined --> Deleted: delete
    DeployedDev --> Deleted: delete
    DeployedTest --> Deleted: delete
    DeployedProd --> Deleted: delete
```

## 7. Data

| Collection | Env var | Key fields | Validation |
|---|---|---|---|
| `flexApi` | `FLEX_API_MODEL` (`config/config.js:32`) | `apiName`, `version`, `subUrlPath`, `companyId`, `activeVersion`, `archived`, `flexApiId`, `tags[]`, `environmentVariables`, `securityPolicies[]`, `endpoints[]` | required `apiName`, `version`, `subUrlPath`, `companyId`; `securityPolicies[].policyType` enum of 7 (`model/api/flexApi.js:43-53`); endpoint `apiMethod` enum `GET/POST/PUT/PATCH/DELETE` (`:90-94`) |
| `flexApiVersionTracker` | `FLEX_API_VERSION_TRACKER` (`config/config.js:33`) | `flexApiId`, `companyId`, `activeVersion`, `productionDeployedVersion`, `testDeployedVersion`, `developmentDeployedVersion`, three deploy dates, `versions[]` | required ids; `versions[].createdBy` requires `userId`, `firstName`, `lastName`, `email` with an `isEmail` validator (`model/api/flexApiVersionTracker.js:38-56`) |
| `deployedEndpoints` | `DEPLOYED_API_ENDPOINTS_MODEL` (`config/config.js:49`) | `companyId`, `flexApiId`, `subUrlPath`, `apiMethod`, `slug`, `environment`, `endpointId` (`deployFlexApi.js:331-340`) | required by schema (`model/api/deployedEndpoints.js:91`) |
| `apiServiceCache` | `API_SERVICE_CACHE_MODEL` (`config/config.js:67`) | cache rows keyed by `flexApiId` + `companyId` | deleted, never read here (`deployFlexApi.js:121-127`) |
| `flexApiDeploymentLog` | `FLEX_API_DEPLOYMENT_LOG_MODEL` (`config/config.js:50`) | `actionType`, `version`, `createdById`, `createdDate`, `environment`, `companyId`, `flexApiId`, `endpointSlugs[]` | written at `deployFlexApi.js:391-401` |
| `flexApiDeleteLog` | `FLEX_API_DELETE_LOG_MODEL` (`config/config.js:66`) | delete audit | written at `deleteFlexApi.js:232` |
| `subscriptionServices` | `SUBSCRIPTION_SERVICE_MODEL` (`config/config.js:65`) | service registration, touched on delete (`deleteFlexApi.js:58`) | shared with the subscription service |

Shared data coupling (collections also written by other services):

- `deployedEndpoints` is the runtime contract with the API gateway, which reads it and is told to
  invalidate via Redis (`utils/cacheManager/cacheInvalidationPublisher.js:4`).
- `functions` / `deployedFunctions` are owned by the function services; this service reads them to
  deploy endpoints (`deployFlexApi.js:186`).
- `company`, `User`, `userRoles`, `permissions`, `roles`, `session` are identity collections owned
  elsewhere.
- `subscriptionServices` couples this service to billing.

## 8. Public interfaces

All routes are `POST /api/flexapi/*` (`controller/flexApiController/flexApiRoutes.js:26-41`).

| Route | Auth chain | Handler |
|---|---|---|
| `/create` | `isLoggedIn`, `companyAccountCheck`, `subdomainCheck`, `isApiDeveloper` | `createFlexApi.js:8` |
| `/edit` | same | `editFlexApi.js:8` |
| `/getflexapis` | `lightLoginCheck`, `subdomainValidator` | `getFlexApis.js:8` |
| `/getflexapi` | `lightLoginCheck`, `subdomainValidator` | `getFlexApi.js:7` |
| `/delete` | `isLoggedIn`, `subdomainCheck`, `isApiDeveloper`, `hasDeletePermission` | `deleteFlexApi.js:6` |
| `/deploy` | `isLoggedIn`, `companyAccountCheck`, `subdomainCheck`, `isApiDeveloper` | `deployFlexApi.js:17` |
| `/undeploy/endpoint` | `isLoggedIn`, `subdomainCheck`, `isApiDeveloper` | `undeployApiEndpoint.js:7` |
| `/undeploy/environment` | same | `undeployApiEnvironment.js:7` |
| `/rebuildendpoints` | `isLoggedIn`, `companyAccountCheck` | `rebuildDeployedEndpoints.js:11` |
| `/setflexapiversion` | `isLoggedIn`, `companyAccountCheck`, `subdomainCheck`, `isApiDeveloper` | `setFlexApiVersion.js:8` |
| `/getapitracker` | `isLoggedIn`, `subdomainCheck` | `getApiTracker.js:7` |
| `/mergedeployments` | `isLoggedIn`, `companyAccountCheck`, `subdomainCheck` | `mergeEndpointDeployments.js:12` |
| `/documentationlist` | `lightLoginCheck`, `subdomainValidator` | `getApisDocumentation.js:8` |
| `/documentation` | `lightLoginCheck`, `subdomainValidator` | `getApiDocumentation .js:6` |
| `/getdynamicseoapis` | none | `getDynamicSeoApis.js:7` |
| `/getdeployedendpoints` | `isLoggedIn`, `subdomainCheck` | `getDeployedEndpoints.js:7` |

Request shapes:

- Create/edit: `{flexApiObject: {...}}` where the object matches the `flexApi` schema
  (`createFlexApi.js:11-13`, `:28-35`).
- Deploy: `{flexApiId, versionToDeploy: number, environment}` (`deployFlexApi.js:19-21`).
- Errors are returned as `{error:{message}}`; a deploy error may also carry `errorPayload`
  (`deployFlexApi.js:140-146`).

Outbound interface: `POST ${VIEW_BUILDER_URL}/api/viewbuilder/generalsystemrebuild`
(`mergeEndpointDeployments.js:273-274`).

Redis interface: channel `api-service:cache-invalidate`, message
`{"type":"endpoint","flexApiId":"..."}` (`cacheInvalidationPublisher.js:4`, `:30`).

## 9. Configuration

Secret files: `sendgridapikey`, `sessionsecret`, `mongourl`, `clientsecretkey`, `clientpublickey`,
`redishost`, `redispassword` — with `SENDGRID_API_KEY`, `SESSION_SECRET`, `MONGO_URL`,
`CLIENT_SECRET_KEY`, `CLIENT_PUBLIC_KEY`, `REDIS_HOST`, `REDIS_PASSWORD` env fallbacks
(`config/config.js:26-64`).

Env vars read by config: `INHOUZ_API_DOMAIN`, `INHOUZ_APP_DOMAIN`, `FLEX_FORM_FILE_MODEL`,
`FLEX_MODULE_MODEL`, `FLEX_COLLECTION_MODEL`, `FORM_MODEL`, `SMPL_EMAIL`,
`DATA_RULE_EXECUTION_RESULT_MODEL`, `USER_MODEL`, `COMPANY_MODEL`, `FLEX_API_MODEL`,
`FLEX_API_VERSION_TRACKER`, `ROLE_MODEL`, `PERMISSION_MODEL`, `USER_ROLES_MODEL`, `SESSION_MODEL`,
`REDIS_DB`, `REDIS_PORT`, `COOKIE_DOMAIN`, `FUNCTION_MODEL`, `SYSTEM_USER_MODEL`,
`SYSTEM_USER_ACCOUNT_LOG_MODEL`, `DEPLOYED_API_ENDPOINTS_MODEL`, `FLEX_API_DEPLOYMENT_LOG_MODEL`,
`VIEW_BUILDER_URL`, `SUBSCRIPTION_SERVICE_MODEL`, `FLEX_API_DELETE_LOG_MODEL`,
`API_SERVICE_CACHE_MODEL`, `DEPLOYED_FUNCTION_MODEL`, `API_PRODUCTION_DEPLOYMENT_PERMISSION`,
`DELETE_API_PERMISSION`, `PORT`, `NODE_ENV` (`config/config.js:20-71`, `server.js:30`, `:92`).

Permission names in code: `apiDeveloper` (`config/config.js:44`), plus the two env-supplied
permission names above. Environment list literal: `development`, `test`, `production`
(`config/config.js:51`).

## 10. Dependencies

| Package | Why |
|---|---|
| `express`, `body-parser`, `cookie-parser`, `cors`, `helmet`, `hpp`, `dotenv` | HTTP stack (`server.js:1-8`) |
| `mongoose` | models |
| `redis` v4 | cache-invalidation publisher (`utils/cacheManager/cacheInvalidationPublisher.js:1`) |
| `node-fetch` | HTTP client (`utils/requests/*`) |
| `node-rsa`, `cryptr` | key material and payload crypto |
| `sanitizer` | `recursiveSanitizer` on every request body |
| `lodash` | `isEmpty`, `uniq`, `compact` (`deployFlexApi.js:4`, `createFlexApi.js:4`) |
| `moment` | date handling in the login middleware |
| `shrink-string` | compressed deployment payloads (`deployFlexApi.js:6`) |
| `validator` | schema field validation (`model/api/flexApi.js:3`) |
| `@sendgrid/mail` | email, not used on the API path |
| `passport`, `passport-local-mongoose` | declared; no `require` found in `server.js`, `services/`, `utils/` |
| `connect-mongo`, `express-session`, `crypto-js`, `request-ip` | template carry-overs |

## 11. Testing

No tests. `package.json:8` is the placeholder that exits 1. Nothing covers the deploy rollback
paths, the tracker transitions, or the cache-invalidation publish.

## 12. Known issues and risks

- **Redis password is interpolated into a URL string.** `utils/cacheManager/cacheInvalidationPublisher.js:6`
  builds `redis://default:${config.redisPassword}@...`. The value is not logged, but it lives in a
  process-wide string and is passed to `redis.createClient`. The publisher also connects at module
  load (`:24`) in every worker, so there is one Redis connection per forked worker.
- **Redis publisher has no shutdown hook.** `server.js:82-90` closes only Mongo; the Redis client is
  left to the process exit.
- **Deployment log write is fire-and-forget.** `deployFlexApi.js:391-408` calls `.create()` without
  `await`, so a failed audit insert does not fail the deploy.
- **`deleteMany` on the cache is fire-and-forget.** `deployFlexApi.js:121-127` does not await the
  cache deletion, so a deploy can complete while stale cache rows still exist. The Redis publish is
  the compensating mechanism.
- **Endpoint deploy is not transactional.** Endpoints are written one by one, then the tracker, then
  stale endpoints are pruned; rollback is manual compensation (`handleCachedEndpoints`,
  `deleteNewEndpoints`) and only covers endpoint rows.
- **`upsert: true` without a unique index.** `deployFlexApi.js:365-369` upserts the tracker by
  `flexApiId` + `companyId`; the schema declares `index: true`, not `unique: true`
  (`model/api/flexApiVersionTracker.js:7-16`), so duplicate tracker rows are possible under
  concurrency.
- **Public route with no auth.** `/getdynamicseoapis` has no middleware
  (`flexApiRoutes.js:40`) and reads deployed endpoints for SEO; confirm that is intended.
- **File name contains a space.** `services/flexApi/getApiDocumentation .js` is required with the
  space (`flexApiRoutes.js:15`). It works, but it breaks tooling and glob-based checks.
- **Health probe mismatch.** `healthcheck.js:7` requests `/healthz`; no such route is registered.
- **`uncaughtException` only closes Mongo** (`server.js:85-90`), and the cluster master respawns the
  worker (`server.js:35-46`) with a console line only.
- **28 k8s-injected env vars are unread by code.** For example `STRIPE_API_KEY`, `PAYMENT_MS_URL`,
  `OPEN_EXCHANGE_RATES_API_KEY`, `OPEN_EXCHANGE_RATES_BASE_URL`, `CHURN_TRACKER_MODEL`,
  `EXCHANGE_RATE_CACHE_MODEL` appear in the deployment but are not referenced in
  `config/config.js`. They are template carry-overs risk: they look like live configuration of this
  service and are not.
- **The brief's "called by functions_ms" is unverified.** No inbound service name appears in code;
  only the k8s service name defines the caller contract.

## 13. Module map

```mermaid
graph TD
    S[server.js] --> C[config/config.js]
    S --> R[controller/flexApiController/flexApiRoutes.js]
    R --> MW[login / company / permissions / subdomain middlewares]
    R --> SV[services/flexApi/*]
    SV --> M[models: flexApi, tracker, deployedEndpoints, logs, cache]
    SV --> CM[utils/cacheManager/cacheInvalidationPublisher]
    SV --> FE[utils/functions/functionExtractor]
    SV --> ENV[utils/environmentVariable/parseEnvironmentVariables]
    SV --> HL[utils/flexApi/deployment/handleCachedEndpoints]
    SV --> MG[mergeEndpointDeployments]
    MG --> Q[utils/requests/postRequest]
    Q --> VB[(view-builder-ms)]
    CM --> RD[(Redis pub/sub)]
    M --> DB[(MongoDB)]
```

## 14. Open questions

- Who consumes channel `api-service:cache-invalidate`? The subscriber is not in this repo; the brief
  names `view-builder-ms` as an outbound HTTP target only.
- Does the API gateway read `deployedEndpoints` directly, or does it keep its own copy that the
  Redis message invalidates? Nothing in this repo reads the collection back.
- Why are Stripe, payment and exchange-rate env vars injected into this deployment when no code path
  reads them?
- Is `/getdynamicseoapis` (`flexApiRoutes.js:40`) intentionally unauthenticated, and does it leak
  customer API names?
- Not read (step budget): `deleteFlexApi.js`, `editFlexApi.js`, `setFlexApiVersion.js`,
  `mergeEndpointDeployments.js` beyond the outbound call, `rebuildDeployedEndpoints.js`,
  `undeployApiEndpoint.js`, `undeployApiEnvironment.js` beyond grep, `utils/flexApi/deployment/*`,
  `utils/flexApi/filter/*`, the five middlewares beyond their export lines, and all model files
  except `flexApi` and `flexApiVersionTracker`. Claims about those rest on grep output.
