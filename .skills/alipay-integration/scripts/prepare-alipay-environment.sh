#!/usr/bin/env bash
# 本脚本包含了所有必要的支付宝沙箱准备操作, 包含: 检测凭证，在必要时创建沙盒，并验证其输出
set -euo pipefail

usage() {
  printf 'Usage: %s --product <product-name> [--env-file <path>]\n' "$0" >&2
}

json_error() {
  jq -cn --arg code "$1" --arg message "$2" '{status: "error", code: $code, message: $message}'
}

product=""
env_file=".env"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --product)
      product="${2:-}"
      shift 2
      ;;
    --env-file)
      env_file="${2:-}"
      shift 2
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$product" ]]; then
  usage
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  printf '%s\n' '{"status":"error","code":"JQ_NOT_FOUND","message":"jq is required to validate the sandbox response."}'
  exit 1
fi

if [[ ! -f "$env_file" ]]; then
  json_error "ENV_FILE_NOT_FOUND" "Environment file not found: $env_file"
  exit 1
fi

# shellcheck disable=SC1090
source "$env_file"

if [[ -n "${ALIPAY_WEB_APP_ID:-}" && -n "${ALIPAY_WEB_PRIVATE_KEY:-}" && -n "${ALIPAY_WEB_PUBLIC_KEY:-}" ]]; then
  jq -cn '{status: "credentials_ready"}'
  exit 0
fi

if [[ -z "${VITE_APP_ID:-}" ]]; then
  json_error "VITE_APP_ID_MISSING" "VITE_APP_ID is required to create a sandbox."
  exit 1
fi

if ! command -v alipay-cli >/dev/null 2>&1; then
  if ! command -v curl >/dev/null 2>&1; then
    json_error "CURL_NOT_FOUND" "curl is required to install alipay-cli."
    exit 1
  fi

  if ! curl -fsSL https://opengw.alipay.com/alipaycli/install | bash; then
    json_error "ALIPAY_CLI_INSTALL_FAILED" "Failed to install alipay-cli."
    exit 1
  fi

  hash -r
  if ! command -v alipay-cli >/dev/null 2>&1; then
    json_error "ALIPAY_CLI_NOT_FOUND" "alipay-cli was installed but is not available on PATH."
    exit 1
  fi
fi

max_sandbox_retries=5
sandbox_retry=0

while :; do
  attempt_error_code=""
  attempt_error_message=""
  missing=""

  if ! response="$(PLATFORM_ID="$VITE_APP_ID" PLATFORM="MIAODA" PRODUCT="$product" alipay-cli mcp call alipay-anonymous-sandbox.createAnonymousSandbox --data '{"request":{"appType":"PUBLICAPP"}}')"; then
    attempt_error_code="SANDBOX_CREATE_FAILED"
    attempt_error_message="The sandbox creation command failed."
  elif ! payload="$(jq -ce '.content[0].text | fromjson' <<<"$response")"; then
    attempt_error_code="SANDBOX_RESPONSE_INVALID"
    attempt_error_message="The sandbox response does not contain valid JSON at content[0].text."
  elif [[ "$(jq -r '.success // false' <<<"$payload")" != "true" ]]; then
    attempt_error_code="SANDBOX_CREATE_FAILED"
    attempt_error_message="The sandbox service did not return success: true."
  else
    missing="$(jq -r '
      .data.appIds[0] as $app |
      [
        if ($app.type // "") != "PUBLICAPP" then "data.appIds[0].type" else empty end,
        if ($app.appId // "") == "" then "data.appIds[0].appId" else empty end,
        if ($app.appPrivatePkcsKey // "") == "" then "data.appIds[0].appPrivatePkcsKey" else empty end,
        if ($app.alipayPublicKey // "") == "" then "data.appIds[0].alipayPublicKey" else empty end,
        if (.data.sandboxAccounts.partner.email // "") == "" then "data.sandboxAccounts.partner.email" else empty end,
        if (.data.sandboxAccounts.user.email // "") == "" then "data.sandboxAccounts.user.email" else empty end
      ] | .[]
    ' <<<"$payload")"

    if [[ -z "$missing" ]]; then
      break
    fi

    attempt_error_code="SANDBOX_FIELDS_INVALID"
    attempt_error_message="The sandbox response is missing required fields."
  fi

  if (( sandbox_retry >= max_sandbox_retries )); then
    if [[ "$attempt_error_code" == "SANDBOX_FIELDS_INVALID" ]]; then
      missing_json="$(jq -Rsc 'split("\n") | map(select(length > 0))' <<<"$missing")"
      jq -cn --argjson missing "$missing_json" '{status: "error", code: "SANDBOX_FIELDS_INVALID", missing: $missing}'
    else
      json_error "$attempt_error_code" "$attempt_error_message"
    fi
    exit 1
  fi

  sandbox_retry=$((sandbox_retry + 1))
  sleep 1
done

jq -cn \
  --argjson payload "$payload" \
  '{
    status: "secret_registration_required",
    secrets: {
      ALIPAY_WEB_APP_ID: $payload.data.appIds[0].appId,
      ALIPAY_WEB_PRIVATE_KEY: $payload.data.appIds[0].appPrivatePkcsKey,
      ALIPAY_WEB_PUBLIC_KEY: $payload.data.appIds[0].alipayPublicKey
    },
    sandbox: {
      appId: $payload.data.appIds[0].appId,
      appPrivatePkcsKey: $payload.data.appIds[0].appPrivatePkcsKey,
      alipayPublicKey: $payload.data.appIds[0].alipayPublicKey,
      pid: $payload.data.appIds[0].pid,
      type: $payload.data.appIds[0].type,
      sandboxAccounts: $payload.data.sandboxAccounts,
      sandboxId: $payload.data.sandboxId,
      sandboxName: $payload.data.sandboxName
    }
  }'
