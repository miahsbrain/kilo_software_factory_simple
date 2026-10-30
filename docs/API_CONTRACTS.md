# API CONTRACTS

The route surface of the 75 Node.js/Express microservices under `apps/`. Every service is its own git repository; citations below are relative to that service's repository root. Route declarations were read from the `app.<method>(...)` calls in `controller/` and `server.js`, not from the skeletons.

## 1. Summary

Each service is one Express app started from `server.js`. Routes are not mounted as Express routers; the server calls one function per controller file, and that function registers routes directly on the app:

- `require("./controller/roles/roleRoutes")(app)` — `authentication_ms/server.js:65`
- `require("./controller/paymentRoutes")(app)` — `payment_ms/server.js:58`
- `require("./controller/appBuilder/appBuilderRoutes")(app)` — `app_builder_ms/server.js:125`
- `require("./controller/payment/paymentRoutes")(app)` — `inhouz_pay_ms/server.js:79`

The path convention is `/api/<domain>/<action>`, where `<domain>` is the ingress prefix and `<action>` is a lowercase verb-like token. Most services declare every route in one controller file per domain area; a few split by concern (`payment_ms` has `controller/paymentRoutes.js` and `controller/payoutRoutes.js`). `POST` carries almost every operation, `GET` is used for reads that take no body, and `DELETE` for deletes.

The public surface is declared in one file: `authentication_ms/k8s/inhouz-ingress-service.yml`. It maps host paths to sibling service ports. The `inhouz.io` host block has 70 path→service→port entries; across all six host blocks there are 71 distinct paths and 72 distinct path/service/port triplets, repeated 325 times in total. The task brief said 78 entries; the YAML has 70 on the primary host, so the code's count is used here.

### 1.1 Public ingress map (inhouz.io host)

| Path | Service | Port | Ingress line |
|---|---|---|---|
| `/` | `inhouzio-app-ms-cluster-ip-service` | 5000 | `authentication_ms/k8s/inhouz-ingress-service.yml:36` |
| `/api/authentication` | `authentication-ms-cluster-ip-service` | 5002 | `authentication_ms/k8s/inhouz-ingress-service.yml:44` |
| `/api/moduletransfer` | `module-transfer-ms-cluster-ip-service` | 5078 | `authentication_ms/k8s/inhouz-ingress-service.yml:52` |
| `/api/moduletransferparser` | `module-transfer-parser-ms-cluster-ip-service` | 5077 | `authentication_ms/k8s/inhouz-ingress-service.yml:60` |
| `/api/database` | `flex-module-collection-ms-cluster-ip-service` | 5004 | `authentication_ms/k8s/inhouz-ingress-service.yml:68` |
| `/api/flexmodule` | `flex-module-collection-ms-cluster-ip-service` | 5004 | `authentication_ms/k8s/inhouz-ingress-service.yml:76` |
| `/api/flexcollection` | `flex-module-collection-ms-cluster-ip-service` | 5004 | `authentication_ms/k8s/inhouz-ingress-service.yml:84` |
| `/api/flexapi` | `flex-api-ms-cluster-ip-service` | 5006 | `authentication_ms/k8s/inhouz-ingress-service.yml:92` |
| `/api/function` | `functions-ms-cluster-ip-service` | 5001 | `authentication_ms/k8s/inhouz-ingress-service.yml:100` |
| `/api/permissions` | `authentication-ms-cluster-ip-service` | 5002 | `authentication_ms/k8s/inhouz-ingress-service.yml:108` |
| `/api/roles` | `authentication-ms-cluster-ip-service` | 5002 | `authentication_ms/k8s/inhouz-ingress-service.yml:116` |
| `/api/userroles` | `authentication-ms-cluster-ip-service` | 5002 | `authentication_ms/k8s/inhouz-ingress-service.yml:124` |
| `/api/scheduledtask` | `scheduled-task-ms-cluster-ip-service` | 5007 | `authentication_ms/k8s/inhouz-ingress-service.yml:132` |
| `/api/secret` | `functions-ms-cluster-ip-service` | 5001 | `authentication_ms/k8s/inhouz-ingress-service.yml:140` |
| `/api/users` | `authentication-ms-cluster-ip-service` | 5002 | `authentication_ms/k8s/inhouz-ingress-service.yml:148` |
| `/api/fileoperations` | `file-operations-ms-cluster-ip-service` | 5008 | `authentication_ms/k8s/inhouz-ingress-service.yml:156` |
| `/api/subscriptionservice` | `subscription-ms-cluster-ip-service` | 5005 | `authentication_ms/k8s/inhouz-ingress-service.yml:164` |
| `/api/servicediscount` | `subscription-ms-cluster-ip-service` | 5005 | `authentication_ms/k8s/inhouz-ingress-service.yml:172` |
| `/api/subscriber` | `subscription-ms-cluster-ip-service` | 5005 | `authentication_ms/k8s/inhouz-ingress-service.yml:180` |
| `/api/functionparser` | `function-parser-ms-cluster-ip-service` | 5035 | `authentication_ms/k8s/inhouz-ingress-service.yml:188` |
| `/api/subscriptionmetrics` | `subscription-metrics-ms-cluster-ip-service` | 5011 | `authentication_ms/k8s/inhouz-ingress-service.yml:196` |
| `/api/company` | `authentication-ms-cluster-ip-service` | 5002 | `authentication_ms/k8s/inhouz-ingress-service.yml:204` |
| `/api/filestorageservice` | `flex-module-collection-ms-cluster-ip-service` | 5004 | `authentication_ms/k8s/inhouz-ingress-service.yml:212` |
| `/api/multimedia` | `multimedia-ms-cluster-ip-service` | 5013 | `authentication_ms/k8s/inhouz-ingress-service.yml:220` |
| `/api/payment` | `payment-ms-cluster-ip-service` | 5014 | `authentication_ms/k8s/inhouz-ingress-service.yml:228` |
| `/api/payoutaccount` | `payment-ms-cluster-ip-service` | 5014 | `authentication_ms/k8s/inhouz-ingress-service.yml:236` |
| `/api/appbuilder` | `app-builder-ms-cluster-ip-service` | 5016 | `authentication_ms/k8s/inhouz-ingress-service.yml:244` |
| `/api/viewbuilder` | `view-builder-ms-cluster-ip-service` | 5017 | `authentication_ms/k8s/inhouz-ingress-service.yml:252` |
| `/api/remoteexecution` | `database-execution-ms-cluster-ip-service` | 5021 | `authentication_ms/k8s/inhouz-ingress-service.yml:260` |
| `/api/systemuser` | `system-user-ms-cluster-ip-service` | 5022 | `authentication_ms/k8s/inhouz-ingress-service.yml:268` |
| `/api/subscribe` | `subscription-signup-ms-cluster-ip-service` | 5023 | `authentication_ms/k8s/inhouz-ingress-service.yml:276` |
| `/api/servicemigration` | `subscription-migration-parser-ms-cluster-ip-service` | 5025 | `authentication_ms/k8s/inhouz-ingress-service.yml:284` |
| `/api/subscriptionrenewal` | `subscription-renewal-ms-cluster-ip-service` | 5027 | `authentication_ms/k8s/inhouz-ingress-service.yml:292` |
| `/api/subscriptionauthentication` | `subscription-authentication-ms-cluster-ip-service` | 5030 | `authentication_ms/k8s/inhouz-ingress-service.yml:300` |
| `/api/subscriptionauthorization` | `subscription-authorization-ms-cluster-ip-service` | 5031 | `authentication_ms/k8s/inhouz-ingress-service.yml:308` |
| `/api/subscriptionpayment` | `subscription-payment-ms-cluster-ip-service` | 5032 | `authentication_ms/k8s/inhouz-ingress-service.yml:316` |
| `/api/subscriptionsettings` | `subscription-settings-ms-cluster-ip-service` | 5033 | `authentication_ms/k8s/inhouz-ingress-service.yml:324` |
| `/api/imageproxy` | `image-proxy-ms-cluster-ip-service` | 5034 | `authentication_ms/k8s/inhouz-ingress-service.yml:332` |
| `/api/scheduledtaskparser` | `scheduled-task-parser-ms-cluster-ip-service` | 5037 | `authentication_ms/k8s/inhouz-ingress-service.yml:340` |
| `/api/scheduledtaskfunctionparser` | `scheduled-task-function-parser-ms-cluster-ip-service` | 5038 | `authentication_ms/k8s/inhouz-ingress-service.yml:348` |
| `/api/webcomponent` | `webcomponent-ms-cluster-ip-service` | 5039 | `authentication_ms/k8s/inhouz-ingress-service.yml:356` |
| `/appbuildersocket` | `appbuilder-multiplayer-ms-cluster-ip-service` | 5019 | `authentication_ms/k8s/inhouz-ingress-service.yml:364` |
| `/api/accounttermination` | `account-termination-ms-cluster-ip-service` | 5048 | `authentication_ms/k8s/inhouz-ingress-service.yml:372` |
| `/api/generaltaskparser` | `general-task-parser-ms-cluster-ip-service` | 5042 | `authentication_ms/k8s/inhouz-ingress-service.yml:380` |
| `/api/inhouzsubscription` | `inhouz-subscription-ms-cluster-ip-service` | 5041 | `authentication_ms/k8s/inhouz-ingress-service.yml:388` |
| `/api/inhouzsubscriptionrenewal` | `inhouz-subscription-renewal-ms-cluster-ip-service` | 5044 | `authentication_ms/k8s/inhouz-ingress-service.yml:396` |
| `/api/latepayment` | `late-payment-ms-cluster-ip-service` | 5051 | `authentication_ms/k8s/inhouz-ingress-service.yml:404` |
| `/api/paymentvalidator` | `payment-validation-ms-cluster-ip-service` | 5050 | `authentication_ms/k8s/inhouz-ingress-service.yml:412` |
| `/api/remotenetworkrequest` | `remote-network-request-ms-cluster-ip-service` | 5045 | `authentication_ms/k8s/inhouz-ingress-service.yml:420` |
| `/api/subscriberdatafunction` | `subscriber-data-function-ms-cluster-ip-service` | 5055 | `authentication_ms/k8s/inhouz-ingress-service.yml:428` |
| `/api/inhouzfileupload` | `inhouz-file-upload-ms-cluster-ip-service` | 5053 | `authentication_ms/k8s/inhouz-ingress-service.yml:436` |
| `/api/appmetrics` | `app-metrics-ms-cluster-ip-service` | 5054 | `authentication_ms/k8s/inhouz-ingress-service.yml:444` |
| `/api/inhouzpay` | `inhouz-pay-ms-cluster-ip-service` | 5058 | `authentication_ms/k8s/inhouz-ingress-service.yml:452` |
| `/api/customerportal` | `customer-portal-ms-cluster-ip-service` | 5062 | `authentication_ms/k8s/inhouz-ingress-service.yml:460` |
| `/api/inhouzcommerce` | `inhouz-commerce-ms-cluster-ip-service` | 5060 | `authentication_ms/k8s/inhouz-ingress-service.yml:468` |
| `/api/inhouzpaymetrics` | `inhouz-pay-metrics-ms-cluster-ip-service` | 5064 | `authentication_ms/k8s/inhouz-ingress-service.yml:476` |
| `/api/inhouzpayrecurringstats` | `inhouz-pay-recurring-stats-ms-cluster-ip-service` | 5063 | `authentication_ms/k8s/inhouz-ingress-service.yml:484` |
| `/api/paymentgateway` | `payment-gateway-ms-cluster-ip-service` | 5057 | `authentication_ms/k8s/inhouz-ingress-service.yml:492` |
| `/api/paymentlink` | `payment-link-ms-cluster-ip-service` | 5059 | `authentication_ms/k8s/inhouz-ingress-service.yml:500` |
| `/api/appviewerlog` | `appviewer-log-ms-cluster-ip-service` | 5046 | `authentication_ms/k8s/inhouz-ingress-service.yml:508` |
| `/api/contacts` | `contact-ms-cluster-ip-service` | 5071 | `authentication_ms/k8s/inhouz-ingress-service.yml:516` |
| `/api/documentgeneratorparser` | `document-generation-parser-ms-cluster-ip-service` | 5069 | `authentication_ms/k8s/inhouz-ingress-service.yml:524` |
| `/api/inhouzproject` | `inhouz-project-ms-cluster-ip-service` | 5067 | `authentication_ms/k8s/inhouz-ingress-service.yml:532` |
| `/api/inhouzsecurity` | `inhouz-security-ms-cluster-ip-service` | 5068 | `authentication_ms/k8s/inhouz-ingress-service.yml:540` |
| `/api/inhouzsign` | `inhouz-sign-ms-cluster-ip-service` | 5065 | `authentication_ms/k8s/inhouz-ingress-service.yml:548` |
| `/api/inhouzsignmetrics` | `inhouz-sign-metrics-ms-cluster-ip-service` | 5070 | `authentication_ms/k8s/inhouz-ingress-service.yml:556` |
| `/api/pdfgenerator` | `pdf-generator-ms-cluster-ip-service` | 5072 | `authentication_ms/k8s/inhouz-ingress-service.yml:564` |
| `/api/appversionmanager` | `app-version-manager-ms-cluster-ip-service` | 5074 | `authentication_ms/k8s/inhouz-ingress-service.yml:572` |
| `/api/pushnotificationparser` | `push-notification-parser-ms-cluster-ip-service` | 5076 | `authentication_ms/k8s/inhouz-ingress-service.yml:580` |
| `/api/websiteresource` | `website-resource-ms-cluster-ip-service` | 5056 | `authentication_ms/k8s/inhouz-ingress-service.yml:588` |

Services with no HTTP route are reached only over scheduled work or the private network; they are listed in §3.10.

## 2. Auth model

Every service carries its own copy of the middleware under `middlewares/`. There is no shared package, so a fix in one copy does not reach the others.

### 2.1 Middleware vocabulary

| Name | What it checks | Definition |
|---|---|---|
| `checkLogin` (mounted as `isLoggedIn`) | Session cookie `SMPL` or header `x-access-token`, plus header `x-csrfToken`; decrypts the session id with Cryptr and loads the session record. Missing token or bad session returns **HTTP 200** with `{error:{message:'Not Authorized'}}`. | `payment_ms/middlewares/login/checkLogin.js:9-20` |
| `isLoggedIn` | Alias for `checkLogin`; controllers write `const isLoggedIn = require('../middlewares/login/checkLogin')`. | `payment_ms/controller/paymentRoutes.js:9` |
| `moduleAccessCheck` | Checks the module name suffix against `req.user.companyId` and loads the module from Mongo. Returns 200 with `{error:{message:'Module Access Denied'}}`. | `payment_ms/middlewares/module/moduleAccessCheck.js:7-41` |
| `isSubscriptionAdmin` | Permission check on the subscription admin permission. Returns 200 with an error body. | `account_termination_ms/middlewares/permissions/isSubscriptionAdmin.js:1` |
| `isAdmin` | Checks `user.permissions` contains the configured admin permission. Returns 200 with `{error:{message:'Not Authorized.'}}`. | `authentication_ms/middlewares/permissions/isAdmin.js:3-16` |
| `isPaymentDeveloper` | Payment-developer permission check. Returns 200 with an error body. | `payment_ms/middlewares/permissions/isPaymentDeveloper.js:3` |
| `isPaymentAdmin` | Payment-admin permission check. Returns 200 with an error body. | `payment_ms/middlewares/permissions/isPaymentAdmin.js:3` |
| `apiKeyValidation` | Reads `X-SE-API-KEY` or `X-CE-API-KEY`, decrypts it and loads the system user. **If the header is absent it calls `next()`** — an optional authenticator, not an enforcement gate. | `account_termination_ms/middlewares/apiKey/apiKeyValidation.js:6-18` |
| `clientEncryptedLogin` | Reads `clientEncryptedAccessHeader`, RSA-decrypts it, checks `expirationTimestamp`, loads `req.user`. **Calls `next()` when the header is absent.** | `inhouz_pay_ms/middlewares/login/clientEncryptedLogin.js:6-24` |
| `serverEncryptedLogin` | Reads `serverEncryptedAccessHeader`, Cryptr-decrypts it, checks `expirationTimestamp`, loads `req.user`. **Calls `next()` when the header is absent.** | `inhouz_pay_ms/middlewares/login/serverEncryptedLogin.js:7-26` |
| `singleSubdomainValidation` | Checks that `req.subdomains` has one entry equal to `www` or `req.user.subDomain`. Returns 200 with `{error:{message:'Failed subdomain validation'}}`. | `payment_ms/middlewares/subdomain/singleSubdomainValidation.js:1-19` |

`apiKeyValidation`, `clientEncryptedLogin` and `serverEncryptedLogin` are permissive by design: a request with no matching header passes through. Authorization depends on whatever follows them (`isLoggedIn`, a permission middleware, or nothing).

### 2.2 Which service mounts which

Counts are route declarations that name the middleware. Only the ten shared names above are counted; domain guards such as `companyAccountCheck`, `subdomainCheck`, `checkPortalLogin` and `isAllowedDeveloper` are not.

| Unit | Routes | Auth middleware mounted |
|---|---|---|
| `account_termination_ms` | 3 | isLoggedIn (2), isSubscriptionAdmin, isAdmin, apiKeyValidation |
| `api_service_ms` | 5 | apiKeyValidation (5) |
| `app_builder_ms` | 43 | isLoggedIn (41), apiKeyValidation (3), clientEncryptedLogin (3), serverEncryptedLogin (3) |
| `app_metrics_ms` | 7 | isLoggedIn (7), isAdmin (7) |
| `app_version_manager_ms` | 1 | none |
| `appviewer_log_ms` | 5 | none |
| `appviewer_password_ms` | 1 | none |
| `authentication_ms` | 32 | isLoggedIn (23), isAdmin (13), apiKeyValidation (2) |
| `contact_ms` | 5 | isLoggedIn (5) |
| `customer_portal_ms` | 5 | none |
| `database_execution_ms` | 3 | isLoggedIn (1) |
| `document_generation_parser_ms` | 2 | none |
| `file_operations_ms` | 5 | isLoggedIn (3) |
| `flex_api_ms` | 16 | isLoggedIn (11) |
| `flex_module_collection_ms` | 23 | isLoggedIn (23) |
| `function_parser_ms` | 1 | none |
| `functions_ms` | 16 | isLoggedIn (13) |
| `general_task_parser_ms` | 7 | none |
| `image_proxy_ms` | 5 | none |
| `inhouz_commerce_ms` | 17 | isLoggedIn (12) |
| `inhouz_file_upload_ms` | 4 | isLoggedIn (3) |
| `inhouz_pay_metrics_ms` | 11 | checkLogin (11), isPaymentDeveloper (11) |
| `inhouz_pay_ms` | 38 | isLoggedIn (4), isPaymentDeveloper (2), apiKeyValidation (1), clientEncryptedLogin (1), serverEncryptedLogin (1) |
| `inhouz_pay_recurring_stats_ms` | 1 | none |
| `inhouz_project_ms` | 15 | isLoggedIn (15), apiKeyValidation (7), clientEncryptedLogin (7), serverEncryptedLogin (7) |
| `inhouz_security_ms` | 7 | none |
| `inhouz_sign_metrics_ms` | 6 | checkLogin (5) |
| `inhouz_sign_ms` | 45 | isLoggedIn (31), apiKeyValidation (11), clientEncryptedLogin (11), serverEncryptedLogin (11) |
| `inhouz_subscription_ms` | 6 | isLoggedIn (4), isAdmin (3) |
| `inhouz_subscription_renewal_ms` | 3 | none |
| `inhouzio_app_ms` | 1 | none |
| `late_payment_ms` | 1 | isSubscriptionAdmin (1) |
| `module_transfer_ms` | 9 | isLoggedIn (9) |
| `module_transfer_parser_ms` | 1 | isLoggedIn (1) |
| `multimedia_ms` | 6 | isLoggedIn (1) |
| `payment_gateway_ms` | 52 | isLoggedIn (37), apiKeyValidation (1), clientEncryptedLogin (1), serverEncryptedLogin (1) |
| `payment_link_ms` | 31 | isLoggedIn (15) |
| `payment_ms` | 18 | isLoggedIn (16), isPaymentDeveloper (1) |
| `payment_validation_ms` | 4 | none |
| `pdf_generator_ms` | 14 | isLoggedIn (11) |
| `push_notification_parser_ms` | 1 | none |
| `remote_network_request_ms` | 2 | none |
| `scheduled_task_function_parser_ms` | 1 | none |
| `scheduled_task_ms` | 9 | isLoggedIn (6) |
| `scheduled_task_parser_ms` | 2 | none |
| `subscriber_data_function_ms` | 4 | none |
| `subscription_authentication_ms` | 7 | none |
| `subscription_authorization_ms` | 1 | none |
| `subscription_metrics_ms` | 16 | isLoggedIn (10), isSubscriptionAdmin (10) |
| `subscription_migration_parser_ms` | 3 | checkLogin (1), isSubscriptionAdmin (1) |
| `subscription_migration_scheduler_ms` | 1 | none |
| `subscription_ms` | 29 | isLoggedIn (17), isSubscriptionAdmin (4), apiKeyValidation (4), clientEncryptedLogin (1), serverEncryptedLogin (1) |
| `subscription_payment_ms` | 7 | isLoggedIn (7), isAdmin (7) |
| `subscription_renewal_ms` | 2 | none |
| `subscription_renewal_scheduler_ms` | 1 | none |
| `subscription_settings_ms` | 2 | isLoggedIn (2) |
| `subscription_signup_ms` | 6 | apiKeyValidation (3), checkLogin (1), isSubscriptionAdmin (2) |
| `system_users_ms` | 10 | checkLogin (8) |
| `view_builder_ms` | 9 | isLoggedIn (7), apiKeyValidation (1), clientEncryptedLogin (1), serverEncryptedLogin (1) |
| `webcomponent_ms` | 7 | isLoggedIn (6), isSubscriptionAdmin (3) |
| `website_resource_ms` | 3 | none |
| `websocket_ms` | 1 | none |

### 2.3 Services that mount no auth middleware

These services register routes without any of the ten shared auth middlewares. Some are internal-only, but `customer_portal_ms`, `inhouz_security_ms`, `website_resource_ms` and `subscription_authorization_ms` are on public ingress paths.

`app_version_manager_ms`, `appviewer_log_ms`, `appviewer_password_ms`, `customer_portal_ms`, `document_generation_parser_ms`, `function_parser_ms`, `general_task_parser_ms`, `image_proxy_ms`, `inhouz_pay_recurring_stats_ms`, `inhouz_security_ms`, `inhouz_subscription_renewal_ms`, `inhouzio_app_ms`, `payment_validation_ms`, `push_notification_parser_ms`, `remote_network_request_ms`, `scheduled_task_function_parser_ms`, `scheduled_task_parser_ms`, `subscriber_data_function_ms`, `subscription_authentication_ms`, `subscription_authorization_ms`, `subscription_migration_scheduler_ms`, `subscription_renewal_ms`, `subscription_renewal_scheduler_ms`, `website_resource_ms`, `websocket_ms`

The 13 units with no HTTP routes at all are listed in §3.10; they mount no auth middleware because they register no route.

### 2.4 Unauthenticated routes that move money or write tenant data

These declarations have no middleware token at all. They are public ingress paths unless noted.

| Path | Unit | file:line | Risk |
|---|---|---|---|
| `POST /api/payment/stripe/addsubscriptionpaymentmethod` | `payment_ms` | `payment_ms/controller/paymentRoutes.js:21` | attaches a payment method without a session |
| `POST /api/payoutaccount/sanitycheck` | `payment_ms` | `payment_ms/controller/payoutRoutes.js:21` | payout-account validation without a session |
| `POST /api/paymentlink/recordsplitpayment` | `payment_link_ms` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:67` | records a split payment |
| `POST /api/paymentlink/markpaymentlinkasused` | `payment_link_ms` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:68` | marks a payment link used |
| `POST /api/paymentlink/setactivestatus` | `payment_link_ms` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:69` | changes a link's active state |
| `POST /api/inhouzpay/stripe/createpaymentintent` | `inhouz_pay_ms` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:43` | creates a Stripe payment intent |
| `POST /api/inhouzpay/stripe/finalizestripeuipayment` | `inhouz_pay_ms` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:46` | finalizes a payment |
| `POST /api/inhouzpay/payment/markassuccess` | `inhouz_pay_ms` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:49` | marks a payment successful |
| `POST /api/inhouzpay/payment/serversubscriptionpayment` | `inhouz_pay_ms` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:62` | server-side subscription charge |
| `POST /api/inhouzpay/payment/subscription/addsubscribers` | `inhouz_pay_ms` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:76` | writes subscriber records |
| `POST /api/inhouzpay/payment/subscription/ondemand/web` | `inhouz_pay_ms` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:78` | on-demand charge |
| `POST /api/inhouzpay/payment/subscription/ondemand/server` | `inhouz_pay_ms` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:79` | on-demand charge |
| `POST /api/inhouzcommerce/product/servercreate` | `inhouz_commerce_ms` | `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:15` | creates a tenant product |
| `POST /api/inhouzcommerce/product/markaspurchased` | `inhouz_commerce_ms` | `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:23` | marks a product purchased |
| `POST /api/paymentgateway/distribution/createaccount` | `payment_gateway_ms` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:66` | creates a distribution account |
| `POST /api/paymentgateway/distribution/distribute/serverrun` | `payment_gateway_ms` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:79` | runs a money distribution |

`api_service_ms` is a separate case: its five catch-all routes (`GET|POST|PUT|PATCH|DELETE *`) attach `apiKeyValidation` after the policy middleware, so the API gateway's authorization is the policy chain, not `isLoggedIn` (`api_service_ms/controller/apiService/apiRoute.js:12-16`).

## 3. Route catalogue

One table per unit. Where a unit has many routes, paths are grouped by prefix and the group cites the first route line; the unit handover has the per-route detail. `—` in the auth column means no middleware was declared on that route.

Excluded routes: `payment_ms` has two commented-out Braintree routes at `payment_ms/controller/paymentRoutes.js:18-19`; `payment_link_ms` has eight commented-out subscriber routes at `payment_link_ms/controller/payment/paymentLinkRoutes.js:73-80`; `function_parser_ms/lib/routes/index.js:6-8` is an entirely commented-out router that is not mounted. Code wins over the skeletons, so these are not in the tables.

### 3.1 Identity, access and account lifecycle

#### `authentication_ms` (32 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/userroles/updateuserroles` | `authentication_ms/controller/userRoles/userRolesRoute.js:12` | isLoggedIn, companyAccountCheck, subdomainCheck, isAdmin |
| POST | `/api/userroles/automateupdateuserroles` | `authentication_ms/controller/userRoles/userRolesRoute.js:13` | apiKeyValidation, isAdmin, resolveEncryptedAutomationPayload |
| POST | `/api/userroles/getusersroles` | `authentication_ms/controller/userRoles/userRolesRoute.js:14` | isLoggedIn, subdomainCheck |
| POST | `/api/userroles/getuserroles` | `authentication_ms/controller/userRoles/userRolesRoute.js:15` | isLoggedIn, subdomainCheck |
| POST | `/api/authentication/login` | `authentication_ms/controller/Auth/authController.js:12` | — |
| POST | `/api/authentication/logout` | `authentication_ms/controller/Auth/authController.js:13` | — |
| POST | `/api/authentication/validatetwofactor` | `authentication_ms/controller/Auth/authController.js:14` | — |
| POST | `/api/authentication/resendtwofactor` | `authentication_ms/controller/Auth/authController.js:15` | — |
| POST | `/api/authentication/forgotpassword` | `authentication_ms/controller/Auth/authController.js:16` | — |
| POST | `/api/authentication/changepassword` | `authentication_ms/controller/Auth/authController.js:17` | — |
| POST | `/api/authentication/checksubdomainavailability` | `authentication_ms/controller/Auth/authController.js:18` | — |
| GET | `/api/authentication/getloggedinuser` | `authentication_ms/controller/Auth/authController.js:19` | isLoggedIn |
| POST | `/api/authentication/registercompany` | `authentication_ms/controller/signup/signUpController.js:4` | — |
| POST | `/api/roles/create` | `authentication_ms/controller/roles/roleRoutes.js:12` | isLoggedIn, companyAccountCheck, subdomainCheck, isAdmin |
| POST | `/api/roles/edit` | `authentication_ms/controller/roles/roleRoutes.js:13` | isLoggedIn, companyAccountCheck, subdomainCheck, isAdmin |
| POST | `/api/roles/delete` | `authentication_ms/controller/roles/roleRoutes.js:14` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/roles/getroles` | `authentication_ms/controller/roles/roleRoutes.js:15` | isLoggedIn, subdomainCheck |
| GET | `/api/roles/getrole/:roleId` | `authentication_ms/controller/roles/roleRoutes.js:16` | isLoggedIn, subdomainCheck |
| POST | `/api/users/addusers` | `authentication_ms/controller/user/userRoutes.js:16` | apiKeyValidation, isLoggedIn, companyAccountCheck, subdomainCheck, isAdmin |
| POST | `/api/users/edituser` | `authentication_ms/controller/user/userRoutes.js:17` | isLoggedIn, companyAccountCheck, subdomainCheck, canEditUser |
| GET | `/api/users/getapikey` | `authentication_ms/controller/user/userRoutes.js:18` | isLoggedIn, companyAccountCheck, subdomainCheck |
| POST | `/api/users/changeapikey` | `authentication_ms/controller/user/userRoutes.js:19` | isLoggedIn, companyAccountCheck, subdomainCheck |
| GET | `/api/users/getcompanymembers` | `authentication_ms/controller/user/userRoutes.js:20` | isLoggedIn |
| GET | `/api/users/getsessions/:skip/:limit` | `authentication_ms/controller/user/userRoutes.js:21` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/users/endsession` | `authentication_ms/controller/user/userRoutes.js:22` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/permissions/create` | `authentication_ms/controller/permissions/permissonRoutes.js:12` | isLoggedIn, companyAccountCheck, subdomainCheck, isAdmin |
| POST | `/api/permissions/edit` | `authentication_ms/controller/permissions/permissonRoutes.js:13` | isLoggedIn, companyAccountCheck, subdomainCheck, isAdmin |
| POST | `/api/permissions/delete` | `authentication_ms/controller/permissions/permissonRoutes.js:14` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/permissions/getpermissions` | `authentication_ms/controller/permissions/permissonRoutes.js:15` | isLoggedIn, subdomainCheck |
| GET | `/api/permissions/getpermission/:permissionId` | `authentication_ms/controller/permissions/permissonRoutes.js:16` | isLoggedIn, subdomainCheck |
| POST | `/api/company/update` | `authentication_ms/controller/company/companyRoutes.js:8` | isLoggedIn, subdomainCheck, isAdmin |
| GET | `/api/company/get` | `authentication_ms/controller/company/companyRoutes.js:9` | isLoggedIn, subdomainCheck, isAdmin |

#### `system_users_ms` (10 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/systemuser/create` | `system_users_ms/controller/systemUser/systemUserRoutes.js:15` | checkLogin, companyAccountCheck |
| POST | `/api/systemuser/editfield` | `system_users_ms/controller/systemUser/systemUserRoutes.js:16` | checkLogin, companyAccountCheck |
| POST | `/api/systemuser/edit` | `system_users_ms/controller/systemUser/systemUserRoutes.js:17` | checkLogin, companyAccountCheck |
| POST | `/api/systemuser/getsystemusers` | `system_users_ms/controller/systemUser/systemUserRoutes.js:18` | checkLogin, companyAccountCheck |
| GET | `/api/systemuser/getsystemuser/:systemUserId` | `system_users_ms/controller/systemUser/systemUserRoutes.js:19` | checkLogin |
| POST | `/api/systemuser/delete` | `system_users_ms/controller/systemUser/systemUserRoutes.js:20` | checkLogin |
| POST | `/api/systemuser/validateusername` | `system_users_ms/controller/systemUser/systemUserRoutes.js:21` | checkLogin |
| POST | `/api/systemuser/getapikey` | `system_users_ms/controller/systemUser/systemUserRoutes.js:22` | checkLogin, companyAccountCheck |
| POST | `/api/systemuser/getencryptedapikey` | `system_users_ms/controller/systemUser/systemUserRoutes.js:23` | — |
| POST | `/api/systemuser/getappbuildersystemusers` | `system_users_ms/controller/systemUser/systemUserRoutes.js:24` | — |

#### `contact_ms` (5 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/contacts/create` | `contact_ms/controller/contact/contactRoutes.js:11` | isLoggedIn, hasWriteAccess |
| POST | `/api/contacts/edit` | `contact_ms/controller/contact/contactRoutes.js:12` | isLoggedIn, hasWriteAccess |
| DELETE | `/api/contacts/delete/:contactId` | `contact_ms/controller/contact/contactRoutes.js:13` | isLoggedIn, hasWriteAccess |
| POST | `/api/contacts/getcontacts` | `contact_ms/controller/contact/contactRoutes.js:14` | isLoggedIn, hasReadAccess |
| GET | `/api/contacts/getcontact/:contactId` | `contact_ms/controller/contact/contactRoutes.js:15` | isLoggedIn, hasReadAccess |

#### `customer_portal_ms` (5 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/customerportal/requestpassword` | `customer_portal_ms/controller/customerPortal/customerPortalRoutes.js:8` | — |
| POST | `/api/customerportal/login` | `customer_portal_ms/controller/customerPortal/customerPortalRoutes.js:9` | — |
| POST | `/api/customerportal/getloggedincustomer` | `customer_portal_ms/controller/customerPortal/customerPortalRoutes.js:10` | — |
| POST | `/api/customerportal/logout` | `customer_portal_ms/controller/customerPortal/customerPortalRoutes.js:11` | — |
| GET | `/api/customerportal/getportalmetadata/:subDomain` | `customer_portal_ms/controller/customerPortal/customerPortalRoutes.js:12` | — |

#### `inhouz_security_ms` (7 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzsecurity/requestuserpassword` | `inhouz_security_ms/controller/security/securityRoutes.js:10` | — |
| POST | `/api/inhouzsecurity/passwordlogin` | `inhouz_security_ms/controller/security/securityRoutes.js:11` | — |
| POST | `/api/inhouzsecurity/questionnaireauth` | `inhouz_security_ms/controller/security/securityRoutes.js:12` | — |
| POST | `/api/inhouzsecurity/getdocumentverificationclientsecret` | `inhouz_security_ms/controller/security/securityRoutes.js:13` | — |
| POST | `/api/inhouzsecurity/registerdocumentverification` | `inhouz_security_ms/controller/security/securityRoutes.js:14` | — |
| POST | `/api/inhouzsecurity/documentverificationstatuscheck` | `inhouz_security_ms/controller/security/securityRoutes.js:15` | — |
| POST | `/api/inhouzsecurity/documentverificationlogin` | `inhouz_security_ms/controller/security/securityRoutes.js:16` | — |

#### `subscription_authentication_ms` (7 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscriptionauthentication/weblogin` | `subscription_authentication_ms/controller/auth/authRoutes.js:10` | — |
| POST | `/api/subscriptionauthentication/appviewerlogin` | `subscription_authentication_ms/controller/auth/authRoutes.js:11` | — |
| POST | `/api/subscriptionauthentication/weblogout` | `subscription_authentication_ms/controller/auth/authRoutes.js:12` | — |
| POST | `/api/subscriptionauthentication/validatetwofactor` | `subscription_authentication_ms/controller/auth/authRoutes.js:13` | — |
| POST | `/api/subscriptionauthentication/resendtwofactor` | `subscription_authentication_ms/controller/auth/authRoutes.js:14` | — |
| POST | `/api/subscriptionauthentication/forgotpassword` | `subscription_authentication_ms/controller/auth/authRoutes.js:15` | — |
| POST | `/api/subscriptionauthentication/changepassword` | `subscription_authentication_ms/controller/auth/authRoutes.js:16` | — |

#### `subscription_authorization_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscriptionauthorization/getloggedinuser` | `subscription_authorization_ms/controller/auth/authRoutes.js:4` | — |

#### `websocket_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `/api/helloworld` | `websocket_ms/controller/helloWorld/helloRoutes.js:4` | — |

#### `account_termination_ms` (3 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/accounttermination/inhouzsubscriptiontermination` | `account_termination_ms/controller/terminationRoutes/terminationRoutes.js:12` | isLoggedIn, isAccountOwner |
| POST | `/api/accounttermination/subcriptionservicetermination` | `account_termination_ms/controller/terminationRoutes/terminationRoutes.js:13` | subscriptionCheckLogin, isSubscriptionAdmin |
| POST | `/api/accounttermination/useraccounttermination` | `account_termination_ms/controller/terminationRoutes/terminationRoutes.js:14` | apiKeyValidation, isLoggedIn, isAdmin |

### 3.2 Subscriptions and billing

#### `subscription_ms` (29 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/servicediscount/create` | `subscription_ms/controller/serviceDiscount/serviceDiscountRoutes.js:15` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/servicediscount/edit` | `subscription_ms/controller/serviceDiscount/serviceDiscountRoutes.js:16` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| GET | `/api/servicediscount/getservicediscount/:serviceDiscountId` | `subscription_ms/controller/serviceDiscount/serviceDiscountRoutes.js:17` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/servicediscount/getservicediscounts` | `subscription_ms/controller/serviceDiscount/serviceDiscountRoutes.js:18` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/servicediscount/verifyservicediscount` | `subscription_ms/controller/serviceDiscount/serviceDiscountRoutes.js:19` | lightLoginCheck, subdomainValidator |
| POST | `/api/servicediscount/usage` | `subscription_ms/controller/serviceDiscount/serviceDiscountRoutes.js:20` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/create` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:32` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/clone` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:33` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/edit` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:34` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/deploy` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:35` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/setversion` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:36` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/getsubscription` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:37` | lightLoginCheck, subdomainValidator |
| POST | `/api/subscriptionservice/getsubscriptionservices` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:38` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/getconnectedsubscriptionservices` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:39` | subscriptionCheckLogin, isSubscriptionServiceAdmin, subdomainCheck |
| POST | `/api/subscriptionservice/getsubscriptionserviceversions` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:40` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/subscriptionservice/transfersubscriptions` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:41` | lightLoginCheck |
| POST | `/api/subscriptionservice/addtomigrationqueue` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:42` | lightLoginCheck |
| POST | `/api/subscriptionservice/getmigrationtiers` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:43` | isLoggedIn, companyAccountCheck, subdomainCheck, isSubscriptionAdmin |
| POST | `/api/subscriptionservice/logexternalserviceusage` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:44` | apiKeyValidation, isSubscriptionAdmin |
| POST | `/api/subscriptionservice/checkuseraccess` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:45` | apiKeyValidation, isSubscriptionAdmin |
| POST | `/api/subscriptionservice/signup/getsubscriptionservice` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:46` | lightLoginCheck, subdomainValidator |
| POST | `/api/subscriptionservice/manageuserrestriction` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:47` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, isLoggedIn, isAllowedDeveloper |
| POST | `/api/subscriptionservice/getuserrestrictionlist` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:48` | isLoggedIn, isAllowedDeveloper |
| POST | `/api/subscriptionservice/fieldavailabilitycheck` | `subscription_ms/controller/subscriptionService/subscriptionServiceRoutes.js:49` | isLoggedIn, isAllowedDeveloper |
| POST | `/api/subscriber/getsubscribedusersinfo` | `subscription_ms/controller/subscriber/subscriberRoutes.js:13` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriber/cancelsubscription` | `subscription_ms/controller/subscriber/subscriberRoutes.js:14` | lightLoginCheck |
| POST | `/api/subscriber/automatecancelsubscription` | `subscription_ms/controller/subscriber/subscriberRoutes.js:15` | apiKeyValidation, resolveFunctionGeneratedSubscriberCancellation |
| POST | `/api/subscriber/getsubscriptionapikey` | `subscription_ms/controller/subscriber/subscriberRoutes.js:16` | lightLoginCheck, isSubscriberLoggedIn |
| POST | `/api/subscriber/changesubscriptionapikey` | `subscription_ms/controller/subscriber/subscriberRoutes.js:17` | lightLoginCheck, isSubscriberLoggedIn |

#### `subscription_signup_ms` (6 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscribe/signup` | `subscription_signup_ms/controller/subscribe/subscribeRoutes.js:13` | lightLoginCheck, resolvePaidSignup |
| POST | `/api/subscribe/automatedinitialexternalsignup` | `subscription_signup_ms/controller/subscribe/subscribeRoutes.js:14` | apiKeyValidation, resolveAutomatedInitialExternalSignup |
| POST | `/api/subscribe/automatedsignup` | `subscription_signup_ms/controller/subscribe/subscribeRoutes.js:15` | apiKeyValidation, resolveFunctionGeneratedSignup |
| POST | `/api/subscribe/expansionsignup` | `subscription_signup_ms/controller/subscribe/subscribeRoutes.js:16` | checkLogin, isSubscriptionAdmin |
| POST | `/api/subscribe/automatedexternalsignup` | `subscription_signup_ms/controller/subscribe/subscribeRoutes.js:17` | apiKeyValidation, isSubscriptionAdmin |
| POST | `/api/subscribe/changeplan` | `subscription_signup_ms/controller/subscribe/subscribeRoutes.js:18` | lightLoginCheck |

#### `subscription_payment_ms` (7 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscriptionpayment/getpaymentmethods` | `subscription_payment_ms/controller/paymentRoutes/paymentRoutes.js:12` | isLoggedIn, isAdmin |
| GET | `/api/subscriptionpayment/getpaymentmethod/:paymentMethodId` | `subscription_payment_ms/controller/paymentRoutes/paymentRoutes.js:13` | isLoggedIn, isAdmin |
| POST | `/api/subscriptionpayment/stripe/editpaymentmethod` | `subscription_payment_ms/controller/paymentRoutes/paymentRoutes.js:14` | isLoggedIn, isAdmin |
| POST | `/api/subscriptionpayment/stripe/addpaymentmethod` | `subscription_payment_ms/controller/paymentRoutes/paymentRoutes.js:15` | isLoggedIn, isAdmin |
| POST | `/api/subscriptionpayment/getpaymentintents` | `subscription_payment_ms/controller/paymentRoutes/paymentRoutes.js:16` | isLoggedIn, isAdmin |
| POST | `/api/subscriptionpayment/getpaymentcharges` | `subscription_payment_ms/controller/paymentRoutes/paymentRoutes.js:17` | isLoggedIn, isAdmin |
| POST | `/api/subscriptionpayment/deletepaymentmethod` | `subscription_payment_ms/controller/paymentRoutes/paymentRoutes.js:18` | isLoggedIn, isAdmin |

#### `subscription_settings_ms` (2 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscriptionsettings/updateprofile` | `subscription_settings_ms/controller/subscription/subscriptionSettingsRoutes.js:6` | isLoggedIn |
| POST | `/api/subscriptionsettings/getsubscriberprofile` | `subscription_settings_ms/controller/subscription/subscriptionSettingsRoutes.js:7` | isLoggedIn |

#### `subscription_metrics_ms` (16 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscriptionmetrics/getsubscribedcompanies` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:23` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getsubscribers` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:24` | lightLoginCheck |
| POST | `/api/subscriptionmetrics/getSubscriptions` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:25` | lightLoginCheck |
| POST | `/api/subscriptionmetrics/getserviceusagelogs` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:26` | lightLoginCheck |
| POST | `/api/subscriptionmetrics/getsubscriberactionlogs` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:27` | lightLoginCheck |
| POST | `/api/subscriptionmetrics/getsubscribedpackages` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:28` | — |
| POST | `/api/subscriptionmetrics/getSubscribedServices` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:29` | lightLoginCheck |
| POST | `/api/subscriptionmetrics/getsubscribercount` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:30` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getdailyactiveusercount` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:31` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getrecurringrevenue` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:32` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getcurrentrecurringrevenue` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:33` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getrecurringrevenues` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:34` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getdailyrecurringrevenues` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:35` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getchurndata` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:36` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/getlifetimevalue` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:37` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/subscriptionmetrics/subscribercountchart` | `subscription_metrics_ms/controller/subscription/subscriptionRoutes.js:38` | isLoggedIn, isSubscriptionAdmin |

#### `subscription_renewal_ms` (2 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscriptionrenewal/internal` | `subscription_renewal_ms/controller/subscription/subscriptionRoutes.js:7` | — |
| POST | `/api/subscriptionrenewal/external` | `subscription_renewal_ms/controller/subscription/subscriptionRoutes.js:8` | — |

#### `inhouz_subscription_ms` (6 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzsubscription/initialsubscription` | `inhouz_subscription_ms/controller/inhouzSubscription/subscriptionRoutes.js:11` | — |
| POST | `/api/inhouzsubscription/changeplan` | `inhouz_subscription_ms/controller/inhouzSubscription/subscriptionRoutes.js:12` | isLoggedIn |
| POST | `/api/inhouzsubscription/validatediscountcode` | `inhouz_subscription_ms/controller/inhouzSubscription/subscriptionRoutes.js:13` | — |
| POST | `/api/inhouzsubscription/getdiscountcodeusagelog` | `inhouz_subscription_ms/controller/inhouzSubscription/subscriptionRoutes.js:14` | isLoggedIn, isAdmin |
| POST | `/api/inhouzsubscription/updateaccountlicense` | `inhouz_subscription_ms/controller/inhouzSubscription/subscriptionRoutes.js:15` | isLoggedIn, isAdmin |
| GET | `/api/inhouzsubscription/getaccountlicense` | `inhouz_subscription_ms/controller/inhouzSubscription/subscriptionRoutes.js:16` | isLoggedIn, isAdmin |

#### `inhouz_subscription_renewal_ms` (3 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzsubscriptionrenewal/accountsubscriptionrenewal` | `inhouz_subscription_renewal_ms/controller/renewalRoutes/renewalRoutes.js:6` | — |
| POST | `/api/inhouzsubscriptionrenewal/accountutilityrenewal` | `inhouz_subscription_renewal_ms/controller/renewalRoutes/renewalRoutes.js:7` | — |
| POST | `/api/inhouzsubscriptionrenewal/addusers` | `inhouz_subscription_renewal_ms/controller/renewalRoutes/renewalRoutes.js:8` | — |

#### `subscription_migration_parser_ms` (3 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/servicemigration/parse` | `subscription_migration_parser_ms/controller/migration/migrationRoutes.js:9` | — |
| POST | `/api/servicemigration/subscriber/create` | `subscription_migration_parser_ms/controller/migration/migrationRoutes.js:10` | subscriptionCheckLogin, isSubscriptionAdmin |
| POST | `/api/servicemigration/assetowner/create` | `subscription_migration_parser_ms/controller/migration/migrationRoutes.js:11` | checkLogin, isAllowedDeveloper |

### 3.3 Payments, payouts and money movement

#### `payment_ms` (18 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/payment/stripe/addpaymentmethod`<br>`/api/payment/stripe/editpaymentmethod` | `payment_ms/controller/paymentRoutes.js:20` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/payment/stripe/addsubscriptionpaymentmethod` | `payment_ms/controller/paymentRoutes.js:21` | — |
| POST | `/api/payment/getpaymentmethods` | `payment_ms/controller/paymentRoutes.js:23` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| GET | `/api/payment/getpaymentmethod/:paymentMethodId` | `payment_ms/controller/paymentRoutes.js:24` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| DELETE | `/api/payment/deletepaymentmethod/:paymentMethodId` | `payment_ms/controller/paymentRoutes.js:25` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/payment/revenue/getdailyrevenue` | `payment_ms/controller/paymentRoutes.js:26` | isLoggedIn, isPaymentAdmin |
| POST | `/api/payment/setaccountprimary` | `payment_ms/controller/paymentRoutes.js:27` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/payment/getpaymentintents` | `payment_ms/controller/paymentRoutes.js:28` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/payment/getpaymentcharges` | `payment_ms/controller/paymentRoutes.js:29` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/payoutaccount/create` | `payment_ms/controller/payoutRoutes.js:16` | isLoggedIn, companyAccountCheck, subdomainCheck, isPaymentAdmin |
| POST | `/api/payoutaccount/edit` | `payment_ms/controller/payoutRoutes.js:17` | isLoggedIn, companyAccountCheck, subdomainCheck, isPaymentAdmin |
| DELETE | `/api/payoutaccount/delete/:payoutAccountId` | `payment_ms/controller/payoutRoutes.js:18` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| GET | `/api/payoutaccount/get/:payoutAccountId` | `payment_ms/controller/payoutRoutes.js:19` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/payoutaccount/getaccounts` | `payment_ms/controller/payoutRoutes.js:20` | isLoggedIn, subdomainCheck, isPaymentDeveloper |
| POST | `/api/payoutaccount/sanitycheck` | `payment_ms/controller/payoutRoutes.js:21` | — |
| POST | `/api/payoutaccount/stripe/createaccountlink`<br>`/api/payoutaccount/stripe/getconnectaccountdashboardurl` | `payment_ms/controller/payoutRoutes.js:22` | isLoggedIn, companyAccountCheck, subdomainCheck, isPaymentAdmin |

#### `payment_gateway_ms` (52 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/paymentgateway/taxrule/createtaxrule`<br>`/api/paymentgateway/taxrule/edittaxrule`<br>`/api/paymentgateway/taxrule/gettaxrules` | `payment_gateway_ms/controller/taxRule/taxRuleRoutes.js:11` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| DELETE | `/api/paymentgateway/taxrule/deletetaxrule/:taxRuleId` | `payment_gateway_ms/controller/taxRule/taxRuleRoutes.js:13` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| GET | `/api/paymentgateway/taxrule/gettaxrule/:taxRuleId` | `payment_gateway_ms/controller/taxRule/taxRuleRoutes.js:14` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/paymentgateway/gateway/creategateway`<br>`/api/paymentgateway/gateway/editgateway` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:55` | isLoggedIn, subdomainCheck, isPaymentDistributionDeveloper |
| POST | `/api/paymentgateway/gateway/deletegateway` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:57` | isLoggedIn, subdomainCheck, isPaymentDistributionAdmin |
| POST | `/api/paymentgateway/gateway/getgateways`<br>`/api/paymentgateway/gateway/getgateway` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:58` | isLoggedIn, subdomainCheck, hasPaymentDistributionReadAccess |
| POST | `/api/paymentgateway/distribution/createdistributionaccountrequest`<br>`/api/paymentgateway/distribution/deletedistributionaccountrequest`<br>`/api/paymentgateway/distribution/deletepaymentaccount`<br>`/api/paymentgateway/distribution/inhouz/getdistributionaccounts`<br>`/api/paymentgateway/distribution/inhouz/getdistributionaccount`<br>`/api/paymentgateway/distribution/inhouz/getdistributionaccountrequests`<br>`/api/paymentgateway/distribution/getpaymentdistributions`<br>`/api/paymentgateway/distribution/getpaymentdistributionTopups`<br>`/api/paymentgateway/distribution/getpaymentdistribution`<br>`/api/paymentgateway/distribution/inhouz/getdistributionpayouts`<br>`/api/paymentgateway/distribution/approval/approvalhandler`<br>`/api/paymentgateway/distribution/approval/getapprovalrequests`<br>`/api/paymentgateway/distribution/approval/getapprovalrequest`<br>`/api/paymentgateway/distribution/approval/getapprovalbreakdown`<br>`/api/paymentgateway/distribution/inhouz/getpendingpayouts`<br>`/api/paymentgateway/distribution/fileupload`<br>`/api/paymentgateway/distribution/getpaymentdistributionfiles`<br>`/api/paymentgateway/distribution/getpaymentdistributionfile` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:60` | isLoggedIn |
| POST | `/api/paymentgateway/distribution/requestportal/passwordrequest`<br>`/api/paymentgateway/distribution/requestportal/portallogin`<br>`/api/paymentgateway/distribution/requestportal/portallogout`<br>`/api/paymentgateway/distribution/requestportal/getportaluser`<br>`/api/paymentgateway/distribution/createaccount`<br>`/api/paymentgateway/distribution/createonboardinglink`<br>`/api/paymentgateway/distribution/validateaccount`<br>`/api/paymentgateway/distribution/inhouz/getdistributionaccountrequest`<br>`/api/paymentgateway/distribution/distribute/serverrun` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:62` | — |
| POST | `/api/paymentgateway/distribution/deletesubscriptionaccount`<br>`/api/paymentgateway/distribution/subscription/getdistributionaccounts`<br>`/api/paymentgateway/distribution/subscription/getdistributionaccount`<br>`/api/paymentgateway/distribution/subscription/getdashboardlink`<br>`/api/paymentgateway/distribution/subscription/getdistributionpayouts` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:67` | subscriptionCheckLogin |
| POST | `/api/paymentgateway/distribution/distribute/run` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:78` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, isLoggedIn |
| POST | `/api/paymentgateway/distribution/customerportal/getdistributionpayouts` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:85` | checkPortalLogin |
| POST | `/api/paymentgateway/distribution/approval/updateworkflow` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:86` | isLoggedIn, isPaymentDistributionAdmin |
| GET | `/api/paymentgateway/distribution/approval/getglobalworkflow` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:88` | isLoggedIn, isPaymentDistributionAdmin |
| POST | `/api/paymentgateway/distribution/category/create`<br>`/api/paymentgateway/distribution/category/edit`<br>`/api/paymentgateway/distribution/category/delete` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:96` | isLoggedIn, isPaymentDistributionDeveloper |
| POST | `/api/paymentgateway/distribution/category/getcategory`<br>`/api/paymentgateway/distribution/category/getcategories`<br>`/api/paymentgateway/distribution/category/checknameavailability` | `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:99` | isLoggedIn, hasPaymentDistributionReadAccess |

#### `payment_link_ms` (31 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/paymentlink/create` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:46` | isLoggedIn, canWritePaymentLink |
| POST | `/api/paymentlink/servercreatepaymentlink` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:47` | serverCreatePaymentLink |
| POST | `/api/paymentlink/edit` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:48` | isLoggedIn, canWritePaymentLink |
| DELETE | `/api/paymentlink/delete/:paymentLinkId` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:49` | isLoggedIn, canDeletePaymentLink |
| POST | `/api/paymentlink/serverdeletepaymentlinks` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:50` | — |
| POST | `/api/paymentlink/generateslug` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:51` | — |
| POST | `/api/paymentlink/slugavailabilitycheck` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:52` | isLoggedIn |
| POST | `/api/paymentlink/fieldavailabilitycheck` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:53` | isLoggedIn |
| GET | `/api/paymentlink/getpaymentlink/:paymentLinkId` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:54` | isLoggedIn, canReadPaymentLink |
| POST | `/api/paymentlink/getpaymentlinks` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:55` | isLoggedIn, canReadPaymentLink |
| POST | `/api/paymentlink/requestpasswordchange` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:56` | isLoggedIn, canWritePaymentLink |
| POST | `/api/paymentlink/passwordlogin` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:57` | — |
| POST | `/api/paymentlink/deploy` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:58` | isLoggedIn, canWritePaymentLink |
| POST | `/api/paymentlink/serverdeploy` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:59` | serverDeployPaymentLink |
| POST | `/api/paymentlink/questionnaireauth` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:60` | — |
| POST | `/api/paymentlink/requestuserpassword` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:61` | — |
| POST | `/api/paymentlink/getlinkdata` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:62` | getPaymentLinkData, countryWhitelist, countryBlocklist, ipWhitelist, ipBlockPolicy |
| POST | `/api/paymentlink/getdocumentverificationclientsecret` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:63` | — |
| POST | `/api/paymentlink/registerdocumentverification` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:64` | — |
| POST | `/api/paymentlink/documentverificationstatuscheck` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:65` | — |
| POST | `/api/paymentlink/documentverificationlogin` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:66` | — |
| POST | `/api/paymentlink/recordsplitpayment` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:67` | — |
| POST | `/api/paymentlink/markpaymentlinkasused` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:68` | — |
| POST | `/api/paymentlink/setactivestatus` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:69` | — |
| POST | `/api/paymentlink/getpaymentlinkmetadata` | `payment_link_ms/controller/payment/paymentLinkRoutes.js:70` | — |
| POST | `/api/paymentlink/design/create`<br>`/api/paymentlink/design/edit`<br>`/api/paymentlink/design/delete`<br>`/api/paymentlink/design/getdesign`<br>`/api/paymentlink/design/getdesigns` | `payment_link_ms/controller/payment/paymentPageRoutes.js:10` | isLoggedIn |
| GET | `/api/paymentlink/design/getdefaultdesign` | `payment_link_ms/controller/payment/paymentPageRoutes.js:15` | isLoggedIn |

#### `inhouz_pay_ms` (38 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzpay/stripe/getpublickey`<br>`/api/inhouzpay/stripe/createpaymentintent`<br>`/api/inhouzpay/stripe/createsetupintent`<br>`/api/inhouzpay/stripe/finalizestripeuipayment`<br>`/api/inhouzpay/stripe/cancelpayment` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:42` | — |
| POST | `/api/inhouzpay/tax/gettaxamount` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:45` | — |
| POST | `/api/inhouzpay/payment/deactivateinhouzpayment` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:48` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, isPaymentAdmin |
| POST | `/api/inhouzpay/payment/markassuccess`<br>`/api/inhouzpay/payment/cachepaymentmetadata`<br>`/api/inhouzpay/payment/markrefundassuccess`<br>`/api/inhouzpay/payment/markrefundasfail`<br>`/api/inhouzpay/payment/serversubscriptionpayment`<br>`/api/inhouzpay/payment/paymentmethod/getpaymentmethods`<br>`/api/inhouzpay/payment/paymentmethod/changepaymentmethod`<br>`/api/inhouzpay/payment/paymentlink/initfixedflexpayment`<br>`/api/inhouzpay/payment/paymentlink/pay/fixedflexschedule`<br>`/api/inhouzpay/payment/paymentlink/initsubscriptionpayment`<br>`/api/inhouzpay/payment/paymentlink/pay/subscriptionpayment`<br>`/api/inhouzpay/payment/subscription/addsubscribers`<br>`/api/inhouzpay/payment/subscription/paymentsubscriberquery`<br>`/api/inhouzpay/payment/subscription/ondemand/web`<br>`/api/inhouzpay/payment/subscription/ondemand/server` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:49` | — |
| POST | `/api/inhouzpay/payment/getpayments` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:51` | isLoggedIn, subdomainCheck, isPaymentDeveloper |
| POST | `/api/inhouzpay/payment/getportalpayments`<br>`/api/inhouzpay/payment/paymentlink/pay/offscheduledfixedflex`<br>`/api/inhouzpay/payment/paymentlink/terminatesubscription`<br>`/api/inhouzpay/payment/subscription/getsubscribers`<br>`/api/inhouzpay/payment/subscription/getsubscriber`<br>`/api/inhouzpay/payment/subscription/editsubscriber`<br>`/api/inhouzpay/payment/subscription/cancelsubscriptions` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:52` | checkPortalLogin |
| POST | `/api/inhouzpay/payment/getsubscriptionrelatedpayments` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:53` | checkSubscriberLogin |
| GET | `/api/inhouzpay/payment/getpayment/:inhouzPaymentId` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:54` | isLoggedIn, subdomainCheck, isPaymentDeveloper |
| GET | `/api/inhouzpay/payment/getportalpayment/:inhouzPaymentId` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:55` | checkPortalLogin |
| GET | `/api/inhouzpay/payment/getsubscriptionrelatedpayment/:inhouzPaymentId` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:56` | checkSubscriberLogin |
| POST | `/api/inhouzpay/payment/refund` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:57` | isLoggedIn, subdomainCheck, isPaymentAdmin |
| POST | `/api/inhouzpay/payment/refundweb`<br>`/api/inhouzpay/payment/refundserver` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:58` | refundValidator |
| POST | `/api/inhouzpay/payment/subscription/findpaymentsubscribers` | `inhouz_pay_ms/controller/payment/paymentRoutes.js:72` | isLoggedIn |

#### `late_payment_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/latepayment/quickpay` | `late_payment_ms/controller/payment/paymentRoutes.js:10` | lightLoginCheck, subscriptionCheckLogin, isPaymentAdmin, isSubscriptionAdmin |

#### `payment_validation_ms` (4 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/paymentvalidator/validate` | `payment_validation_ms/controller/paymentController/paymentRoutes.js:7` | — |
| POST | `/api/paymentvalidator/refundvalidator` | `payment_validation_ms/controller/paymentController/paymentRoutes.js:8` | — |
| POST | `/api/paymentvalidator/setupintentstatusvalidation` | `payment_validation_ms/controller/paymentController/paymentRoutes.js:9` | — |
| POST | `/api/paymentvalidator/topupvalidation` | `payment_validation_ms/controller/paymentController/paymentRoutes.js:10` | — |

#### `inhouz_pay_metrics_ms` (11 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzpaymetrics/gettopsection` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:16` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/recurringrevenuemetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:17` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/recurringrevenuetimelinemetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:18` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/paymenttimelinemetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:19` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/paymentpiemetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:20` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/basesessionmetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:21` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/avgsessionduration` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:22` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/sessiontimelinemetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:23` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/sessionpiemetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:24` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/conversionpiemetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:25` | checkLogin, isPaymentDeveloper |
| POST | `/api/inhouzpaymetrics/taxmetrics` | `inhouz_pay_metrics_ms/controller/metricsController/metricsRoutes.js:26` | checkLogin, isPaymentDeveloper |

#### `inhouz_pay_recurring_stats_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzpayrecurringstats/parsemrr` | `inhouz_pay_recurring_stats_ms/controller/paymentController/paymentRoutes.js:4` | — |

### 3.4 App builder and app runtime

#### `app_builder_ms` (43 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/appbuilder/createapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:55` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/cloneapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:56` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, checkServerLogin, isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/getapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:57` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, checkServerLogin, isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/getcompressedapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:58` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/encgetcompressedapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:59` | — |
| POST | `/api/appbuilder/editapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:60` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/commitapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:61` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/getappcommits` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:62` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/setcommitversion` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:63` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/setrebasefallback` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:64` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/getrebasefallbacks` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:65` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/undeploy` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:66` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/getapps` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:67` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/getappsbyname` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:68` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/activatecustomdomain` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:69` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/deactivatecustomdomain` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:70` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/cloudflare/purgedomaincache` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:71` | — |
| POST | `/api/appbuilder/deleteapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:72` | isLoggedIn, subdomainCheck, isAllowedDeveloper, hasDeletePermission |
| POST | `/api/appbuilder/serverdeleteapp` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:73` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, checkServerLogin, isLoggedIn |
| POST | `/api/appbuilder/logexternalusereditoraccess` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:74` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/getuniqueid` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:76` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/fieldnamecheck` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:77` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/appfolder/create`<br>`/api/appbuilder/appfolder/edit` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:78` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| DELETE | `/api/appbuilder/appfolder/delete/:folderId` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:80` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| GET | `/api/appbuilder/appfolder/getfolder/:folderId` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:81` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/appfolder/getfolders`<br>`/api/appbuilder/appfolder/foldernamecheck` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:82` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/savedstyles/create`<br>`/api/appbuilder/savedstyles/edit` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:84` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| DELETE | `/api/appbuilder/savedstyles/delete/:appId/:styleId` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:86` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/savedstyles/getstyles`<br>`/api/appbuilder/savedstyles/namecheck` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:87` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/styleguide/create` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:89` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/styleguide/edit` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:90` | isLoggedIn, subdomainCheck, companyAccountCheck, isAllowedDeveloper |
| DELETE | `/api/appbuilder/styleguide/delete/:appId/:styleGuideId` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:91` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/styleguide/getstyleguide` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:92` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/appaccess/setpassword`<br>`/api/appbuilder/appaccess/changepassword`<br>`/api/appbuilder/appaccess/requestpasswordchange` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:93` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/elements/save` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:96` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/appbuilder/elements/delete`<br>`/api/appbuilder/elements/getsavedappelements` | `app_builder_ms/controller/appBuilder/appBuilderRoutes.js:97` | isLoggedIn, subdomainCheck, isAllowedDeveloper |

#### `view_builder_ms` (9 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/viewbuilder/build` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:20` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, serverUserLogin, isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/viewbuilder/buildclone` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:21` | — |
| POST | `/api/viewbuilder/getqueueddeployment` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:22` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/viewbuilder/buildapproval` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:23` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/viewbuilder/systemrebuild` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:24` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/viewbuilder/getbuildreports` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:25` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/viewbuilder/mergebuild` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:26` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/viewbuilder/generalsystemrebuild` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:27` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/viewbuilder/getappbuild` | `view_builder_ms/controller/buildRoutes/buildRoutes.js:28` | — |

#### `app_version_manager_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/appversionmanager/inhouzapprebase` | `app_version_manager_ms/controller/appVersionManager/appRoutes.js:4` | — |

#### `appviewer_log_ms` (5 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/appviewerlog/daulog` | `appviewer_log_ms/controller/appVisitController/appVisitRoutes.js:8` | — |
| POST | `/api/appviewerlog/routelog` | `appviewer_log_ms/controller/appVisitController/appVisitRoutes.js:9` | — |
| POST | `/api/appviewerlog/setappmetrics` | `appviewer_log_ms/controller/appVisitController/appVisitRoutes.js:10` | — |
| POST | `/api/appviewerlog/setinhouzpaymetrics` | `appviewer_log_ms/controller/appVisitController/appVisitRoutes.js:11` | — |
| POST | `/api/appviewerlog/setinhouzsignmetrics` | `appviewer_log_ms/controller/appVisitController/appVisitRoutes.js:12` | — |

#### `appviewer_password_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/appviewerpassword/validatepassword` | `appviewer_password_ms/controller/password/passwordRoutes.js:4` | — |

#### `inhouzio_app_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `*` | `inhouzio_app_ms/server.js:31` | — |

### 3.5 Functions, APIs and data tooling

#### `functions_ms` (16 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/secret/create` | `functions_ms/controller/secretKeys/secretKeyRoutes.js:12` | isLoggedIn, companyAccountCheck, subdomainCheck |
| POST | `/api/secret/edit` | `functions_ms/controller/secretKeys/secretKeyRoutes.js:13` | isLoggedIn, companyAccountCheck, subdomainCheck |
| POST | `/api/secret/getsecrets` | `functions_ms/controller/secretKeys/secretKeyRoutes.js:14` | isLoggedIn, subdomainCheck |
| POST | `/api/secret/getsecret` | `functions_ms/controller/secretKeys/secretKeyRoutes.js:15` | lightLoginCheck |
| POST | `/api/secret/getserversecret` | `functions_ms/controller/secretKeys/secretKeyRoutes.js:16` | serverValidator |
| POST | `/api/function/create` | `functions_ms/controller/function/functionRoutes.js:21` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/function/edit` | `functions_ms/controller/function/functionRoutes.js:22` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper, editableByNonAuthor |
| POST | `/api/function/deletefunction` | `functions_ms/controller/function/functionRoutes.js:23` | isLoggedIn, subdomainCheck, isAllowedDeveloper |
| POST | `/api/function/getfunctions` | `functions_ms/controller/function/functionRoutes.js:24` | isLoggedIn, subdomainCheck |
| POST | `/api/function/getfunction` | `functions_ms/controller/function/functionRoutes.js:25` | lightLoginCheck |
| POST | `/api/function/setfunctionversion` | `functions_ms/controller/function/functionRoutes.js:26` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/function/getFunctionVersions` | `functions_ms/controller/function/functionRoutes.js:27` | isLoggedIn, subdomainCheck |
| POST | `/api/function/deploy` | `functions_ms/controller/function/functionRoutes.js:28` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/function/registeroperation` | `functions_ms/controller/function/functionRoutes.js:29` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/function/migrateappfunctions` | `functions_ms/controller/function/functionRoutes.js:30` | isLoggedIn, companyAccountCheck, subdomainCheck, isAllowedDeveloper |
| POST | `/api/function/migrateapifunctions` | `functions_ms/controller/function/functionRoutes.js:31` | isLoggedIn, companyAccountCheck, subdomainCheck, isApiDeveloper |

#### `flex_api_ms` (16 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/flexapi/create` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:26` | isLoggedIn, companyAccountCheck, subdomainCheck, isApiDeveloper |
| POST | `/api/flexapi/edit` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:27` | isLoggedIn, companyAccountCheck, subdomainCheck, isApiDeveloper |
| POST | `/api/flexapi/getflexapis` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:28` | lightLoginCheck, subdomainValidator |
| POST | `/api/flexapi/getflexapi` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:29` | lightLoginCheck, subdomainValidator |
| POST | `/api/flexapi/delete` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:30` | isLoggedIn, subdomainCheck, isApiDeveloper, hasDeletePermission |
| POST | `/api/flexapi/deploy` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:31` | isLoggedIn, companyAccountCheck, subdomainCheck, isApiDeveloper |
| POST | `/api/flexapi/undeploy/endpoint`<br>`/api/flexapi/undeploy/environment` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:32` | isLoggedIn, subdomainCheck, isApiDeveloper |
| POST | `/api/flexapi/rebuildendpoints` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:34` | isLoggedIn, companyAccountCheck |
| POST | `/api/flexapi/setflexapiversion` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:35` | isLoggedIn, companyAccountCheck, subdomainCheck, isApiDeveloper |
| POST | `/api/flexapi/getapitracker` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:36` | isLoggedIn, subdomainCheck |
| POST | `/api/flexapi/mergedeployments` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:37` | isLoggedIn, companyAccountCheck, subdomainCheck |
| POST | `/api/flexapi/documentationlist` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:38` | lightLoginCheck, subdomainValidator |
| POST | `/api/flexapi/documentation` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:39` | lightLoginCheck, subdomainValidator |
| POST | `/api/flexapi/getdynamicseoapis` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:40` | — |
| POST | `/api/flexapi/getdeployedendpoints` | `flex_api_ms/controller/flexApiController/flexApiRoutes.js:41` | isLoggedIn, subdomainCheck |

#### `flex_module_collection_ms` (23 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/database/create` | `flex_module_collection_ms/controller/database/databaseRoutes.js:14` | isLoggedIn, companyAccountCheck, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/database/edit` | `flex_module_collection_ms/controller/database/databaseRoutes.js:15` | isLoggedIn, companyAccountCheck, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/database/changepassword` | `flex_module_collection_ms/controller/database/databaseRoutes.js:16` | isLoggedIn, companyAccountCheck, subdomainCheck, isDbAdminDeveloper |
| DELETE | `/api/database/delete/:id` | `flex_module_collection_ms/controller/database/databaseRoutes.js:17` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/database/getall` | `flex_module_collection_ms/controller/database/databaseRoutes.js:18` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/database/getdatabase` | `flex_module_collection_ms/controller/database/databaseRoutes.js:19` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/filestorageservice/create` | `flex_module_collection_ms/controller/database/fileStorageServiceRoutes.js:13` | isLoggedIn, companyAccountCheck, subdomainCheck, isDbAdmin |
| POST | `/api/filestorageservice/edit` | `flex_module_collection_ms/controller/database/fileStorageServiceRoutes.js:14` | isLoggedIn, companyAccountCheck, subdomainCheck, isDbAdmin |
| POST | `/api/filestorageservice/getservices` | `flex_module_collection_ms/controller/database/fileStorageServiceRoutes.js:15` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| GET | `/api/filestorageservice/getservice/:fileStorageServiceId` | `flex_module_collection_ms/controller/database/fileStorageServiceRoutes.js:16` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| DELETE | `/api/filestorageservice/deleteservice/:fileStorageServiceId` | `flex_module_collection_ms/controller/database/fileStorageServiceRoutes.js:17` | isLoggedIn, subdomainCheck, isDbAdmin |
| POST | `/api/flexcollection/create` | `flex_module_collection_ms/controller/collection/collectionRoutes.js:16` | isLoggedIn, companyAccountCheck, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/flexcollection/edit` | `flex_module_collection_ms/controller/collection/collectionRoutes.js:17` | isLoggedIn, companyAccountCheck, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/flexcollection/get/getCollections` | `flex_module_collection_ms/controller/collection/collectionRoutes.js:18` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| GET | `/api/flexcollection/get/:collectionId/:prod` | `flex_module_collection_ms/controller/collection/collectionRoutes.js:19` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/flexcollection/deploy` | `flex_module_collection_ms/controller/collection/collectionRoutes.js:20` | isLoggedIn, companyAccountCheck, subdomainCheck, collectionValidator, isDbAdminDeveloper |
| POST | `/api/flexcollection/collectionexistscheck` | `flex_module_collection_ms/controller/collection/collectionRoutes.js:21` | isLoggedIn, subdomainCheck, isDbAdminDeveloper |
| POST | `/api/flexmodule/create` | `flex_module_collection_ms/controller/module/moduleRoutes.js:14` | isLoggedIn, subdomainCheck |
| POST | `/api/flexmodule/editmodulecollections` | `flex_module_collection_ms/controller/module/moduleRoutes.js:15` | isLoggedIn, subdomainCheck, basicModuleValidation |
| POST | `/api/flexmodule/editmodule` | `flex_module_collection_ms/controller/module/moduleRoutes.js:16` | isLoggedIn, subdomainCheck, basicModuleValidation |
| POST | `/api/flexmodule/getmodule` | `flex_module_collection_ms/controller/module/moduleRoutes.js:17` | isLoggedIn, subdomainCheck |
| POST | `/api/flexmodule/deploymodule` | `flex_module_collection_ms/controller/module/moduleRoutes.js:18` | isLoggedIn, subdomainCheck, basicModuleValidation |
| POST | `/api/flexmodule/moduleexistscheck` | `flex_module_collection_ms/controller/module/moduleRoutes.js:19` | isLoggedIn, subdomainCheck |

#### `database_execution_ms` (3 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/remoteexecution/webtransaction` | `database_execution_ms/controller/executionRoutes.js:11` | partialDecryptTransaction, getDatabaseData |
| POST | `/api/remoteexecution/servertransaction` | `database_execution_ms/controller/executionRoutes.js:12` | serverValidator, partialDecryptTransaction, getDatabaseData |
| POST | `/api/remoteexecution/testconnection` | `database_execution_ms/controller/executionRoutes.js:13` | isLoggedIn, companyAccountCheck, decryptTransaction |

#### `api_service_ms` (5 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `*` | `api_service_ms/controller/apiService/apiRoute.js:12` | getCachedApi, getApi, httpPolicy, ipBlockPolicy, ipWhitelist, hostWhitelist, hostBlocklist, apiKeyValidation |
| POST | `*` | `api_service_ms/controller/apiService/apiRoute.js:13` | getCachedApi, getApi, httpPolicy, ipBlockPolicy, ipWhitelist, hostWhitelist, hostBlocklist, apiKeyValidation |
| PUT | `*` | `api_service_ms/controller/apiService/apiRoute.js:14` | getCachedApi, getApi, httpPolicy, ipBlockPolicy, ipWhitelist, hostWhitelist, hostBlocklist, apiKeyValidation |
| PATCH | `*` | `api_service_ms/controller/apiService/apiRoute.js:15` | getCachedApi, getApi, httpPolicy, ipBlockPolicy, ipWhitelist, hostWhitelist, hostBlocklist, apiKeyValidation |
| DELETE | `*` | `api_service_ms/controller/apiService/apiRoute.js:16` | getCachedApi, getApi, httpPolicy, ipBlockPolicy, ipWhitelist, hostWhitelist, hostBlocklist, apiKeyValidation |

#### `function_parser_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/functionparser/parsefunction` | `function_parser_ms/lib/index.js:87` | — |

#### `module_transfer_ms` (9 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/moduletransfer/createpackage` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:16` | isLoggedIn, hasWriteAccess |
| POST | `/api/moduletransfer/editpackage` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:17` | isLoggedIn, hasWriteAccess |
| POST | `/api/moduletransfer/deletepackage` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:18` | isLoggedIn, hasWriteAccess |
| POST | `/api/moduletransfer/getpackage` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:19` | isLoggedIn, hasReadAccess |
| POST | `/api/moduletransfer/getpackages` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:20` | isLoggedIn, hasReadAccess |
| POST | `/api/moduletransfer/acceptpackage` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:21` | isLoggedIn, hasAdminAccess |
| POST | `/api/moduletransfer/gettransferlogs` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:22` | isLoggedIn, hasReadAccess |
| POST | `/api/moduletransfer/importenvironmentvariables` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:23` | isLoggedIn, hasReadAccess |
| POST | `/api/moduletransfer/checktransferprogress` | `module_transfer_ms/controller/moduleTransfer/moduleTransferRoutes.js:24` | isLoggedIn, hasReadAccess |

#### `module_transfer_parser_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/moduletransferparser/run` | `module_transfer_parser_ms/controller/moduleTransfer/moduleTransferRoutes.js:6` | isLoggedIn, hasRunAccess |

### 3.6 Scheduling, automation and parsers

#### `scheduled_task_ms` (9 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/scheduledtask/create` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:19` | lightLoginCheck |
| POST | `/api/scheduledtask/servercreate` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:20` | serverValidator |
| POST | `/api/scheduledtask/deactivate` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:21` | — |
| POST | `/api/scheduledtask/run` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:22` | isLoggedIn |
| POST | `/api/scheduledtask/edit` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:23` | isLoggedIn, companyAccountCheck, subdomainCheck |
| POST | `/api/scheduledtask/rebuildscheduledtasks` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:24` | isLoggedIn, companyAccountCheck |
| POST | `/api/scheduledtask/getscheduledtasks` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:27` | isLoggedIn, subdomainCheck |
| POST | `/api/scheduledtask/getscheduledtasklogs` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:28` | isLoggedIn, subdomainCheck |
| POST | `/api/scheduledtask/getscheduledtask` | `scheduled_task_ms/controller/scheduledTask/scheduledTaskRoutes.js:29` | isLoggedIn, subdomainCheck |

#### `scheduled_task_parser_ms` (2 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/scheduledtaskparser/parse` | `scheduled_task_parser_ms/controller/scheduledTask/taskRoutes.js:5` | — |
| POST | `/api/scheduledtaskparser/resolve` | `scheduled_task_parser_ms/controller/scheduledTask/taskRoutes.js:6` | — |

#### `scheduled_task_function_parser_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/scheduledtaskfunctionparser/parsefunction` | `scheduled_task_function_parser_ms/lib/index.js:89` | — |

#### `general_task_parser_ms` (7 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/generaltaskparser/paymentmethodexpirationnotice` | `general_task_parser_ms/controller/generalRoutes/generalRoutes.js:10` | — |
| POST | `/api/generaltaskparser/jwtsign` | `general_task_parser_ms/controller/generalRoutes/generalRoutes.js:11` | — |
| POST | `/api/generaltaskparser/jwtverify` | `general_task_parser_ms/controller/generalRoutes/generalRoutes.js:12` | — |
| POST | `/api/generaltaskparser/jwktopem` | `general_task_parser_ms/controller/generalRoutes/generalRoutes.js:13` | — |
| POST | `/api/generaltaskparser/getwebsocketconnectionkey` | `general_task_parser_ms/controller/generalRoutes/generalRoutes.js:14` | — |
| POST | `/api/generaltaskparser/refreshwebsocketclientkey` | `general_task_parser_ms/controller/generalRoutes/generalRoutes.js:15` | — |
| POST | `/api/generaltaskparser/validaterecaptchav3token` | `general_task_parser_ms/controller/generalRoutes/generalRoutes.js:16` | — |

#### `document_generation_parser_ms` (2 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/documentgeneratorparser/inhouzsign` | `document_generation_parser_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:5` | — |
| POST | `/api/documentgeneratorparser/pdffunction` | `document_generation_parser_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:6` | — |

#### `remote_network_request_ms` (2 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/remotenetworkrequest/parse` | `remote_network_request_ms/server.js:86` | — |
| GET | `/api/helloworld` | `remote_network_request_ms/controller/helloWorld/helloRoutes.js:4` | — |

#### `subscriber_data_function_ms` (4 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/subscriberdatafunction/getsubscribers` | `subscriber_data_function_ms/controller/subscriber/subscriberDataRoutes.js:7` | — |
| POST | `/api/subscriberdatafunction/getsubscribercount` | `subscriber_data_function_ms/controller/subscriber/subscriberDataRoutes.js:8` | — |
| POST | `/api/subscriberdatafunction/querysubscribedtenant` | `subscriber_data_function_ms/controller/subscriber/subscriberDataRoutes.js:9` | — |
| POST | `/api/subscriberdatafunction/updatesubscriberdata` | `subscriber_data_function_ms/controller/subscriber/subscriberDataRoutes.js:10` | — |

#### `push_notification_parser_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/pushnotificationparser/sendpushnotification` | `push_notification_parser_ms/controller/notification/notificationRoutes.js:4` | — |

#### `subscription_migration_scheduler_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `/api/helloworld` | `subscription_migration_scheduler_ms/controller/helloWorld/helloRoutes.js:4` | — |

#### `subscription_renewal_scheduler_ms` (1 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `/api/helloworld` | `subscription_renewal_scheduler_ms/controller/helloWorld/helloRoutes.js:4` | — |

### 3.7 Documents, signing and media

#### `inhouz_sign_ms` (45 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzsign/approvalworkflow/update`<br>`/api/inhouzsign/approvalworkflow/getapprovalrequests`<br>`/api/inhouzsign/approvalworkflow/getapprovalrequest`<br>`/api/inhouzsign/approvalworkflow/getapprovalbreakdown` | `inhouz_sign_ms/controller/inhouzSign/approvalRoutes.js:9` | isLoggedIn |
| GET | `/api/inhouzsign/approvalworkflow/getglobalworkflow` | `inhouz_sign_ms/controller/inhouzSign/approvalRoutes.js:10` | isLoggedIn |
| POST | `/api/inhouzsign/document/create`<br>`/api/inhouzsign/document/edit`<br>`/api/inhouzsign/document/workflowapproval`<br>`/api/inhouzsign/document/getgeneratedinhouzsignfile`<br>`/api/inhouzsign/document/getidentityverificationlogs`<br>`/api/inhouzsign/document/attachment/getattachment`<br>`/api/inhouzsign/document/attachment/getattachments`<br>`/api/inhouzsign/document/initinhouzsignpayment` | `inhouz_sign_ms/controller/inhouzSign/contractRoutes.js:46` | isLoggedIn |
| POST | `/api/inhouzsign/document/createfromtemplate`<br>`/api/inhouzsign/document/initcreatefromtemplate`<br>`/api/inhouzsign/document/getdocument`<br>`/api/inhouzsign/document/generatesignerurl`<br>`/api/inhouzsign/document/getdocumentfile`<br>`/api/inhouzsign/document/getdocuments`<br>`/api/inhouzsign/document/canceldocument`<br>`/api/inhouzsign/document/markascomplete` | `inhouz_sign_ms/controller/inhouzSign/contractRoutes.js:47` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, isLoggedIn |
| POST | `/api/inhouzsign/document/delete`<br>`/api/inhouzsign/document/senddocument`<br>`/api/inhouzsign/document/distribute` | `inhouz_sign_ms/controller/inhouzSign/contractRoutes.js:50` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, checkServerLogin, isLoggedIn |
| POST | `/api/inhouzsign/document/getportaldocumentfile`<br>`/api/inhouzsign/document/getportaldocuments` | `inhouz_sign_ms/controller/inhouzSign/contractRoutes.js:54` | checkPortalLogin |
| POST | `/api/inhouzsign/document/getencrypteddocument` | `inhouz_sign_ms/controller/inhouzSign/contractRoutes.js:55` | getEncryptedDocument, countryWhitelist, countryBlocklist, ipWhitelist, ipBlockPolicy |
| POST | `/api/inhouzsign/document/getcontractbuild`<br>`/api/inhouzsign/document/expiredocument`<br>`/api/inhouzsign/document/sendreminder`<br>`/api/inhouzsign/document/getauditlogs`<br>`/api/inhouzsign/document/requestpassword`<br>`/api/inhouzsign/document/signdocument`<br>`/api/inhouzsign/document/declinedocument`<br>`/api/inhouzsign/document/uploadgenerateddocument`<br>`/api/inhouzsign/document/startdocumentgeneration`<br>`/api/inhouzsign/document/testfilestorage`<br>`/api/inhouzsign/document/postpaymentaction` | `inhouz_sign_ms/controller/inhouzSign/contractRoutes.js:56` | — |
| POST | `/api/inhouzsign/template/create`<br>`/api/inhouzsign/template/createfromclone`<br>`/api/inhouzsign/template/edit` | `inhouz_sign_ms/controller/inhouzSign/templateRoutes.js:13` | isLoggedIn, hasGenericWriteAccess |
| DELETE | `/api/inhouzsign/template/delete/:templateId` | `inhouz_sign_ms/controller/inhouzSign/templateRoutes.js:16` | isLoggedIn, hasGenericWriteAccess |
| GET | `/api/inhouzsign/template/gettemplate/:templateId` | `inhouz_sign_ms/controller/inhouzSign/templateRoutes.js:17` | isLoggedIn, hasGenericReadAccess |
| POST | `/api/inhouzsign/template/gettemplates` | `inhouz_sign_ms/controller/inhouzSign/templateRoutes.js:18` | isLoggedIn, hasGenericReadAccess |
| POST | `/api/inhouzsign/template/fieldavailabilitycheck` | `inhouz_sign_ms/controller/inhouzSign/templateRoutes.js:19` | isLoggedIn |

#### `inhouz_sign_metrics_ms` (6 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `/api/helloworld` | `inhouz_sign_metrics_ms/controller/helloWorld/helloRoutes.js:4` | — |
| POST | `/api/inhouzsignmetrics/gettopsection` | `inhouz_sign_metrics_ms/controller/metricsController/metricsRoutes.js:9` | checkLogin |
| POST | `/api/inhouzsignmetrics/documenttimelinemetrics` | `inhouz_sign_metrics_ms/controller/metricsController/metricsRoutes.js:10` | checkLogin |
| POST | `/api/inhouzsignmetrics/basesessionmetrics` | `inhouz_sign_metrics_ms/controller/metricsController/metricsRoutes.js:11` | checkLogin |
| POST | `/api/inhouzsignmetrics/basesessionpiemetrics` | `inhouz_sign_metrics_ms/controller/metricsController/metricsRoutes.js:12` | checkLogin |
| POST | `/api/inhouzsignmetrics/sendermetrics` | `inhouz_sign_metrics_ms/controller/metricsController/metricsRoutes.js:13` | checkLogin |

#### `pdf_generator_ms` (14 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/pdfgenerator/template/create`<br>`/api/pdfgenerator/template/createfromclone`<br>`/api/pdfgenerator/template/edit` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:20` | isLoggedIn, hasGenericWriteAccess |
| DELETE | `/api/pdfgenerator/template/delete/:templateId` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:23` | isLoggedIn, hasGenericWriteAccess |
| GET | `/api/pdfgenerator/template/gettemplate/:templateId` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:24` | isLoggedIn, hasGenericReadAccess |
| POST | `/api/pdfgenerator/template/gettemplates` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:25` | isLoggedIn, hasGenericReadAccess |
| POST | `/api/pdfgenerator/template/fieldavailabilitycheck` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:26` | isLoggedIn |
| POST | `/api/pdfgenerator/document/getpdfgenerationpackage`<br>`/api/pdfgenerator/document/uploadpdffile`<br>`/api/pdfgenerator/document/startdocumentgeneration` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:27` | — |
| POST | `/api/pdfgenerator/document/getgenerateddocuments`<br>`/api/pdfgenerator/document/getgenerateddocument` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:30` | isLoggedIn, hasGenericReadAccess |
| POST | `/api/pdfgenerator/metrics/topsection`<br>`/api/pdfgenerator/metrics/timelinemetrics` | `pdf_generator_ms/controller/pdfGenerator/pdfGeneratorRoutes.js:32` | isLoggedIn, hasGenericReadAccess |

#### `multimedia_ms` (6 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/multimedia/upload` | `multimedia_ms/controller/multimediaRoutes.js:15` | — |
| POST | `/api/multimedia/getfilefunction` | `multimedia_ms/controller/multimediaRoutes.js:16` | — |
| GET | `/api/multimedia/:encryptedKey/:fileKey` | `multimedia_ms/controller/multimediaRoutes.js:17` | — |
| POST | `/api/multimedia/deletefiles` | `multimedia_ms/controller/multimediaRoutes.js:18` | — |
| POST | `/api/multimedia/filesearch` | `multimedia_ms/controller/multimediaRoutes.js:19` | isLoggedIn, companyAccountCheck, subdomainCheck |
| POST | `/api/multimedia/getspeedtestdata` | `multimedia_ms/controller/multimediaRoutes.js:20` | — |

#### `image_proxy_ms` (5 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `/api/imageproxy/getimage` | `image_proxy_ms/controller/imageRoutes/imageRoutes.js:6` | — |
| GET | `/api/imageproxy/getimage/:imageKey` | `image_proxy_ms/controller/imageRoutes/imageRoutes.js:7` | — |
| GET | `/api/imageproxy/getstaticimage/:staticFileId` | `image_proxy_ms/controller/imageRoutes/imageRoutes.js:8` | — |
| GET | `/api/imageproxy/getstaticemailimage/:staticFileId` | `image_proxy_ms/controller/imageRoutes/imageRoutes.js:9` | — |
| GET | `/api/imageproxy/getinhouzsignfile/:staticFileId` | `image_proxy_ms/controller/imageRoutes/imageRoutes.js:10` | — |

#### `inhouz_file_upload_ms` (4 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzfileupload/userprofile` | `inhouz_file_upload_ms/controller/uploadRoutes/uploadRoutes.js:7` | isLoggedIn |
| POST | `/api/inhouzfileupload/inhouzapp` | `inhouz_file_upload_ms/controller/uploadRoutes/uploadRoutes.js:8` | isLoggedIn |
| POST | `/api/inhouzfileupload/subscriptionservice` | `inhouz_file_upload_ms/controller/uploadRoutes/uploadRoutes.js:9` | isLoggedIn, isSubscriptionDeveloper |
| POST | `/api/inhouzfileupload/subscriberprofile` | `inhouz_file_upload_ms/controller/uploadRoutes/uploadRoutes.js:10` | isSubscriberLoggedIn |

#### `file_operations_ms` (5 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/fileoperations/adduserscsv` | `file_operations_ms/controller/fileOpsRoutes.js:18` | isLoggedIn, companyAccountCheck, subdomainCheck |
| POST | `/api/fileoperations/subcriptionusercsv` | `file_operations_ms/controller/fileOpsRoutes.js:20` | — |
| POST | `/api/fileoperations/pdftoimage` | `file_operations_ms/controller/fileOpsRoutes.js:21` | isLoggedIn |
| POST | `/api/fileoperations/csvtojson` | `file_operations_ms/controller/fileOpsRoutes.js:22` | decryptAndExtractCompanyId, csvToJsonPlans, subscriptionPlanValidation |
| POST | `/api/fileoperations/bulkproductupload` | `file_operations_ms/controller/fileOpsRoutes.js:23` | isLoggedIn, companyAccountCheck |

### 3.8 Commerce, projects and web components

#### `inhouz_commerce_ms` (17 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzcommerce/category/create`<br>`/api/inhouzcommerce/category/edit`<br>`/api/inhouzcommerce/category/checknameavailability`<br>`/api/inhouzcommerce/category/getcategories` | `inhouz_commerce_ms/controller/product/paymentCategoryRoutes.js:10` | isLoggedIn |
| DELETE | `/api/inhouzcommerce/category/delete/:productCategoryId` | `inhouz_commerce_ms/controller/product/paymentCategoryRoutes.js:12` | isLoggedIn |
| GET | `/api/inhouzcommerce/category/get/:productCategoryId` | `inhouz_commerce_ms/controller/product/paymentCategoryRoutes.js:14` | isLoggedIn |
| POST | `/api/inhouzcommerce/product/create`<br>`/api/inhouzcommerce/product/edit`<br>`/api/inhouzcommerce/product/checknameavailability`<br>`/api/inhouzcommerce/product/getproducts` | `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:14` | isLoggedIn |
| POST | `/api/inhouzcommerce/product/servercreate`<br>`/api/inhouzcommerce/product/getproductserverquery`<br>`/api/inhouzcommerce/product/markaspurchased`<br>`/api/inhouzcommerce/product/calculateproductprice` | `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:15` | — |
| DELETE | `/api/inhouzcommerce/product/delete/:productId` | `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:17` | isLoggedIn |
| GET | `/api/inhouzcommerce/product/get/:productId` | `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:19` | isLoggedIn |
| POST | `/api/inhouzcommerce/product/encryptedrequest/getproduct` | `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:20` | encryptedProductRequest |

#### `inhouz_project_ms` (15 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/inhouzproject/projectcategory/create`<br>`/api/inhouzproject/projectcategory/edit`<br>`/api/inhouzproject/projectcategory/getprojectcategory`<br>`/api/inhouzproject/projectcategory/getprojectcategories`<br>`/api/inhouzproject/projectcategory/delete`<br>`/api/inhouzproject/projectcategory/getstatuslist` | `inhouz_project_ms/controller/projectCategoryRoutes.js:11` | isLoggedIn, parseRequestBody |
| POST | `/api/inhouzproject/project/create`<br>`/api/inhouzproject/project/getproject`<br>`/api/inhouzproject/project/getprojects`<br>`/api/inhouzproject/project/changestatus`<br>`/api/inhouzproject/project/changeprojectstate`<br>`/api/inhouzproject/project/delete` | `inhouz_project_ms/controller/projectRoutes.js:17` | apiKeyValidation, clientEncryptedLogin, serverEncryptedLogin, isLoggedIn, parseRequestBody |
| POST | `/api/inhouzproject/project/edit` | `inhouz_project_ms/controller/projectRoutes.js:18` | clientEncryptedLogin, serverEncryptedLogin, isLoggedIn, parseRequestBody |
| POST | `/api/inhouzproject/project/changeowner` | `inhouz_project_ms/controller/projectRoutes.js:22` | apiKeyValidation, isLoggedIn, parseRequestBody |
| POST | `/api/inhouzproject/project/fieldavailabilitycheck` | `inhouz_project_ms/controller/projectRoutes.js:23` | isLoggedIn |

#### `website_resource_ms` (3 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| GET | `/api/websiteresource/getwebsiteresources/:companyId/:appId/:variationId/:environment` | `website_resource_ms/controller/webResourceRoutes/webResourceRoutes.js:6` | — |
| GET | `/api/websiteresource/getwebsitepageresources/:companyId/:appId/:slug?` | `website_resource_ms/controller/webResourceRoutes/webResourceRoutes.js:7` | — |
| GET | `/api/websiteresource/manifestjson/:appId` | `website_resource_ms/controller/webResourceRoutes/webResourceRoutes.js:8` | — |

#### `webcomponent_ms` (7 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/webcomponent/grantaccess` | `webcomponent_ms/controller/webComponent/webComponentRoutes.js:13` | isLoggedIn, companyAccountCheck, isSubscriptionAdmin |
| POST | `/api/webcomponent/revokeaccess` | `webcomponent_ms/controller/webComponent/webComponentRoutes.js:14` | isLoggedIn, isSubscriptionAdmin |
| POST | `/api/webcomponent/getaccesstracker` | `webcomponent_ms/controller/webComponent/webComponentRoutes.js:15` | isLoggedIn, isSubscriptionAdmin |
| GET | `/api/webcomponent/getmywebcomponents` | `webcomponent_ms/controller/webComponent/webComponentRoutes.js:16` | isLoggedIn |
| GET | `/api/webcomponent/getwebcomponent/:companyId/:appId/:environment/:lzutf8Encrypted` | `webcomponent_ms/controller/webComponent/webComponentRoutes.js:17` | — |
| GET | `/api/webcomponent/getdeployedwebcomponents` | `webcomponent_ms/controller/webComponent/webComponentRoutes.js:18` | isLoggedIn, companyAccountCheck |
| POST | `/api/webcomponent/updatewebcomponentconfig` | `webcomponent_ms/controller/webComponent/webComponentRoutes.js:19` | isLoggedIn, companyAccountCheck |

### 3.9 Platform metrics

#### `app_metrics_ms` (7 routes)

| Method | Path | file:line | Auth middleware |
|---|---|---|---|
| POST | `/api/appmetrics/gettopsection` | `app_metrics_ms/controller/metrics/metricsRoutes.js:15` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/appmetrics/getappvisitlist` | `app_metrics_ms/controller/metrics/metricsRoutes.js:16` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/appmetrics/getpiemetrics` | `app_metrics_ms/controller/metrics/metricsRoutes.js:17` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/appmetrics/getBasicApiMetrics` | `app_metrics_ms/controller/metrics/metricsRoutes.js:18` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/appmetrics/getaverageapitime` | `app_metrics_ms/controller/metrics/metricsRoutes.js:19` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/appmetrics/getapitraffic` | `app_metrics_ms/controller/metrics/metricsRoutes.js:20` | isLoggedIn, subdomainCheck, isAdmin |
| POST | `/api/appmetrics/getapiusagesummary` | `app_metrics_ms/controller/metrics/metricsRoutes.js:21` | isLoggedIn, subdomainCheck, isAdmin |

### 3.10 Units with no HTTP routes

These units register no `app.<method>` route. They run timers, queue consumers or socket work, or are deployment-only.

| Unit | Why it has no route |
|---|---|
| `account_termination_cron_ms` | cron worker; termination routes live in `account_termination_ms` |
| `app_viewer_ms` | static app viewer (ingress `/` → port 3000) |
| `appbuilder_multiplayer_ms` | socket service mounted at `/appbuildersocket` |
| `churn_tracker_ms` | scheduler |
| `data_scanner_ms` | scheduler |
| `document_scheduler_ms` | scheduler |
| `general_task_scheduler_ms` | scheduler |
| `inhouz_pay_scheduler_ms` | scheduler |
| `inhouz_subscription_renewal_scheduler_ms` | scheduler |
| `log_manager_ms` | log consumer |
| `payment_validation_scheduler_ms` | scheduler |
| `scheduled_launch_ms` | scheduler |
| `scheduled_task_scheduler_ms` | scheduler |

## 4. The internal envelope

Service-to-service and client-to-service calls that need an authenticated payload use an encrypted envelope with three fields:

```json
{ "encryptedPayload": "<ciphertext>", "expirationTimestamp": 1700000000000, "serverEncrypted": false }
```

`expirationTimestamp` is a millisecond epoch compared against `new Date().getTime()`. When the timestamp has passed, the payload is treated as absent and the request is rejected or passes through, depending on the middleware.

- `inhouz_pay_ms/middlewares/login/serverEncryptedLogin.js:22-26` — Cryptr decrypt, JSON parse, expiry check, then `payload`.
- `inhouz_pay_ms/middlewares/login/clientEncryptedLogin.js:20-24` — RSA decrypt, JSON parse, expiry check, then `payload`.
- `authentication_ms/middlewares/automation/resolveEncryptedAutomationPayload.js:11-35` — reads `encryptedPayload` and `serverEncrypted` from the body, decrypts with Cryptr when `serverEncrypted` is true, otherwise with the RSA helper, then checks `expirationTimestamp`.

The envelope is **not a shared library**. Each service reimplements it in `utils/cryptography/encryptDecrypt.js`, and the signatures differ:

- `payment_ms/utils/cryptography/encryptDecrypt.js:3` — `function(data, encrypt=false)`
- `inhouz_pay_ms/utils/cryptography/encryptDecrypt.js:3` — `function(data, encrypt=false, publicEncryt=false, publicDecrypt=false)`
- `account_termination_ms/utils/cryptography/encryptDecrypt.js:3` — `function(data, encrypt=false, publicEncryt=false)`

The helper is copied into 75 service repositories. Responses use the same idea under different names: `payment_link_ms` returns `{ encryptedResponse: <ciphertext> }` where the plaintext is `{ payload, expirationTimestamp }` (`payment_link_ms/services/paymentLink/initStripeIdVerification.js:147-158`; `payment_link_ms/services/paymentLink/questionnaireAuth.js:254-266`).

## 5. Error format

There is no single error contract. The fleet uses at least five shapes, and several of them return HTTP 200 for a failure.

| Shape | Example | HTTP status |
|---|---|---|
| `res.send({error:{message}})` | `payment_ms/middlewares/login/checkLogin.js:14-20` | **200** |
| `res.send({error:{message}})` (service layer) | `app_builder_ms/services/appBuilder/savedStyles/getAppStyles.js:23` | **200** |
| `res.send({error:{...error}})` | `multimedia_ms/services/multimedia/uploadFile.js:219` | **200** |
| `{success:false, ...}` returned from a service | `view_builder_ms/utils/builder/viewBuilder.js:137` | **200** when sent by the controller |
| `{success:false}` internal result | `inhouz_pay_ms/services/payment/subscriptionOnDemandPayment.js:261` | depends on caller |
| Socket `error:{success:false, message}` | `websocket_ms/server.js:98-104` | websocket event |
| `res.status(400|401|403|404|500).send({error:{message}})` | `payment_gateway_ms/services/paymentDistribution/getPortalUser.js:15,37,91` | 400/401/500 |
| `res.status(200).send({...})` success payload | `subscription_ms/services/subscriptionService/getSignupSubscriptionService.js:304` | 200 |

Samples across services:

- `authentication_ms` — unauthorized is `res.send({error:{message:'Not Authorized'}})` at `authentication_ms/middlewares/login/checkLogin.js:17`; internal failures use `{success:false}` at `authentication_ms/services/user/addUsers.js:215`.
- `payment_ms` — mixed. `res.send(response)` at `payment_ms/services/paymentMethod/getPaymentMethods.js:12`; an explicit `res.status(403).send(...)` at `payment_ms/services/paymentMethod/deletePaymentMethod.js:52`; most other failures are `res.send({error})`.
- `payment_gateway_ms` — the clearest status-code user: 400 at `payment_gateway_ms/services/paymentDistribution/getPortalUser.js:15`, 401 at `:37`, 500 at `:91`.
- `payment_link_ms` — encrypted success payloads with `res.status(200).send` at `payment_link_ms/services/paymentLink/questionnaireAuth.js:254`; catch blocks return 500.
- `view_builder_ms` — `{success:false}` from `view_builder_ms/utils/builder/viewBuilder.js:137`, while controllers also use 400/404/500 (`view_builder_ms/services/builder/getBuild.js:18,40,89`).
- `inhouz_pay_ms` — `{success:false}` from `inhouz_pay_ms/services/payment/subscriptionOnDemandPayment.js:261`.
- `websocket_ms` — socket error `{error:{success:false, message}}` at `websocket_ms/server.js:98`.

The recurring finding: **authorization failures are HTTP 200.** Every `checkLogin` copy returns `res.send({error:{message:'Not Authorized'}})` without a status code, so a client that branches on HTTP status treats a rejected request as success. `checkLogin` is copied into 70 middleware files.

## 6. Known contract defects

### 6.1 `/healthz` is probed but never registered

71 services ship a `healthcheck.js` that requests `/healthz` and exits non-zero unless it gets HTTP 200 (e.g. `payment_ms/healthcheck.js:7`, `authentication_ms/healthcheck.js:7`). No `server.js` and no controller registers a `/healthz` route: a search for `healthz` across all `apps/*/**/*.js` returns only the `healthcheck.js` files. Every container healthcheck therefore depends on a route that does not exist.

### 6.2 Authorization failures return HTTP 200

`checkLogin` returns 200 on every rejection path (missing token, bad session, decrypt failure): `payment_ms/middlewares/login/checkLogin.js:14-20`, `authentication_ms/middlewares/login/checkLogin.js:17-21`, `system_users_ms/middlewares/login/checkLogin.js:14-18`. The same pattern is in `isAdmin` (`authentication_ms/middlewares/permissions/isAdmin.js:12-16`), `moduleAccessCheck` (`payment_ms/middlewares/module/moduleAccessCheck.js:12-26`) and `singleSubdomainValidation` (`payment_ms/middlewares/subdomain/singleSubdomainValidation.js:15-26`). A 401/403 is never produced by these guards.

### 6.3 Money and tenant writes with no auth middleware

See §2.4. The highest-risk groups are:

- `inhouz_pay_ms` — `createpaymentintent`, `finalizestripeuipayment`, `markassuccess`, `serversubscriptionpayment`, `subscription/addsubscribers`, and both `ondemand` routes: `inhouz_pay_ms/controller/payment/paymentRoutes.js:43,46,49,62,76,78,79`.
- `payment_link_ms` — `recordsplitpayment`, `markpaymentlinkasused`, `setactivestatus`: `payment_link_ms/controller/payment/paymentLinkRoutes.js:67-69`.
- `payment_gateway_ms` — `createaccount` and `distribute/serverrun`: `payment_gateway_ms/controller/payment/paymentGatewayRoutes.js:66,79`.
- `inhouz_commerce_ms` — `servercreate` and `markaspurchased`: `inhouz_commerce_ms/controller/product/paymentProductRoutes.js:15,23`.
- `payment_ms` — `addsubscriptionpaymentmethod` and `payoutaccount/sanitycheck`: `payment_ms/controller/paymentRoutes.js:21`, `payment_ms/controller/payoutRoutes.js:21`.

### 6.4 Collection-name mismatch: `company`/`companies` and `User`/`users`

Models are registered from deployment env vars. Every service deployment sets `COMPANY_MODEL=company` and `USER_MODEL=User` (e.g. `payment_ms/k8s/payment-ms-deployment.yml:77-79`, `authentication_ms/k8s/authentication-ms-deployment.yml:102-108`), and the model files register those names (`payment_ms/model/company/company.js:108`, `payment_ms/model/user/user.js:107`).

Aggregation `$lookup` stages hardcode the plural/lowercase names instead:

- `from:'companies'` — `payment_ms/services/transactions/getPaymentIntents.js:90,117`, `payment_ms/services/transactions/getPaymentCharges.js:96,123`, `subscription_payment_ms/services/transactions/getPaymentIntents.js:55`, `subscription_payment_ms/services/transactions/getPaymentCharges.js:61`, `subscription_metrics_ms/services/subscription/getSubscribers.js:118,139`, `module_transfer_ms/services/moduleTransfer/getModuleTransferPackages.js:49,70`, `flex_api_ms/services/flexApi/getApisDocumentation.js:113`.
- `from:'users'` — `payment_ms/utils/payment/paymentMethod/getPaymentMethods.js:44,65`, `payment_ms/utils/payment/payoutAccount/getPayoutAccounts.js:41,62`, `app_builder_ms/services/appBuilder/getApps.js:88,109`, `payment_gateway_ms/services/paymentGateway/getGateways.js:46,67`, `payment_gateway_ms/services/taxRules/getTaxRules.js:46,67`, `system_users_ms/services/systemUser/getSystemUsers.js:96`.

MongoDB collection names are case-sensitive. A lookup against `companies` or `users` does not read the collection registered as `company` or `User`, so these joins return empty arrays without an error.

### 6.5 Permissive auth middleware

`apiKeyValidation`, `clientEncryptedLogin` and `serverEncryptedLogin` all call `next()` when their header is absent: `account_termination_ms/middlewares/apiKey/apiKeyValidation.js:13-18`, `inhouz_pay_ms/middlewares/login/clientEncryptedLogin.js:12-18`, `inhouz_pay_ms/middlewares/login/serverEncryptedLogin.js:13-18`. Mounting one after `isLoggedIn` is harmless; mounting one alone protects nothing.

### 6.6 Route declarations are not always real

The skeleton route lists include commented-out declarations. The code excludes: `payment_ms/controller/paymentRoutes.js:18-19` (both Braintree routes), `payment_link_ms/controller/payment/paymentLinkRoutes.js:73-80` (eight subscriber routes), and `function_parser_ms/lib/routes/index.js:6-8` (the whole router, never mounted). `scheduled_task_function_parser_ms/lib/routes/index.js:6-8` declares a router, but `lib/index.js` never mounts it; the only live route is the inline `app.post` at `scheduled_task_function_parser_ms/lib/index.js:89`.

