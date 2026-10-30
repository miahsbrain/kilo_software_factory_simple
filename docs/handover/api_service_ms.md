# api_service_ms

## 1. Summary

`api_service_ms` is the public runtime gateway for Inhouz Flex APIs. Every method on every host is
captured by five wildcard routes, resolved from the subdomain and URL into a company, environment,
API name and endpoint, checked against IP/host/HTTP/API-key policies, and then executed by
forwarding the call to `function_parser_ms`. It caches endpoint and API-key lookups in process
memory for one hour, listens on Redis for `flex_api_ms` cache-invalidation messages, and records API
usage and metrics for billing. It lives in the separate repository
`/workspaces/kilo_inhouz_ai/apps/api_service_ms/`.

## 2. Stack and commands

- Node.js `>=12.0.0 <17.5.0` (`package.json:5-7`).
- `package.json:9-12` — `start` = `node server.js`; `test` = the npm-init placeholder that exits 1.
- Port `PORT` (`server.js:118`); k8s pins `5010` (`k8s/api-service-ms-cluster-ip-service.yml:10`).
- Image `inhouz/api_service_ms`, 1 replica (`k8s/api-service-ms-deployment.yml:6,17`).
- Health probe: `node healthcheck.js` against `/healthz` (`healthcheck.js:3-8`). No `/healthz` route
  is registered here either.
- Build scripts: `build_ga.sh`, `build_ga_prod.sh`, `deploy.sh`, `Dockerfile`, `docker-compose.yml`.

## 3. Entry points

| Entry point | Location | How it starts |
|---|---|---|
| HTTP server | `server.js:61`, `:118` | `npm start` |
| Cluster master / workers | `server.js:42-59` | production forks one worker per CPU (`:43`) |
| Wildcard routes | `server.js:81` → `controller/apiService/apiRoute.js:12-16` | at boot |
| Mongo connect, pool 2 | `server.js:83-85`, `:123-135` | at boot |
| Cache-expiry sweep | `server.js:112-114` | `setInterval` every 60 s |
| Redis invalidation subscriber | `server.js:116` → `utils/cacheManager/cacheInvalidationSubscriber.js:27-48` | at boot, one subscription per worker |
| Reconnect timer | `server.js:90-97` | 5 s after a Mongo disconnect |
| Healthcheck binary | `healthcheck.js:1-20` | container probe |

No cron file. The two timers are the cache sweep and the Mongo reconnect.

## 4. Module inventory

| Module | Location | Owns | Public API | Kind |
|---|---|---|---|---|
| server bootstrap | `server.js:1` | 25 model registrations (`:16-40`), cluster, middleware, timer, subscriber | none | effectful |
| config factory | `config/config.js:17` | `readSecret` (`:5`), model names, Redis config, outbound service URLs | `() => config` | effectful |
| wildcard routing | `controller/apiService/apiRoute.js:11-17` | `GET/POST/PUT/PATCH/DELETE *` with 8 middlewares then `parseApi` | `(app) => void` | effectful |
| `getCachedApi` | `middlewares/api/getCachedApi.js:6` | derive slug, environment, apiName, company subdomain from the host and URL (`:13-70`); short-circuit from cache (`:73`) | `(req,res,next)` | effectful (also mutates `req`) |
| `getApi` | `middlewares/api/getApi.js:6` | load company by subdomain (`:12-51`), freelancer licence and monthly quota (`:53-91`), deployed endpoint row (`:93-120`) | `(req,res,next)` | effectful |
| `httpPolicy` | `middlewares/policies/httpPolicy.js:1` | protocol policy | `(req,res,next)` | pure |
| `ipBlockPolicy` / `ipWhitelist` | `middlewares/policies/ipBlockPolicy.js:1`, `ipWhitelist.js:1` | IP policies | `(req,res,next)` | pure |
| `hostWhitelist` / `hostBlocklist` | `middlewares/policies/hostWhitelist.js:1`, `hostBlocklist.js:1` | origin/host policies | `(req,res,next)` | pure |
| `apiKeyValidation` | `middlewares/apiKey/apiKeyValidation.js:8` | decrypt the API key with the session secret (`:49`), parse `{userId,userType,companyId,environment,subscriptionId,isInternal}` (`:68-73`), match environment (`:76`), load user/system user | `(req,res,next)` | effectful |
| `parseApi` | `utils/api/parseApi.js:13` | build the function payload (`:34-51`), mint a 30 s encrypted ticket (`:53-60`), POST to `function_parser_ms` (`:69-79`), map status/headers/cookies/file payload, record usage (`:156-166`) | `(req,res)` | effectful |
| `recordApiUsage` | `utils/subscriber/recordApiUsage.js:8` | write usage log (`:30`), increment subscription counters (`:110`, `:131-138`), write API usage log (`:147`) and metrics (`:190`) | `(params)` | effectful |
| `CacheManager` | `utils/cacheManager/cacheManager.js:113` | in-process maps for API-service and API-key cache with 1 h TTL (`:8-38`), delete by flex API id (`:41-55`), `clearExpiredCache` | class | reactive (holds module state) |
| `cacheManagerInstance` | `utils/cacheManager/cacheManagerInstance.js:2` | singleton instance | object | reactive |
| `startCacheInvalidationSubscriber` | `utils/cacheManager/cacheInvalidationSubscriber.js:27` | subscribe to `api-service:cache-invalidate`, delete endpoint or API-key cache entries (`:29-43`) | `() => void` | effectful |
| `getSystemUser` | `utils/systemUser/getSystemUser.js:22` | load a system user for internal key auth | `(params)` | effectful |
| `getSubscriptionUser` | `utils/user/getSubscriptionUser.js:32` | resolve a subscription user across subscriber, company, subscription, service | `(params)` | effectful |
| `environmentDomainMap` | `utils/environmentUtils/environmentDomainMap.js:1` | `dev → development`, `test → test`, `production → production` | object | pure |
| `parseEnvironmentVariables` / env utils | `utils/environmentUtils/*` | runtime env resolution | — | pure |
| `postRequest` / `getRequest` / `deleteRequest` | `utils/requests/*.js` | `node-fetch` wrappers (not used by `parseApi`, which calls `fetch` directly) | `(url, headers, data)` | effectful |
| `parseApiGet/Post/Put/Patch/Delete` | `services/api/*.js:3` | thin wrappers that call `parseApi` and `res.send` the result; **not referenced by the route file** | `(req,res)` | effectful (dead code) |
| `checkLogin` | `middlewares/login/checkLogin.js:24` | cookie session check; not mounted on the wildcard routes | `(req,res,next)` | effectful |
| `subscriptionAccess` | `middlewares/subscription/subscriptionAccess.js:23` | subscriber entitlement; not mounted on the wildcard routes | `(req,res,next)` | effectful |
| `moduleAccessCheck` / `singleSubdomainValidation` | `middlewares/module/moduleAccessCheck.js:29`, `middlewares/subdomain/singleSubdomainValidation.js` | unused by the route table | `(req,res,next)` | effectful |
| models | `model/api/*`, `model/collection/*`, `model/functions/*`, `model/query/*`, `model/subscription/*`, `model/metrics/apiMetrics.js:5`, identity models | schema definitions | mongoose models | effectful |

## 5. Side effects

| Effect | Location |
|---|---|
| Secret files (`sendgridapikey`, `sessionsecret`, `mongourl`, `redishost`, `redispassword`, `clientsecretkey`) | `config/config.js:24-43`, `:63-66` |
| Env vars | `config/config.js:20-69`, `server.js:43`, `:118` |
| Mongo connect, pool 2 | `server.js:123-135` |
| Mongoose reconnect timer | `server.js:90-97` |
| In-process cache sweep every 60 s | `server.js:112-114`; `utils/cacheManager/cacheManager.js` |
| Redis client connect, subscribe to `api-service:cache-invalidate` | `utils/cacheManager/cacheInvalidationSubscriber.js:7-29` |
| Outbound HTTP POST to `${FUNCTION_PARSER_MS_URL}/api/functionparser/parsefunction` | `utils/api/parseApi.js:69` |
| Response header/cookie writes to the caller | `utils/api/parseApi.js:138-151` |
| File payload streamed as base64 | `utils/api/parseApi.js:168-185` |
| Usage log insert (not awaited) | `utils/subscriber/recordApiUsage.js:30` |
| Subscription counter increments | `utils/subscriber/recordApiUsage.js:110`, `:131-138` |
| API usage log and metrics insert | `utils/subscriber/recordApiUsage.js:147`, `:190` |
| Clock and randomness: `Date.now`, `moment`, encrypted ticket | `middlewares/api/getCachedApi.js:8`, `parseApi.js:53-60`, `cacheManager.js:8-23` |
| Crypto: `cryptr` with the session secret for API keys and tickets | `middlewares/apiKey/apiKeyValidation.js:6,49`; `utils/api/parseApi.js:11,53` |
| Logging: `console.log` | throughout, e.g. `server.js:49`, `parseApi.js:91` |

## 6. State and state transitions

The request goes through a fixed pipeline; there is no persisted state machine. The cache is the
only in-process state.

| Stage | Guard | Failure |
|---|---|---|
| URL parse | slug present, at least one subdomain, environment maps (`getCachedApi.js:17-63`) | 400 |
| Cache hit | key `host_slug_method_environment` (`:69-73`) | short-circuits the pipeline |
| Company lookup | company exists (`getApi.js:22-30`), status active (`:42-51`) | 404 / 403 |
| Freelancer quota | `apiUtilizationCount < freeMonthlyApis` (`:83-90`) | 403 |
| Endpoint lookup | deployed endpoint row with `flexApiId` (`:107-119`) | 404 |
| Policies | IP/host/HTTP policies | per-policy status |
| API key | header or Bearer, decrypts, `environment` matches (`apiKeyValidation.js:27-97`); public APIs skip (`:28-30`) | 401 |
| Execution | function parser responds | 500 with `error.message` (`parseApi.js:99-105`) |

Cache entry states:

| State | Field | Where |
|---|---|---|
| Fresh | `expirationTimestamp = now + 1 h` | `cacheManager.js:19`, `:34` |
| Expired | swept by the 60 s interval | `server.js:112-114` |
| Invalidated | deleted by Redis message `{type:'endpoint', flexApiId}` or `{type:'apiKey', apiKey}` | `cacheInvalidationSubscriber.js:34-39` |

```mermaid
stateDiagram-v2
    [*] --> Parsed: host + url
    Parsed --> Served: cache hit
    Parsed --> Resolving: cache miss
    Resolving --> Rejected: company/endpoint/policy/key fails
    Resolving --> Forwarded: endpoint + key ok
    Forwarded --> Served: function parser 2xx
    Forwarded --> Failed: parser error
    Served --> [*]
    Rejected --> [*]
    Failed --> [*]
```

## 7. Data

| Collection | Env var | Role here |
|---|---|---|
| `deployedApiEndpoints` | `DEPLOYED_API_ENDPOINTS_MODEL` (`config/config.js:59`) | read-only lookup of the endpoint to run (`getApi.js:93-100`); written by `flex_api_ms` |
| `flexApi` | `FLEX_API_MODEL` (`config/config.js:57`) | read by `getApi` to resolve the function definition and env vars |
| `company` | `COMPANY_MODEL` (`config/config.js:31`) | read by subdomain; `status`, `companyType` (`getApi.js:12-53`) |
| `inhouzSubscriptions` | `INHOUZ_SUBSCRIPTIONS_MODEL` (`config/config.js:67`) | freelancer `freeMonthlyApis` / `apiUtilizationCount` (`getApi.js:54-90`), incremented in `recordApiUsage.js:131-138` |
| `subscriptions` | `SUBSCRIPTION_MODEL` (`config/config.js:61`) | counter update (`recordApiUsage.js:110`) |
| `subscriptionServices` | `SUBSCRIPTION_SERVICE_MODEL` (`config/config.js:55`) | service/tier resolution (`getSubscriptionUser.js:200`) |
| `subscriptionUsageLogs` | `SUBSCRIPTION_USAGE_LOG` (`config/config.js:56`) | usage log insert (`recordApiUsage.js:30`) |
| `apiUsageLogs` | `API_USAGE_LOG_MODEL` (`config/config.js:62`) | per-request log (`recordApiUsage.js:147`) |
| `apiMetrics` | `API_METRICS_MODEL` (`config/config.js:68`) | aggregated metrics (`recordApiUsage.js:190`) |
| `apiServiceCache` | `API_SERVICE_CACHE_MODEL` (`config/config.js:69`) | model registered (`server.js:40`) but the live cache is in process memory, not this collection |
| `subscribers` | `SUBSCRIBER_MODEL` (`config/config.js:54`) | subscriber lookup, `getSubscriptionUser.js:33` |
| `systemUsers` | `SYSTEM_USER_MODEL` (`config/config.js:60`) | internal API-key auth (`getSystemUser.js:22`) |
| `User`, `permissions`, `roles`, `userRoles`, `session`, `sessionValidator` | identity env vars | auth only |
| `functions`, `functionVersionTracker`, `operationTracker` | `FUNCTION_*` env vars | registered (`server.js:27-29`); the function body runs in `function_parser_ms` |
| `flexCollections`, `schema`, `query`, `queryVersionTracker`, `database` | respective env vars | registered for the runtime query path; not read in the modules inspected |

Shared data coupling: `deployedApiEndpoints` and `flexApi` are the contract with `flex_api_ms`; the
API gateway must see a deploy before `getApi` can resolve an endpoint. `apiUsageLogs`,
`apiMetrics`, `subscriptionUsageLogs` and the subscription counters are the billing contract with the
subscription services.

## 8. Public interfaces

| Interface | Shape |
|---|---|
| `GET|POST|PUT|PATCH|DELETE *` (`apiRoute.js:12-16`) | pipeline `getCachedApi → getApi → httpPolicy → ipBlockPolicy → ipWhitelist → hostWhitelist → hostBlocklist → apiKeyValidation → parseApi` |
| Host contract | `<api-name>[-<env>].<company-subdomain>.<domain>/<slug>` — `apiName = split('-')[0]`, environment from the first subdomain when there are exactly two (`getCachedApi.js:33-52`) |
| Auth header | `X-API-KEY` or `Authorization: Bearer <key>` (`apiKeyValidation.js:27-37`) |
| Parser request | `{functionId, routeParameters, queryStringParameters, companyId, requestBody, userAgent, user, requestHeaders, functionData, functionIds, environmentVariables, environment, encryptedData}` (`parseApi.js:34-60`) |
| Parser response | `{updatedVariableObject, returnStatement, hasError, errorPayload}`; reads `runtime_response_status_code`, `runtime_response_header`, `runtime_response_cookies`, `runtime_api_return_file_payload_xyz` (`parseApi.js:81-168`) |
| Redis message | `{type:'endpoint', flexApiId}` or `{type:'apiKey', apiKey}` on `api-service:cache-invalidate` (`cacheInvalidationSubscriber.js:5,31-39`) |

No events produced, no queue topic, no CLI command.

## 9. Configuration

Secret files: `sendgridapikey`, `sessionsecret`, `mongourl`, `redishost`, `redispassword`,
`clientsecretkey` with env fallbacks `SENDGRID_API_KEY`, `SESSION_SECRET`, `MONGO_URL`, `REDIS_HOST`,
`REDIS_PASSWORD`, `CLIENT_SECRET_KEY` (`config/config.js:24-43`, `:63-66`).

Env vars: `FLEX_FORM_FILE_MODEL`, `FLEX_MODULE_MODEL`, `FLEX_COLLECTION_MODEL`, `FORM_MODEL`,
`SMPL_EMAIL`, `DATA_RULE_EXECUTION_RESULT_MODEL`, `USER_MODEL`, `COMPANY_MODEL`, `ROLE_MODEL`,
`PERMISSION_MODEL`, `USER_ROLES_MODEL`, `SESSION_MODEL`, `SESSION_VALIDATOR_MODEL`, `AUTH_LOG_MODEL`,
`REDIS_DB`, `REDIS_PORT`, `COOKIE_DOMAIN`, `DATABASE_MODEL`, `QUERY_MODEL`, `QUERY_VERSION_TRACKER`,
`SCHEMA_MODEL`, `SCHEDULED_TASK_MS_URL`, `FUNCTION_MS_URL`, `FUNCTION_MODEL`,
`FUNCTION_VERSION_TRACKER_MODEL`, `OPERATION_TRACKER_MODEL`, `SUBSCRIBER_MODEL`,
`SUBSCRIPTION_SERVICE_MODEL`, `SUBSCRIPTION_USAGE_LOG`, `FLEX_API_MODEL`, `FUNCTION_PARSER_MS_URL`,
`DEPLOYED_API_ENDPOINTS_MODEL`, `SYSTEM_USER_MODEL`, `SUBSCRIPTION_MODEL`, `API_USAGE_LOG_MODEL`,
`INHOUZ_SUBSCRIPTIONS_MODEL`, `API_METRICS_MODEL`, `API_SERVICE_CACHE_MODEL`, `PORT`, `NODE_ENV`,
`SECRETS_PATH` (`config/config.js:20-69`, `server.js:43`, `:118`).

Permission literal: `admin` (`config/config.js:38`). Environment literals: `development`, `test`,
`production` (`utils/environmentUtils/environmentDomainMap.js:1-5`).

## 10. Dependencies

| Package | Why |
|---|---|
| `express`, `body-parser`, `cookie-parser`, `cors`, `helmet`, `hpp`, `dotenv` | HTTP stack (`server.js:1-8`) |
| `express-useragent` | parsed user agent is forwarded to the function (`server.js:79`, `parseApi.js:43`) |
| `mongoose` | models |
| `node-fetch` | the call to `function_parser_ms` (`parseApi.js:2,69`) |
| `redis` v4 | cache-invalidation subscriber |
| `cryptr` | API-key decryption and the parser ticket (`apiKeyValidation.js:2`, `parseApi.js:3`) |
| `node-rsa` | RSA key material (`config/config.js:1,63`) |
| `moment` | ticket expiry and cache TTL |
| `lodash` | `isEmpty`, `isEqual` in the cache manager and parser |
| `sanitizer` | imported by the module-access middleware only; the wildcard path does **not** sanitise the body |
| `form-data`, `js-base64`, `immutability-helper`, `shortid`, `bcryptjs`, `validator` | declared; no `require` found in the gateway path inspected |
| `@sendgrid/mail`, `connect-mongo`, `express-session`, `crypto-js`, `request-ip` | template carry-overs |

## 11. Testing

No tests. `package.json:10` is the placeholder that exits 1. The gateway path is only exercised by
live traffic.

## 12. Known issues and risks

- **CORS reflects any origin.** `server.js:63-74` calls `callback(null, origin)` for every origin
  while also sending `credentials: true`. Any site can call the gateway with cookies. The other
  services in this cluster restrict the origin to `/inhouz.localhost/`; this one does not.
- **`services/api/*.js` are dead code.** `parseApiGet/Post/Put/Patch/Delete` are never required by
  `apiRoute.js`, which mounts `utils/api/parseApi` directly (`apiRoute.js:3,12-16`). Both sets also
  `res.send` the same request (`services/api/parseApiGet.js:5-6`), which would double-send if wired.
- **`recordApiUsage` is not awaited.** `parseApi.js:156-166` fires it and immediately returns the
  response, so a failed billing write never fails the request; the util logs only.
- **The parser ticket is short-lived and single-purpose.** `parseApi.js:53-60` encrypts
  `{functionId, expirationTimestamp: now + 30 s}` with the session secret. Clock skew between this
  service and `function_parser_ms` greater than 30 s breaks every API call.
- **The session secret is the API-key cipher key.** `apiKeyValidation.js:6` builds `cryptr` from
  `config.sessionSecret`; rotating the session secret invalidates every issued API key.
- **API keys are not signed or rotation-aware.** The decrypted payload is trusted as-is after an
  environment check (`apiKeyValidation.js:68-97`); there is no revocation list beyond the cache
  delete.
- **Process-local cache in a multi-worker deployment.** `cacheManagerInstance` is a module singleton
  (`cacheManagerInstance.js:2`) and production forks one worker per CPU (`server.js:43`). A Redis
  invalidation message reaches every worker's subscriber, but any worker that missed it keeps stale
  entries for up to an hour.
- **Redis password is interpolated into a URL string.** `cacheInvalidationSubscriber.js:7` builds
  `redis://default:${config.redisPassword}@...`. Not logged, but present in process memory and in
  any error that echoes the connection string.
- **The subscribe call does not reconnect after a failed connect.** `cacheInvalidationSubscriber.js:27-47`
  catches the connect error and never retries, so a Redis outage at boot disables invalidation until
  the pod restarts. There is no health signal for it either.
- **Two configured outbound URLs are unused.** `FUNCTION_MS_URL` and `SCHEDULED_TASK_MS_URL` are
  read into config (`config/config.js:49-50`) and never referenced again.
- **`apiServiceCache` model is registered but unused.** The live cache is the in-memory
  `CacheManager`; the collection is never read or written in the code inspected.
- **No body sanitising on the public path.** `sanitizer` is only in `moduleAccessCheck`, which the
  wildcard routes do not mount (`apiRoute.js:12-16`).
- **Health probe mismatch.** `healthcheck.js:7` requests `/healthz`; the wildcard routes would
  actually answer it as an API call, but `/healthz` is not special-cased anywhere.
- **`uncaughtException` only closes Mongo** (`server.js:104-109`); the cluster respawns the worker.
- **`Dockerfile` / `kus` / `service-account.json.enc` are present.** The service account file is
  encrypted and was not opened; do not decrypt it into the repo.

## 13. Module map

```mermaid
graph TD
    S[server.js] --> C[config/config.js]
    S --> R[controller/apiService/apiRoute.js]
    S --> CI[cacheManagerInstance]
    S --> SUB[cacheInvalidationSubscriber]
    R --> GC[getCachedApi]
    R --> GA[getApi]
    R --> POL[policies: http, ip, host]
    R --> KV[apiKeyValidation]
    R --> PA[utils/api/parseApi]
    GC --> CI
    GA --> M[(company, deployedApiEndpoints, inhouzSubscriptions)]
    KV --> SU[getSystemUser]
    KV --> SBU[getSubscriptionUser]
    KV --> CI
    PA --> FP[(function_parser_ms)]
    PA --> RU[recordApiUsage]
    RU --> M2[(apiUsageLogs, apiMetrics, subscriptionUsageLogs, subscriptions)]
    SUB --> RD[(Redis)]
    SUB --> CI
```

## 14. Open questions

- Does the platform terminate TLS and set the subdomain headers this service relies on
  (`req.subdomains`, `req.hostname`, `CF-Connecting-IP`)? The Dockerfile and k8s manifests were not
  read in detail.
- What is the intended difference between `FUNCTION_MS_URL`, `FUNCTION_PARSER_MS_URL` and
  `SCHEDULED_TASK_MS_URL`, and why are two of them unused?
- Is `services/api/*.js` an abandoned refactor, or intended to be re-wired?
- Which service consumes `apiMetrics`? Nothing in this repo reads it back.
- Is `service-account.json.enc` still needed? It is not referenced by `server.js` or `config/`.
- Not read (step budget): `getCachedApi.js` after line 80, `getApi.js` after line 120,
  `apiKeyValidation.js` after line 100, the five policy middlewares, `recordApiUsage.js` bodies,
  `getSubscriptionUser.js`, `getSystemUser.js`, `cacheManager.js` after line 60, and all models.
  Claims about those rest on grep output.
