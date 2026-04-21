#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
PYTEST_BIN="${PYTEST_BIN:-$ROOT_DIR/.venv/bin/pytest}"

run_step() {
    local title="$1"
    shift
    echo
    echo "==> ${title}"
    "$@"
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

run_step "Structural smoke" "$PYTHON_BIN" scripts/e2e_smoke.py structural
run_step "Quality smoke" "$PYTHON_BIN" scripts/e2e_smoke.py quality
run_step "Pipeline review API regression" "$PYTEST_BIN" tests/test_pipeline_review_api.py
run_step "Matrix model ops regression" "$PYTEST_BIN" tests/test_matrix_model_ops_api.py
run_step "Outputs API regression" "$PYTEST_BIN" tests/test_outputs_api.py
run_step "Aux routes regression" "$PYTEST_BIN" tests/test_aux_api_mounts.py
run_step "KB integration regression" "$PYTEST_BIN" tests/test_kb_integration_postgres.py

echo
echo "Release-ready verification pack completed successfully."