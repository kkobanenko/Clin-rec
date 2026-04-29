#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
PYTEST_BIN="${PYTEST_BIN:-$ROOT_DIR/.venv/bin/pytest}"
INTEGRATION_POSTGRES_URL="${CRIN_INTEGRATION_POSTGRES_URL:-postgresql://crplatform:crplatform@localhost:5433/crplatform}"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/.artifacts/release_checks/$TIMESTAMP}"
SUMMARY_TEMPLATE="$ROOT_DIR/docs/RELEASE_SUMMARY_TEMPLATE.md"
SUMMARY_FILE="$OUT_DIR/release_summary.md"
RUNTIME_PROFILE="${RUNTIME_PROFILE:-unknown}"
OPERATOR_NAME="${OPERATOR_NAME:-${USER:-unknown}}"
STRUCTURAL_SMOKE_ARGS=(scripts/e2e_smoke.py --mode structural)
QUALITY_SMOKE_ARGS=(scripts/e2e_smoke.py --mode quality)
STRUCTURAL_POLL_TIMEOUT="${STRUCTURAL_SMOKE_POLL_TIMEOUT:-${SMOKE_POLL_TIMEOUT:-}}"
QUALITY_POLL_TIMEOUT="${QUALITY_SMOKE_POLL_TIMEOUT:-${SMOKE_POLL_TIMEOUT:-}}"
SKIP_STRUCTURAL_SMOKE="${SKIP_STRUCTURAL_SMOKE:-0}"
SKIP_QUALITY_SMOKE="${SKIP_QUALITY_SMOKE:-0}"
QUALITY_GATE_API_BASE="${QUALITY_GATE_API_BASE:-http://127.0.0.1:8000}"
QUALITY_GATE_MAX_VERSIONS="${QUALITY_GATE_MAX_VERSIONS:-100}"
QUALITY_GATE_HIGH_SKIP_THRESHOLD="${QUALITY_GATE_HIGH_SKIP_THRESHOLD:-0.8}"
QUALITY_GATE_MAX_AVG_SKIP_RATE="${QUALITY_GATE_MAX_AVG_SKIP_RATE:-0.75}"
QUALITY_GATE_MIN_CANDIDATE_PAIRS="${QUALITY_GATE_MIN_CANDIDATE_PAIRS:-1}"
QUALITY_GATE_FAIL_ON_WARN="${QUALITY_GATE_FAIL_ON_WARN:-0}"
QUALITY_GATE_ALLOW_NO_DATA="${QUALITY_GATE_ALLOW_NO_DATA:-0}"
QUALITY_GATE_WEBHOOK_URL="${QUALITY_GATE_WEBHOOK_URL:-}"
QUALITY_GATE_NOTIFY_RETRIES="${QUALITY_GATE_NOTIFY_RETRIES:-2}"
QUALITY_GATE_NOTIFY_REQUIRED="${QUALITY_GATE_NOTIFY_REQUIRED:-0}"
QUALITY_GATE_NOTIFY_SPOOL_DIR="${QUALITY_GATE_NOTIFY_SPOOL_DIR:-$ROOT_DIR/.artifacts/quality_gate_notify_queue}"
QUALITY_GATE_NOTIFY_DRAIN_BEFORE="${QUALITY_GATE_NOTIFY_DRAIN_BEFORE:-1}"
QUALITY_GATE_NOTIFY_DRAIN_MAX_ITEMS="${QUALITY_GATE_NOTIFY_DRAIN_MAX_ITEMS:-50}"
QUEUE_POLICY_FAIL_ON_DEGRADED="${QUEUE_POLICY_FAIL_ON_DEGRADED:-0}"
QUEUE_POLICY_ALLOW_EMPTY="${QUEUE_POLICY_ALLOW_EMPTY:-1}"
INCIDENT_FAIL_ON_HIGH="${INCIDENT_FAIL_ON_HIGH:-0}"
INCIDENT_ALLOW_INFO="${INCIDENT_ALLOW_INFO:-1}"
QUALITY_GATE_INCIDENT_REGISTRY_DIR="${QUALITY_GATE_INCIDENT_REGISTRY_DIR:-$ROOT_DIR/.artifacts/quality_gate_incident_registry}"
QUALITY_GATE_INCIDENT_RETENTION_MAX_ITEMS="${QUALITY_GATE_INCIDENT_RETENTION_MAX_ITEMS:-1000}"
QUALITY_GATE_INCIDENT_RETENTION_MAX_AGE_DAYS="${QUALITY_GATE_INCIDENT_RETENTION_MAX_AGE_DAYS:-30}"
QUALITY_GATE_INCIDENT_RETENTION_APPLY="${QUALITY_GATE_INCIDENT_RETENTION_APPLY:-0}"
QUALITY_GATE_INCIDENT_RETENTION_FAIL_ON_REMOVALS="${QUALITY_GATE_INCIDENT_RETENTION_FAIL_ON_REMOVALS:-0}"
QUALITY_GATE_GOVERNANCE_MIN_SCORE="${QUALITY_GATE_GOVERNANCE_MIN_SCORE:-60}"

if [[ -n "$STRUCTURAL_POLL_TIMEOUT" ]]; then
    STRUCTURAL_SMOKE_ARGS+=(--poll-timeout "$STRUCTURAL_POLL_TIMEOUT")
fi

if [[ -n "$QUALITY_POLL_TIMEOUT" ]]; then
    QUALITY_SMOKE_ARGS+=(--poll-timeout "$QUALITY_POLL_TIMEOUT")
fi

if [[ -n "${SMOKE_ACTIVATE_MODEL_ID:-}" ]]; then
    QUALITY_SMOKE_ARGS+=(--activate-model-id "$SMOKE_ACTIVATE_MODEL_ID")
fi

if [[ -n "${SMOKE_ACTIVATE_MODEL_AUTHOR:-}" ]]; then
    QUALITY_SMOKE_ARGS+=(--activate-model-author "$SMOKE_ACTIVATE_MODEL_AUTHOR")
fi

if [[ "${SMOKE_FORCE_ACTIVATE_MODEL:-0}" == "1" ]]; then
    QUALITY_SMOKE_ARGS+=(--force-activate-model)
fi

run_step() {
    local step_id="$1"
    local title="$2"
    local log_file="$OUT_DIR/${step_id}.log"
    shift
    shift
    echo
    echo "==> ${title}"
    echo "Log: ${log_file}"
    set +e
    "$@" 2>&1 | tee "$log_file"
    local status=${PIPESTATUS[0]}
    set -e
    if [[ $status -ne 0 ]]; then
        echo "Step failed: ${title}" | tee -a "$log_file" >&2
        return "$status"
    fi
}

run_optional_step() {
    local step_id="$1"
    local title="$2"
    local log_file="$OUT_DIR/${step_id}.log"
    shift
    shift
    echo
    echo "==> ${title}"
    echo "Log: ${log_file}"
    set +e
    "$@" 2>&1 | tee "$log_file"
    local status=${PIPESTATUS[0]}
    set -e
    if [[ $status -ne 0 ]]; then
        echo "Optional step failed (continuing): ${title}" | tee -a "$log_file" >&2
    fi
}

ensure_log_has_no_skips() {
    local step_id="$1"
    local title="$2"
    local log_file="$OUT_DIR/${step_id}.log"
    if rg -n "\bskipped\b" "$log_file" >/dev/null 2>&1; then
        echo "Mandatory step produced skipped tests: ${title}" | tee -a "$log_file" >&2
        return 1
    fi
}

seed_summary_metadata() {
    local current_branch current_commit current_date validation_path branch_md commit_md runtime_md validation_md operator_md
    current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    current_commit="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
    current_date="$(date '+%Y-%m-%d %H:%M:%S %Z')"
    validation_path="full"
    if [[ "$SKIP_STRUCTURAL_SMOKE" == "1" && "$SKIP_QUALITY_SMOKE" == "1" ]]; then
        validation_path="late-stage rerun"
    elif [[ "$SKIP_STRUCTURAL_SMOKE" == "1" || "$SKIP_QUALITY_SMOKE" == "1" ]]; then
        validation_path="composite"
    fi

    printf -v branch_md '`%s`' "$current_branch"
    printf -v commit_md '`%s`' "$current_commit"
    printf -v runtime_md '`%s`' "$RUNTIME_PROFILE"
    printf -v validation_md '`%s`' "$validation_path"
    printf -v operator_md '`%s`' "$OPERATOR_NAME"

    sed -i \
        -e "s|^- Date:$|- Date: $current_date|" \
        -e "s|^- Branch:$|- Branch: $branch_md|" \
        -e "s|^- Commit SHA:$|- Commit SHA: $commit_md|" \
        -e "s|^- Runtime profile:.*$|- Runtime profile: $runtime_md|" \
        -e "s|^- Validation path:.*$|- Validation path: $validation_md|" \
        -e "s|^- Operator:$|- Operator: $operator_md|" \
        "$SUMMARY_FILE"
    sed -i "/^- Artifact bundle(s):$/a\  - \`$OUT_DIR\`" "$SUMMARY_FILE"
}

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Python executable not found: $PYTHON_BIN" >&2
    echo "Set PYTHON_BIN explicitly or create the project venv first." >&2
    exit 1
fi

if [[ ! -x "$PYTEST_BIN" ]]; then
    echo "Pytest executable not found: $PYTEST_BIN" >&2
    echo "Set PYTEST_BIN explicitly or install dev dependencies in the project venv." >&2
    exit 1
fi

cd "$ROOT_DIR"
mkdir -p "$OUT_DIR"

if [[ -f "$SUMMARY_TEMPLATE" ]]; then
    cp "$SUMMARY_TEMPLATE" "$SUMMARY_FILE"
    seed_summary_metadata
fi

echo "Release artifacts directory: $OUT_DIR"
if [[ -f "$SUMMARY_FILE" ]]; then
    echo "Seeded summary template: $SUMMARY_FILE"
fi
echo "Integration Postgres URL: $INTEGRATION_POSTGRES_URL"
echo "Quality Gate API base: $QUALITY_GATE_API_BASE"
if [[ -n "$QUALITY_GATE_WEBHOOK_URL" ]]; then
    echo "Quality Gate webhook: configured"
else
    echo "Quality Gate webhook: not configured"
fi
echo "Quality Gate spool dir: $QUALITY_GATE_NOTIFY_SPOOL_DIR"

if [[ "$SKIP_STRUCTURAL_SMOKE" != "1" ]]; then
    run_step structural_smoke "Structural smoke" "$PYTHON_BIN" -u "${STRUCTURAL_SMOKE_ARGS[@]}"
else
    echo "Skipping structural smoke because SKIP_STRUCTURAL_SMOKE=1"
fi

if [[ "$SKIP_QUALITY_SMOKE" != "1" ]]; then
    run_step quality_smoke "Quality smoke" "$PYTHON_BIN" -u "${QUALITY_SMOKE_ARGS[@]}"
else
    echo "Skipping quality smoke because SKIP_QUALITY_SMOKE=1"
fi

QUALITY_GATE_ARGS=(
    scripts/quality_gate_check.py
    --api-base "$QUALITY_GATE_API_BASE"
    --max-versions "$QUALITY_GATE_MAX_VERSIONS"
    --high-skip-threshold "$QUALITY_GATE_HIGH_SKIP_THRESHOLD"
    --max-avg-skip-rate "$QUALITY_GATE_MAX_AVG_SKIP_RATE"
    --min-candidate-pairs "$QUALITY_GATE_MIN_CANDIDATE_PAIRS"
    --json
)

if [[ "$QUALITY_GATE_FAIL_ON_WARN" == "1" ]]; then
    QUALITY_GATE_ARGS+=(--fail-on-warn)
fi

if [[ "$QUALITY_GATE_ALLOW_NO_DATA" == "1" ]]; then
    QUALITY_GATE_ARGS+=(--allow-no-data)
fi

run_step quality_gate_enforcement "Automated quality gate enforcement" "$PYTHON_BIN" -u "${QUALITY_GATE_ARGS[@]}"

if [[ "$QUALITY_GATE_NOTIFY_DRAIN_BEFORE" == "1" ]]; then
    DRAIN_ARGS=(
        scripts/quality_gate_notify_drain.py
        --spool-dir "$QUALITY_GATE_NOTIFY_SPOOL_DIR"
        --max-items "$QUALITY_GATE_NOTIFY_DRAIN_MAX_ITEMS"
        --retries "$QUALITY_GATE_NOTIFY_RETRIES"
    )
    if [[ -n "$QUALITY_GATE_WEBHOOK_URL" ]]; then
        DRAIN_ARGS+=(--webhook-url "$QUALITY_GATE_WEBHOOK_URL")
    fi
    if [[ "$QUALITY_GATE_NOTIFY_REQUIRED" == "1" ]]; then
        run_step quality_gate_notify_drain "Quality gate queue drain" "$PYTHON_BIN" -u "${DRAIN_ARGS[@]}"
    else
        DRAIN_ARGS+=(--allow-missing-webhook --soft-fail)
        run_optional_step quality_gate_notify_drain "Quality gate queue drain (best-effort)" "$PYTHON_BIN" -u "${DRAIN_ARGS[@]}"
    fi
fi

QUEUE_POLICY_ARGS=(
    scripts/quality_gate_queue_policy_check.py
    --api-base "$QUALITY_GATE_API_BASE"
    --max-items "$QUALITY_GATE_NOTIFY_DRAIN_MAX_ITEMS"
    --json
)

if [[ -n "$QUALITY_GATE_NOTIFY_SPOOL_DIR" ]]; then
    QUEUE_POLICY_ARGS+=(--spool-dir "$QUALITY_GATE_NOTIFY_SPOOL_DIR")
fi

if [[ "$QUEUE_POLICY_FAIL_ON_DEGRADED" == "1" ]]; then
    QUEUE_POLICY_ARGS+=(--fail-on-degraded)
fi

if [[ "$QUEUE_POLICY_ALLOW_EMPTY" == "1" ]]; then
    QUEUE_POLICY_ARGS+=(--allow-empty)
fi

if [[ "$QUALITY_GATE_NOTIFY_REQUIRED" == "1" ]]; then
    run_step queue_policy_check "Queue policy enforcement" "$PYTHON_BIN" -u "${QUEUE_POLICY_ARGS[@]}"
else
    run_optional_step queue_policy_check "Queue policy enforcement (best-effort)" "$PYTHON_BIN" -u "${QUEUE_POLICY_ARGS[@]}"
fi

INCIDENT_ARGS=(
    scripts/quality_gate_incident_check.py
    --api-base "$QUALITY_GATE_API_BASE"
    --max-versions "$QUALITY_GATE_MAX_VERSIONS"
    --high-skip-threshold "$QUALITY_GATE_HIGH_SKIP_THRESHOLD"
    --max-avg-skip-rate "$QUALITY_GATE_MAX_AVG_SKIP_RATE"
    --min-candidate-pairs "$QUALITY_GATE_MIN_CANDIDATE_PAIRS"
    --spool-dir "$QUALITY_GATE_NOTIFY_SPOOL_DIR"
    --max-items "$QUALITY_GATE_NOTIFY_DRAIN_MAX_ITEMS"
    --json
)

if [[ "$INCIDENT_FAIL_ON_HIGH" == "1" ]]; then
    INCIDENT_ARGS+=(--fail-on-high)
fi

if [[ "$INCIDENT_ALLOW_INFO" == "1" ]]; then
    INCIDENT_ARGS+=(--allow-info)
fi

if [[ "$QUALITY_GATE_NOTIFY_REQUIRED" == "1" ]]; then
    run_step incident_escalation_check "Incident escalation governance" "$PYTHON_BIN" -u "${INCIDENT_ARGS[@]}"
else
    run_optional_step incident_escalation_check "Incident escalation governance (best-effort)" "$PYTHON_BIN" -u "${INCIDENT_ARGS[@]}"
fi

INCIDENT_REGISTRY_ARGS=(
    scripts/quality_gate_incident_registry_update.py
    --api-base "$QUALITY_GATE_API_BASE"
    --max-versions "$QUALITY_GATE_MAX_VERSIONS"
    --high-skip-threshold "$QUALITY_GATE_HIGH_SKIP_THRESHOLD"
    --max-avg-skip-rate "$QUALITY_GATE_MAX_AVG_SKIP_RATE"
    --min-candidate-pairs "$QUALITY_GATE_MIN_CANDIDATE_PAIRS"
    --spool-dir "$QUALITY_GATE_NOTIFY_SPOOL_DIR"
    --max-items "$QUALITY_GATE_NOTIFY_DRAIN_MAX_ITEMS"
    --registry-dir "$QUALITY_GATE_INCIDENT_REGISTRY_DIR"
    --source "release_ready_check"
    --json
)

if [[ "$QUALITY_GATE_NOTIFY_REQUIRED" == "1" ]]; then
    run_step incident_registry_update "Incident registry persistence" "$PYTHON_BIN" -u "${INCIDENT_REGISTRY_ARGS[@]}"
else
    run_optional_step incident_registry_update "Incident registry persistence (best-effort)" "$PYTHON_BIN" -u "${INCIDENT_REGISTRY_ARGS[@]}"
fi

INCIDENT_RETENTION_ARGS=(
    scripts/quality_gate_incident_retention_check.py
    --registry-dir "$QUALITY_GATE_INCIDENT_REGISTRY_DIR"
    --max-items "$QUALITY_GATE_INCIDENT_RETENTION_MAX_ITEMS"
    --max-age-days "$QUALITY_GATE_INCIDENT_RETENTION_MAX_AGE_DAYS"
    --json
)

if [[ "$QUALITY_GATE_INCIDENT_RETENTION_APPLY" == "1" ]]; then
    INCIDENT_RETENTION_ARGS+=(--apply)
fi

if [[ "$QUALITY_GATE_INCIDENT_RETENTION_FAIL_ON_REMOVALS" == "1" ]]; then
    INCIDENT_RETENTION_ARGS+=(--fail-on-removals)
fi

if [[ "$QUALITY_GATE_NOTIFY_REQUIRED" == "1" ]]; then
    run_step incident_retention_check "Incident registry retention policy" "$PYTHON_BIN" -u "${INCIDENT_RETENTION_ARGS[@]}"
else
    run_optional_step incident_retention_check "Incident registry retention policy (best-effort)" "$PYTHON_BIN" -u "${INCIDENT_RETENTION_ARGS[@]}"
fi

GOVERNANCE_SCORE_ARGS=(
    scripts/quality_gate_governance_score_check.py
    --api-base "$QUALITY_GATE_API_BASE"
    --max-versions "$QUALITY_GATE_MAX_VERSIONS"
    --high-skip-threshold "$QUALITY_GATE_HIGH_SKIP_THRESHOLD"
    --max-avg-skip-rate "$QUALITY_GATE_MAX_AVG_SKIP_RATE"
    --min-candidate-pairs "$QUALITY_GATE_MIN_CANDIDATE_PAIRS"
    --spool-dir "$QUALITY_GATE_NOTIFY_SPOOL_DIR"
    --registry-dir "$QUALITY_GATE_INCIDENT_REGISTRY_DIR"
    --max-items "$QUALITY_GATE_NOTIFY_DRAIN_MAX_ITEMS"
    --min-score "$QUALITY_GATE_GOVERNANCE_MIN_SCORE"
    --json
)

if [[ "$QUALITY_GATE_NOTIFY_REQUIRED" == "1" ]]; then
    run_step governance_score_check "Governance score enforcement" "$PYTHON_BIN" -u "${GOVERNANCE_SCORE_ARGS[@]}"
else
    run_optional_step governance_score_check "Governance score enforcement (best-effort)" "$PYTHON_BIN" -u "${GOVERNANCE_SCORE_ARGS[@]}"
fi

QUALITY_GATE_NOTIFY_ARGS=(
    scripts/quality_gate_notify.py
    --api-base "$QUALITY_GATE_API_BASE"
    --max-versions "$QUALITY_GATE_MAX_VERSIONS"
    --high-skip-threshold "$QUALITY_GATE_HIGH_SKIP_THRESHOLD"
    --max-avg-skip-rate "$QUALITY_GATE_MAX_AVG_SKIP_RATE"
    --min-candidate-pairs "$QUALITY_GATE_MIN_CANDIDATE_PAIRS"
    --runtime-profile "$RUNTIME_PROFILE"
    --operator "$OPERATOR_NAME"
    --retries "$QUALITY_GATE_NOTIFY_RETRIES"
    --spool-dir "$QUALITY_GATE_NOTIFY_SPOOL_DIR"
    --enqueue-on-failure
)

if [[ -n "$QUALITY_GATE_WEBHOOK_URL" ]]; then
    QUALITY_GATE_NOTIFY_ARGS+=(--webhook-url "$QUALITY_GATE_WEBHOOK_URL")
fi

if [[ "$QUALITY_GATE_NOTIFY_REQUIRED" == "1" ]]; then
    run_step quality_gate_notify "Quality gate external notification" "$PYTHON_BIN" -u "${QUALITY_GATE_NOTIFY_ARGS[@]}"
else
    QUALITY_GATE_NOTIFY_ARGS+=(--allow-missing-webhook --enqueue-on-missing-webhook --succeed-on-enqueue)
    run_optional_step quality_gate_notify "Quality gate external notification (best-effort)" "$PYTHON_BIN" -u "${QUALITY_GATE_NOTIFY_ARGS[@]}"
fi

run_step review_api "Pipeline review API regression" "$PYTEST_BIN" tests/test_pipeline_review_api.py
run_step matrix_model_ops "Matrix model ops regression" "$PYTEST_BIN" tests/test_matrix_model_ops_api.py
run_step outputs_api "Outputs API regression" "$PYTEST_BIN" tests/test_outputs_api.py
run_step document_outcomes_api "Document outcomes API regression" "$PYTEST_BIN" tests/test_document_pipeline_outcomes_api.py
run_step aux_routes "Aux routes regression" "$PYTEST_BIN" tests/test_aux_api_mounts.py
run_step kb_integration "KB integration regression" env CRIN_INTEGRATION_POSTGRES_URL="$INTEGRATION_POSTGRES_URL" "$PYTEST_BIN" tests/test_kb_integration_postgres.py
ensure_log_has_no_skips kb_integration "KB integration regression"

echo
echo "Release-ready verification pack completed successfully."
echo "Artifacts saved to: $OUT_DIR"