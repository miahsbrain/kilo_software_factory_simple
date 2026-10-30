# PROJECT STRUCTURE

Authoritative folder layout. Update this file immediately when folders are added, renamed,
moved, or discovered to be different from what is recorded here. This file records reality; it
does not impose it.

This workspace is one **control repo** plus 75 **microservice repositories**. The control repo
holds `AGENTS.md`, `docs/`, `DOMAIN.md`, `ROADMAP.md`, `CHANGELOG.md`, `.kilo/`, `kilo.jsonc` and
`artifacts/` (`AGENTS.md:9-11`, `AGENTS.md:81-84`). Each microservice lives in its own git repository nested at
`apps/<name>/`, with its own remote `https://github.com/Inhouz-Cloud-AI/<name>.git`
(`apps/clone_repos.sh:99-101`). The control repo does not track those nested repos
(`.gitignore:1-7`).

## Current layout

    control-repo/
    ├── AGENTS.md                     # architect + orchestrator rules
    ├── DOMAIN.md                     # product scope, terminology, user-facing rules
    ├── ROADMAP.md                    # planned work not in progress
    ├── CHANGELOG.md                  # product-facing changelog (user-approved only)
    ├── README.md
    ├── kilo.jsonc                    # Kilo config, permission map, MCPs
    ├── .gitignore                    # ignores apps/*/ except the three scope slots
    ├── .devcontainer/                # dev container definition (Dockerfile, devcontainer.json)
    ├── .kilo/
    │   ├── agent/                    # agent definitions (frontend-dev, backend-dev, docs-writer…)
    │   ├── command/                  # slash commands, derived from AGENTS.md
    │   ├── policies/git-policy.json  # canonical guard-rail policy
    │   ├── repos.json                # repo id → path map (79 entries)
    │   ├── scopes/<id>.md            # canonical scope rules, one per scope
    │   ├── skills/                   # git-worktree, board, qa-review + their scripts
    │   └── worktrees/                # one worktree per board row (git-ignored)
    ├── artifacts/
    │   └── <scope>/qa/<date>/<task-id>/   # canonical UI evidence folder
    ├── docs/
    │   ├── PROJECT_STRUCTURE.md      # this file
    │   ├── HANDOVER.md               # living description of the app as it is now
    │   ├── ARCHITECTURE.md
    │   ├── BUSINESS-LOGIC.md
    │   ├── UI-UX.md
    │   ├── BOARD.md                  # work tracking board, single writer = orchestrator
    │   ├── STACK.md
    │   ├── PROJECT_STATE.md
    │   ├── DECISIONS.md
    │   ├── RISKS.md
    │   ├── API_CONTRACTS.md
    │   ├── ENVIRONMENT.md
    │   ├── README.md
    │   ├── reviews/                  # QA and UI/UX reports and round ledgers
    │   ├── handover/                 # memory map: README.md index + one file per unit
    │   └── changelog/                # engineering changelog
    └── apps/
        ├── web/                      # scope slot: AGENTS.md only, NOT a git repo
        ├── mobile/                   # scope slot: AGENTS.md only, NOT a git repo
        ├── api/                      # scope slot: AGENTS.md only, NOT a git repo
        ├── clone_repos.sh            # clones the 75 service repos from the org
        └── <unit>/                   # 75 microservice folders, each its own git repo

The 75 microservice folders under `apps/` are **not shown in the tree and not tracked here**.
Each one is a separate git repository with its own remote, so `.gitignore:4` ignores `apps/*/`
and only re-includes the three scope slots (`.gitignore:5-7`). They are listed in the table below
instead. `web`, `mobile` and `api` contain only their `AGENTS.md` and are not git repositories.

## The 75 units

`Kind` is `service` when the unit has a ClusterIP Service manifest, so other pods can reach it by
DNS name; it is `worker` when the unit has only a Deployment and no Service manifest. Every unit
starts an HTTP listener (`apps/churn_tracker_ms/server.js:84`, `apps/payment_ms/server.js:89`);
the difference is reachability, not the presence of a server.

`Repository id` is the id in `.kilo/repos.json` and equals the folder name
(`.kilo/repos.json:3-80`).

| Unit | Path | Repository id | Kind | Port | k8s service name | Evidence |
|---|---|---|---|---|---|---|
| account_termination_cron_ms | `apps/account_termination_cron_ms/` | `account_termination_cron_ms` | worker | 5047 | — (no Service) | `apps/account_termination_cron_ms/k8s/account-termination-cron-ms-deployment.yml:26` |
| account_termination_ms | `apps/account_termination_ms/` | `account_termination_ms` | service | 5048 | `account-termination-ms-cluster-ip-service` | `apps/account_termination_ms/k8s/account-termination-ms-cluster-ip-service.yml:10` |
| api_service_ms | `apps/api_service_ms/` | `api_service_ms` | service | 5010 | `api-service-ms-cluster-ip-service` | `apps/api_service_ms/k8s/api-service-ms-cluster-ip-service.yml:10` |
| app_builder_ms | `apps/app_builder_ms/` | `app_builder_ms` | service | 5016 | `app-builder-ms-cluster-ip-service` | `apps/app_builder_ms/k8s/app-builder-ms-cluster-ip-service.yml:10` |
| app_metrics_ms | `apps/app_metrics_ms/` | `app_metrics_ms` | service | 5054 | `app-metrics-ms-cluster-ip-service` | `apps/app_metrics_ms/k8s/app-metrics-ms-cluster-ip-service.yml:10` |
| app_version_manager_ms | `apps/app_version_manager_ms/` | `app_version_manager_ms` | service | 5074 | `app-version-manager-ms-cluster-ip-service` | `apps/app_version_manager_ms/k8s/app-version-manager-ms-cluster-ip-service.yml:10` |
| app_viewer_ms | `apps/app_viewer_ms/` | `app_viewer_ms` | service | 3000 | `app-viewer-ms-cluster-ip-service` | `apps/app_viewer_ms/k8s/app-viewer-ms-cluster-ip-service.yml:10` |
| appbuilder_multiplayer_ms | `apps/appbuilder_multiplayer_ms/` | `appbuilder_multiplayer_ms` | service | 5019 | `appbuilder-multiplayer-ms-cluster-ip-service` | `apps/appbuilder_multiplayer_ms/k8s/appbuilder-multiplayer-ms-cluster-ip-service.yml:10` |
| appviewer_log_ms | `apps/appviewer_log_ms/` | `appviewer_log_ms` | service | 5046 | `appviewer-log-ms-cluster-ip-service` | `apps/appviewer_log_ms/k8s/appviewer-log-ms-cluster-ip-service.yml:10` |
| appviewer_password_ms | `apps/appviewer_password_ms/` | `appviewer_password_ms` | service | 5040 | `appviewer-password-ms-cluster-ip-service` | `apps/appviewer_password_ms/k8s/appviewer-password-ms-cluster-ip-service.yml:10` |
| authentication_ms | `apps/authentication_ms/` | `authentication_ms` | service | 5002 | `authentication-ms-cluster-ip-service` | `apps/authentication_ms/k8s/authentication-ms-cluster-ip-service.yml:10` |
| churn_tracker_ms | `apps/churn_tracker_ms/` | `churn_tracker_ms` | worker | 5029 | — (no Service) | `apps/churn_tracker_ms/k8s/churn-tracker-ms-deployment.yml:26` |
| contact_ms | `apps/contact_ms/` | `contact_ms` | service | 5071 | `contact-ms-cluster-ip-service` | `apps/contact_ms/k8s/contact-ms-cluster-ip-service.yml:10` |
| customer_portal_ms | `apps/customer_portal_ms/` | `customer_portal_ms` | service | 5062 | `customer-portal-ms-cluster-ip-service` | `apps/customer_portal_ms/k8s/customer-portal-ms-cluster-ip-service.yml:10` |
| data_scanner_ms | `apps/data_scanner_ms/` | `data_scanner_ms` | worker | 5015 | — (no Service) | `apps/data_scanner_ms/k8s/data-scanner-ms-deployment.yml:26` |
| database_execution_ms | `apps/database_execution_ms/` | `database_execution_ms` | service | 5021 | `database-execution-ms-cluster-ip-service` | `apps/database_execution_ms/k8s/database-execution-ms-cluster-ip-service.yml:10` |
| document_generation_parser_ms | `apps/document_generation_parser_ms/` | `document_generation_parser_ms` | service | 5069 | `document-generation-parser-ms-cluster-ip-service` | `apps/document_generation_parser_ms/k8s/document-generation-parser-ms-cluster-ip-service.yml:10` |
| document_scheduler_ms | `apps/document_scheduler_ms/` | `document_scheduler_ms` | worker | 5066 | — (no Service) | `apps/document_scheduler_ms/k8s/document-scheduler-ms-deployment.yml:26` |
| file_operations_ms | `apps/file_operations_ms/` | `file_operations_ms` | service | 5008 | `file-operations-ms-cluster-ip-service` | `apps/file_operations_ms/k8s/file-operations-ms-cluster-ip-service.yml:10` |
| flex_api_ms | `apps/flex_api_ms/` | `flex_api_ms` | service | 5006 | `flex-api-ms-cluster-ip-service` | `apps/flex_api_ms/k8s/flex-api-ms-cluster-ip-service.yml:10` |
| flex_module_collection_ms | `apps/flex_module_collection_ms/` | `flex_module_collection_ms` | service | 5004 | `flex-module-collection-ms-cluster-ip-service` | `apps/flex_module_collection_ms/k8s/flex-module-collection-ms-cluster-ip-service.yml:10` |
| function_parser_ms | `apps/function_parser_ms/` | `function_parser_ms` | service | 5035 | `function-parser-ms-cluster-ip-service` | `apps/function_parser_ms/k8s/function-parser-ms-cluster-ip-service.yml:10` |
| functions_ms | `apps/functions_ms/` | `functions_ms` | service | 5001 | `functions-ms-cluster-ip-service` | `apps/functions_ms/k8s/functions-ms-cluster-ip-service.yml:10` |
| general_task_parser_ms | `apps/general_task_parser_ms/` | `general_task_parser_ms` | service | 5042 | `general-task-parser-ms-cluster-ip-service` | `apps/general_task_parser_ms/k8s/general-task-parser-ms-cluster-ip-service.yml:10` |
| general_task_scheduler_ms | `apps/general_task_scheduler_ms/` | `general_task_scheduler_ms` | worker | 5075 | — (no Service) | `apps/general_task_scheduler_ms/k8s/general-task-scheduler-ms-deployment.yml:26` |
| image_proxy_ms | `apps/image_proxy_ms/` | `image_proxy_ms` | service | 5034 | `image-proxy-ms-cluster-ip-service` | `apps/image_proxy_ms/k8s/image-proxy-ms-cluster-ip-service.yml:10` |
| inhouz_commerce_ms | `apps/inhouz_commerce_ms/` | `inhouz_commerce_ms` | service | 5060 | `inhouz-commerce-ms-cluster-ip-service` | `apps/inhouz_commerce_ms/k8s/inhouz-commerce-ms-cluster-ip-service.yml:10` |
| inhouz_file_upload_ms | `apps/inhouz_file_upload_ms/` | `inhouz_file_upload_ms` | service | 5053 | `inhouz-file-upload-ms-cluster-ip-service` | `apps/inhouz_file_upload_ms/k8s/inhouz-file-upload-ms-cluster-ip-service.yml:10` |
| inhouz_pay_metrics_ms | `apps/inhouz_pay_metrics_ms/` | `inhouz_pay_metrics_ms` | service | 5064 | `inhouz-pay-metrics-ms-cluster-ip-service` | `apps/inhouz_pay_metrics_ms/k8s/inhouz-pay-metrics-ms-cluster-ip-service.yml:10` |
| inhouz_pay_ms | `apps/inhouz_pay_ms/` | `inhouz_pay_ms` | service | 5058 | `inhouz-pay-ms-cluster-ip-service` | `apps/inhouz_pay_ms/k8s/inhouz-pay-ms-cluster-ip-service.yml:10` |
| inhouz_pay_recurring_stats_ms | `apps/inhouz_pay_recurring_stats_ms/` | `inhouz_pay_recurring_stats_ms` | service | 5063 | `inhouz-pay-recurring-stats-ms-cluster-ip-service` | `apps/inhouz_pay_recurring_stats_ms/k8s/inhouz-pay-recurring-stats-ms-cluster-ip-service.yml:10` |
| inhouz_pay_scheduler_ms | `apps/inhouz_pay_scheduler_ms/` | `inhouz_pay_scheduler_ms` | service | 5061 | `inhouz-pay-scheduler-ms-cluster-ip-service` | `apps/inhouz_pay_scheduler_ms/k8s/inhouz-pay-scheduler-ms-cluster-ip-service.yml:10` |
| inhouz_project_ms | `apps/inhouz_project_ms/` | `inhouz_project_ms` | service | 5067 | `inhouz-project-ms-cluster-ip-service` | `apps/inhouz_project_ms/k8s/inhouz-project-ms-cluster-ip-service.yml:10` |
| inhouz_security_ms | `apps/inhouz_security_ms/` | `inhouz_security_ms` | service | 5068 | `inhouz-security-ms-cluster-ip-service` | `apps/inhouz_security_ms/k8s/inhouz-security-ms-cluster-ip-service.yml:10` |
| inhouz_sign_metrics_ms | `apps/inhouz_sign_metrics_ms/` | `inhouz_sign_metrics_ms` | service | 5070 | `inhouz-sign-metrics-ms-cluster-ip-service` | `apps/inhouz_sign_metrics_ms/k8s/inhouz-sign-metrics-ms-cluster-ip-service.yml:10` |
| inhouz_sign_ms | `apps/inhouz_sign_ms/` | `inhouz_sign_ms` | service | 5065 | `inhouz-sign-ms-cluster-ip-service` | `apps/inhouz_sign_ms/k8s/inhouz-sign-ms-cluster-ip-service.yml:10` |
| inhouz_subscription_ms | `apps/inhouz_subscription_ms/` | `inhouz_subscription_ms` | service | 5041 | `inhouz-subscription-ms-cluster-ip-service` | `apps/inhouz_subscription_ms/k8s/inhouz-subscription-ms-cluster-ip-service.yml:10` |
| inhouz_subscription_renewal_ms | `apps/inhouz_subscription_renewal_ms/` | `inhouz_subscription_renewal_ms` | service | 5044 | `inhouz-subscription-renewal-ms-cluster-ip-service` | `apps/inhouz_subscription_renewal_ms/k8s/inhouz-subscription-renewal-ms-cluster-ip-service.yml:10` |
| inhouz_subscription_renewal_scheduler_ms | `apps/inhouz_subscription_renewal_scheduler_ms/` | `inhouz_subscription_renewal_scheduler_ms` | worker | 5043 | — (no Service) | `apps/inhouz_subscription_renewal_scheduler_ms/k8s/inhouz-subscription-renewal-scheduler-ms-deployment.yml:26` |
| inhouzio_app_ms | `apps/inhouzio_app_ms/` | `inhouzio_app_ms` | service | 5000 | `inhouzio-app-ms-cluster-ip-service` | `apps/inhouzio_app_ms/k8s/inhouzio-app-ms-cluster-ip-service.yml:10` |
| late_payment_ms | `apps/late_payment_ms/` | `late_payment_ms` | service | 5051 | `late-payment-ms-cluster-ip-service` | `apps/late_payment_ms/k8s/late-payment-ms-cluster-ip-service.yml:10` |
| log_manager_ms | `apps/log_manager_ms/` | `log_manager_ms` | worker | 5073 | — (no Service) | `apps/log_manager_ms/k8s/log-manager-ms-deployment.yml:26` |
| module_transfer_ms | `apps/module_transfer_ms/` | `module_transfer_ms` | service | 5078 | `module-transfer-ms-cluster-ip-service` | `apps/module_transfer_ms/k8s/module-transfer-ms-cluster-ip-service.yml:10` |
| module_transfer_parser_ms | `apps/module_transfer_parser_ms/` | `module_transfer_parser_ms` | service | 5077 | `module-transfer-parser-ms-cluster-ip-service` | `apps/module_transfer_parser_ms/k8s/module-transfer-parser-ms-cluster-ip-service.yml:10` |
| multimedia_ms | `apps/multimedia_ms/` | `multimedia_ms` | service | 5013 | `multimedia-ms-cluster-ip-service` | `apps/multimedia_ms/k8s/multimedia-ms-cluster-ip-service.yml:10` |
| payment_gateway_ms | `apps/payment_gateway_ms/` | `payment_gateway_ms` | service | 5057 | `payment-gateway-ms-cluster-ip-service` | `apps/payment_gateway_ms/k8s/payment-gateway-ms-cluster-ip-service.yml:10` |
| payment_link_ms | `apps/payment_link_ms/` | `payment_link_ms` | service | 5059 | `payment-link-ms-cluster-ip-service` | `apps/payment_link_ms/k8s/payment-link-ms-cluster-ip-service.yml:10` |
| payment_ms | `apps/payment_ms/` | `payment_ms` | service | 5014 | `payment-ms-cluster-ip-service` | `apps/payment_ms/k8s/payment-ms-cluster-ip-service.yml:10` |
| payment_validation_ms | `apps/payment_validation_ms/` | `payment_validation_ms` | service | 5050 | `payment-validation-ms-cluster-ip-service` | `apps/payment_validation_ms/k8s/payment-validation-ms-cluster-ip-service.yml:10` |
| payment_validation_scheduler_ms | `apps/payment_validation_scheduler_ms/` | `payment_validation_scheduler_ms` | service | 5049 | `payment-validation-scheduler-ms-cluster-ip-service` | `apps/payment_validation_scheduler_ms/k8s/payment-validation-scheduler-ms-cluster-ip-service.yml:10` |
| pdf_generator_ms | `apps/pdf_generator_ms/` | `pdf_generator_ms` | service | 5072 | `pdf-generator-ms-cluster-ip-service` | `apps/pdf_generator_ms/k8s/pdf-generator-ms-cluster-ip-service.yml:10` |
| push_notification_parser_ms | `apps/push_notification_parser_ms/` | `push_notification_parser_ms` | service | 5076 | `push-notification-parser-ms-cluster-ip-service` | `apps/push_notification_parser_ms/k8s/push-notification-parser-ms-cluster-ip-service.yml:10` |
| remote_network_request_ms | `apps/remote_network_request_ms/` | `remote_network_request_ms` | service | 5045 | `remote-network-request-ms-cluster-ip-service` | `apps/remote_network_request_ms/k8s/remote-network-request-ms-cluster-ip-service.yml:10` |
| scheduled_launch_ms | `apps/scheduled_launch_ms/` | `scheduled_launch_ms` | worker | 5100 | — (no Service) | `apps/scheduled_launch_ms/k8s/scheduled-launch-ms-deployment.yml:26` |
| scheduled_task_function_parser_ms | `apps/scheduled_task_function_parser_ms/` | `scheduled_task_function_parser_ms` | service | 5038 | `scheduled-task-function-parser-ms-cluster-ip-service` | `apps/scheduled_task_function_parser_ms/k8s/scheduled-task-function-parser-ms-cluster-ip-service.yml:10` |
| scheduled_task_ms | `apps/scheduled_task_ms/` | `scheduled_task_ms` | service | 5007 | `scheduled-task-ms-cluster-ip-service` | `apps/scheduled_task_ms/k8s/scheduled-task-ms-cluster-ip-service.yml:10` |
| scheduled_task_parser_ms | `apps/scheduled_task_parser_ms/` | `scheduled_task_parser_ms` | service | 5037 | `scheduled-task-parser-ms-cluster-ip-service` | `apps/scheduled_task_parser_ms/k8s/scheduled-task-parser-ms-cluster-ip-service.yml:10` |
| scheduled_task_scheduler_ms | `apps/scheduled_task_scheduler_ms/` | `scheduled_task_scheduler_ms` | worker | 5036 | — (no Service) | `apps/scheduled_task_scheduler_ms/k8s/scheduled-task-scheduler-ms-deployment.yml:26` |
| subscriber_data_function_ms | `apps/subscriber_data_function_ms/` | `subscriber_data_function_ms` | service | 5055 | `subscriber-data-function-ms-cluster-ip-service` | `apps/subscriber_data_function_ms/k8s/subscription-metrics-ms-cluster-ip-service.yml:10` |
| subscription_authentication_ms | `apps/subscription_authentication_ms/` | `subscription_authentication_ms` | service | 5030 | `subscription-authentication-ms-cluster-ip-service` | `apps/subscription_authentication_ms/k8s/subscription-authentication-ms-cluster-ip-service.yml:10` |
| subscription_authorization_ms | `apps/subscription_authorization_ms/` | `subscription_authorization_ms` | service | 5031 | `subscription-authorization-ms-cluster-ip-service` | `apps/subscription_authorization_ms/k8s/subscription-authorization-ms-cluster-ip-service.yml:10` |
| subscription_metrics_ms | `apps/subscription_metrics_ms/` | `subscription_metrics_ms` | service | 5011 | `subscription-metrics-ms-cluster-ip-service` | `apps/subscription_metrics_ms/k8s/subscription-metrics-ms-cluster-ip-service.yml:10` |
| subscription_migration_parser_ms | `apps/subscription_migration_parser_ms/` | `subscription_migration_parser_ms` | service | 5025 | `subscription-migration-parser-ms-cluster-ip-service` | `apps/subscription_migration_parser_ms/k8s/subscription-migration-parser-ms-cluster-ip-service.yml:10` |
| subscription_migration_scheduler_ms | `apps/subscription_migration_scheduler_ms/` | `subscription_migration_scheduler_ms` | service | 5024 | `subscription-migration-scheduler-ms-cluster-ip-service` | `apps/subscription_migration_scheduler_ms/k8s/subscription-migration-scheduler-ms-cluster-ip-service.yml:10` |
| subscription_ms | `apps/subscription_ms/` | `subscription_ms` | service | 5005 | `subscription-ms-cluster-ip-service` | `apps/subscription_ms/k8s/subscription-ms-cluster-ip-service.yml:10` |
| subscription_payment_ms | `apps/subscription_payment_ms/` | `subscription_payment_ms` | service | 5032 | `subscription-payment-ms-cluster-ip-service` | `apps/subscription_payment_ms/k8s/subscription-payment-ms-cluster-ip-service.yml:10` |
| subscription_renewal_ms | `apps/subscription_renewal_ms/` | `subscription_renewal_ms` | service | 5027 | `subscription-renewal-ms-cluster-ip-service` | `apps/subscription_renewal_ms/k8s/subscription-renewal-ms-cluster-ip-service.yml:10` |
| subscription_renewal_scheduler_ms | `apps/subscription_renewal_scheduler_ms/` | `subscription_renewal_scheduler_ms` | service | 5026 | `subscription-renewal-scheduler-ms-cluster-ip-service` | `apps/subscription_renewal_scheduler_ms/k8s/subscription-renewal-scheduler-ms-cluster-ip-service.yml:10` |
| subscription_settings_ms | `apps/subscription_settings_ms/` | `subscription_settings_ms` | service | 5033 | `subscription-settings-ms-cluster-ip-service` | `apps/subscription_settings_ms/k8s/subscription-settings-ms-cluster-ip-service.yml:10` |
| subscription_signup_ms | `apps/subscription_signup_ms/` | `subscription_signup_ms` | service | 5023 | `subscription-signup-ms-cluster-ip-service` | `apps/subscription_signup_ms/k8s/subscription-signup-ms-cluster-ip-service.yml:10` |
| system_users_ms | `apps/system_users_ms/` | `system_users_ms` | service | 5022 | `system-user-ms-cluster-ip-service` | `apps/system_users_ms/k8s/system-user-ms-cluster-ip-service.yml:10` |
| view_builder_ms | `apps/view_builder_ms/` | `view_builder_ms` | service | 5017 | `view-builder-ms-cluster-ip-service` | `apps/view_builder_ms/k8s/view-builder-ms-cluster-ip-service.yml:10` |
| webcomponent_ms | `apps/webcomponent_ms/` | `webcomponent_ms` | service | 5039 | `webcomponent-ms-cluster-ip-service` | `apps/webcomponent_ms/k8s/webcomponent-ms-cluster-ip-service.yml:10` |
| website_resource_ms | `apps/website_resource_ms/` | `website_resource_ms` | service | 5056 | `website-resource-ms-cluster-ip-service` | `apps/website_resource_ms/k8s/website-resource-ms-cluster-ip-service.yml:10` |
| websocket_ms | `apps/websocket_ms/` | `websocket_ms` | service | 5079 | `websocket-ms-cluster-ip-service` | `apps/websocket_ms/k8s/websocket-ms-cluster-ip-service.yml:10` |

Nine of the 75 units are workers: they have a Deployment and no Service manifest. Three units
carry manifest names that do not follow the folder name. They are recorded above exactly as they
appear on disk:

- `subscriber_data_function_ms` keeps its Service in `subscription-metrics-ms-cluster-ip-service.yml`.
  The metadata name inside the file is correct: `subscriber-data-function-ms-cluster-ip-service`
  (`apps/subscriber_data_function_ms/k8s/subscription-metrics-ms-cluster-ip-service.yml:4`).
- `system_users_ms` deploys as `system-user-ms-deployment` with image `inhouz/system_user_ms`
  (`apps/system_users_ms/k8s/system-user-ms-deployment.yml:4`, `:17`).
- `scheduled_task_parser_ms` names its HPA and VPA files without the `ms` token
  (`apps/scheduled_task_parser_ms/k8s/scheduled-task-parser-hpa.yml:1`,
  `apps/scheduled_task_parser_ms/k8s/scheduled-task-parser-vpa.yml:1`).

## Path → purpose map

| Path | Purpose | Evidence |
|---|---|---|
| `AGENTS.md` | Rules that govern every agent working here: architect, builders, reviewers, docs writer | `AGENTS.md:1` |
| `DOMAIN.md` | Product scope, terminology and user-facing rules; base for architectural decisions | `AGENTS.md:702` |
| `ROADMAP.md` | Backlog of planned work not in progress | `AGENTS.md:703` |
| `CHANGELOG.md` | Product-facing changelog, updated only on explicit user instruction | `AGENTS.md:704` |
| `docs/` | All project documentation | `AGENTS.md:9-11` |
| `docs/handover/` | The application memory map: `README.md` is the global index, `<unit>.md` is one per unit | `AGENTS.md:707` |
| `docs/reviews/` | QA and UI/UX review reports and round ledgers. Documents, not artifacts | `AGENTS.md:1272-1273` |
| `artifacts/` | The one canonical folder for UI evidence: `<scope>/qa/<date>/<task-id>/` | `AGENTS.md:1250`, `AGENTS.md:1293` |
| `.kilo/policies/git-policy.json` | Canonical guard-rail policy. The permission map in `kilo.jsonc` and `guard.py check-git` are both derived from it | `AGENTS.md:1550`, `.kilo/skills/git-worktree/scripts/guard.py:429` |
| `.kilo/repos.json` | The repo map: repo id → path, relative to the control repo root. 79 entries: `control`, `web`, `mobile`, `api` and the 75 service repos | `.kilo/repos.json:1-81` |
| `.kilo/scopes/<id>.md` | The canonical copy of a scope's rules. `guard.py sync --repo <id>` writes it into that repository as its `AGENTS.md` | `AGENTS.md:1189-1191` |
| `apps/<name>/` | One folder per app or microservice. A service folder is its own git repository | `AGENTS.md:81-91` |
| `apps/clone_repos.sh` | Clones the 75 service repos from `Inhouz-Cloud-AI` into `apps/`; fetches and fast-forwards when already present | `apps/clone_repos.sh:19`, `apps/clone_repos.sh:121` |
| `.devcontainer/` | Dev container definition: `Dockerfile`, `devcontainer.json`, lockfile | `.devcontainer/devcontainer.json:1` |
| `apps/web/`, `apps/mobile/`, `apps/api/` | Scope slots. Each holds only its `AGENTS.md`; the control repo tracks them explicitly | `.gitignore:5-7` |

## Rules

- Existing layouts are kept as discovered. This file records reality; it does not impose it
  (`AGENTS.md:86-88`).
- The repo map in `.kilo/repos.json` is the only way into another repository. A repo is addressed
  by id, never by a raw path (`AGENTS.md:82-84`, `.kilo/skills/git-worktree/scripts/guard.py:735`).
- `guard.py check-repos` proves the map and the `apps/` layout agree; a missing or extra folder
  fails the check (`.kilo/skills/git-worktree/scripts/guard.py:34`, `:849`).
- One app or microservice per folder. A new service is a new folder under `apps/`, never a folder
  inside another service (`AGENTS.md:90-92`).
- Every app folder gets its own `AGENTS.md` with builder rules for that scope (`AGENTS.md:93-94`).
  The canonical copy lives in `.kilo/scopes/<id>.md`; `guard.py sync` keeps them in step
  (`AGENTS.md:1189-1191`).
- New projects start from the three scope slots `apps/web`, `apps/mobile`, `apps/api`; this
  project is past that point, so the slots stay empty and each service gets its own repository
  (`AGENTS.md:55-80`, `.gitignore:4-7`).
- Nested service repos are never tracked by the control repo. `.gitignore` ignores `apps/*/` and
  re-includes only the three scope slots (`.gitignore:1-7`).
- A new service repository must be added to `.kilo/repos.json` in the same change, or
  `guard.py check-repos` fails (`.kilo/skills/git-worktree/scripts/guard.py:34`).
