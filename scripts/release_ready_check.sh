#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
PYTEST_BIN="${PYTEST_BIN:-$ROOT_DIR/.venv/bin/pytest}"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/.artifacts/release_checks/$TIMESTAMP}"
SUMMARY_TEMPLATE="$ROOT_DIR/docs/RELEASE_SUMMARY_TEMPLATE.md"
SUMMARY_FILE="$OUT_DIR/release_summary.md"
STRUCTURAL_SMOKE_ARGS=(scripts/e2e_smoke.py --mode structural)
QUALITY_SMOKE_ARGS=(scripts/e2e_smoke.py --mode quality)
STRUCTURAL_POLL_TIMEOUT="${STRUCTURAL_SMOKE_POLL_TIMEOUT:-${SMOKE_POLL_TIMEOUT:-}}"
QUALITY_POLL_TIMEOUT="${QUALITY_SMOKE_POLL_TIMEOUT:-${SMOKE_POLL_TIMEOUT:-}}"

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
fi

echo "Release artifacts directory: $OUT_DIR"
if [[ -f "$SUMMARY_FILE" ]]; then
    echo "Seeded summary template: $SUMMARY_FILE"
fi

run_step structural_smoke "Structural smoke" "$PYTHON_BIN" -u "${STRUCTURAL_SMOKE_ARGS[@]}"
run_step quality_smoke "Quality smoke" "$PYTHON_BIN" -u "${QUALITY_SMOKE_ARGS[@]}"
run_step review_api "Pipeline review API regression" "$PYTEST_BIN" tests/test_pipeline_review_api.py
run_step matrix_model_ops "Matrix model ops regression" "$PYTEST_BIN" tests/test_matrix_model_ops_api.py
run_step outputs_api "Outputs API regression" "$PYTEST_BIN" tests/test_outputs_api.py
run_step aux_routes "Aux routes regression" "$PYTEST_BIN" tests/test_aux_api_mounts.py
run_step kb_integration "KB integration regression" "$PYTEST_BIN" tests/test_kb_integration_postgres.py

echo
echo "Release-ready verification pack completed successfully."
echo "Artifacts saved to: $OUT_DIR"