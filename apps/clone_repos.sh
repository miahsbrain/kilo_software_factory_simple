#!/usr/bin/env bash
#
# Clones every repo from the new org into a local working folder.
# If a repo is already cloned, it fetches and fast-forwards the current branch.
# Uses git only.
#
# Usage:
#   chmod +x clone_repos.sh
#   ./clone_repos.sh
#
set -uo pipefail

ORG="Inhouz-Cloud-AI"
WORKDIR="."

# Use "ssh" or "https"
PROTOCOL="https"

REPOS=(
    "database_execution_ms"
    "inhouz_pay_metrics_ms"
    "webcomponent_ms"
    "subscription_migration_parser_ms"
    "authentication_ms"
    "payment_validation_scheduler_ms"
    "general_task_scheduler_ms"
    "subscriber_data_function_ms"
    "subscription_settings_ms"
    "inhouz_subscription_ms"
    "image_proxy_ms"
    "inhouz_file_upload_ms"
    "view_builder_ms"
    "push_notification_parser_ms"
    "module_transfer_parser_ms"
    "general_task_parser_ms"
    "subscription_migration_scheduler_ms"
    "inhouz_pay_scheduler_ms"
    "scheduled_task_parser_ms"
    "subscription_payment_ms"
    "inhouz_sign_metrics_ms"
    "payment_ms"
    "file_operations_ms"
    "inhouz_pay_recurring_stats_ms"
    "multimedia_ms"
    "account_termination_cron_ms"
    "payment_link_ms"
    "document_scheduler_ms"
    "websocket_ms"
    "app_version_manager_ms"
    "app_builder_ms"
    "late_payment_ms"
    "inhouzio_app_ms"
    "contact_ms"
    "app_viewer_ms"
    "subscription_authentication_ms"
    "inhouz_pay_ms"
    "subscription_renewal_scheduler_ms"
    "functions_ms"
    "flex_module_collection_ms"
    "api_service_ms"
    "scheduled_task_ms"
    "appviewer_password_ms"
    "subscription_metrics_ms"
    "inhouz_project_ms"
    "function_parser_ms"
    "system_users_ms"
    "scheduled_launch_ms"
    "inhouz_security_ms"
    "data_scanner_ms"
    "remote_network_request_ms"
    "subscription_ms"
    "document_generation_parser_ms"
    "customer_portal_ms"
    "module_transfer_ms"
    "pdf_generator_ms"
    "inhouz_sign_ms"
    "subscription_signup_ms"
    "inhouz_subscription_renewal_ms"
    "flex_api_ms"
    "payment_gateway_ms"
    "payment_validation_ms"
    "inhouz_commerce_ms"
    "appbuilder_multiplayer_ms"
    "log_manager_ms"
    "app_metrics_ms"
    "scheduled_task_function_parser_ms"
    "account_termination_ms"
    "scheduled_task_scheduler_ms"
    "website_resource_ms"
    "subscription_renewal_ms"
    "subscription_authorization_ms"
    "inhouz_subscription_renewal_scheduler_ms"
    "churn_tracker_ms"
    "appviewer_log_ms"
)

url() { # url <repo>
    if [ "$PROTOCOL" = "ssh" ]; then
        echo "git@github.com:$ORG/$1.git"
    else
        echo "https://github.com/$ORG/$1.git"
    fi
}

mkdir -p "$WORKDIR"
cd "$WORKDIR"
FAILED=()

for repo in "${REPOS[@]}"; do
    echo
    echo "==> $repo"
    if [ -d "$repo/.git" ]; then
        # Already cloned: update all remote branches, then fast-forward the current one
        git -C "$repo" fetch --all --prune --tags &&
            git -C "$repo" pull --ff-only ||
            {
                echo "!! Failed to update: $repo"
                FAILED+=("$repo")
            }
    else
        git clone "$(url "$repo")" "$repo" ||
            {
                echo "!! Failed to clone: $repo"
                FAILED+=("$repo")
            }
    fi
done

echo
echo "==> Done: $((${#REPOS[@]} - ${#FAILED[@]})) / ${#REPOS[@]} succeeded."
if [ ${#FAILED[@]} -gt 0 ]; then
    printf 'Failed:\n'
    printf '  - %s\n' "${FAILED[@]}"
    exit 1
fi
