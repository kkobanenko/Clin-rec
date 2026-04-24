#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
API_URL="${API_URL:-http://127.0.0.1:8000/health}"
UI_URL="${UI_URL:-http://127.0.0.1:8501}"
MIN_DISK_KB="${MIN_DISK_KB:-2097152}" # 2 GiB

log() {
    echo "[PILOT_PREFLIGHT] $*"
}

fail() {
    log "FAIL: $*"
    exit 1
}

check_command() {
    local cmd="$1"
    command -v "$cmd" >/dev/null 2>&1 || fail "required command not found: $cmd"
}

check_compose_config() {
    log "Check docker compose config"
    docker compose -f "$ROOT_DIR/docker-compose.yml" config >/dev/null
}

check_env_file() {
    log "Check required env vars in .env"
    [[ -f "$ENV_FILE" ]] || fail ".env file missing: $ENV_FILE"

    local required_vars=(
        CRIN_DATABASE_URL
        CRIN_DATABASE_URL_SYNC
        CRIN_CELERY_BROKER_URL
        CRIN_CELERY_RESULT_BACKEND
        CRIN_REDIS_URL
        CRIN_S3_ENDPOINT_URL
        CRIN_S3_ACCESS_KEY
        CRIN_S3_SECRET_KEY
        CRIN_S3_BUCKET
    )

    for var_name in "${required_vars[@]}"; do
        if ! rg -n "^${var_name}=" "$ENV_FILE" >/dev/null 2>&1; then
            fail "missing env var in .env: ${var_name}"
        fi
    done
}

check_disk_space() {
    log "Check free disk space"
    local available
    available="$(df -Pk "$ROOT_DIR" | awk 'NR==2 {print $4}')"
    [[ -n "$available" ]] || fail "unable to read free disk space"
    if (( available < MIN_DISK_KB )); then
        fail "low disk space: ${available}KB available, need >= ${MIN_DISK_KB}KB"
    fi
}

check_containers_running() {
    log "Check required containers running"
    local required=(crin_postgres crin_redis crin_minio crin_app crin_streamlit)
    for name in "${required[@]}"; do
        docker ps --format '{{.Names}}' | rg -x "$name" >/dev/null 2>&1 || fail "container not running: $name"
    done
}

check_postgres() {
    log "Check Postgres availability"
    docker exec crin_postgres pg_isready -U crplatform >/dev/null
}

check_redis() {
    log "Check Redis availability"
    docker exec crin_redis redis-cli ping | rg -x "PONG" >/dev/null 2>&1 || fail "redis ping failed"
}

check_minio() {
    log "Check MinIO availability"
    curl -fsS "http://127.0.0.1:9010/minio/health/live" >/dev/null || fail "minio health endpoint failed"
}

check_api_ui() {
    log "Check API and UI availability"
    curl -fsS "$API_URL" >/dev/null || fail "api health check failed: $API_URL"
    curl -fsS "$UI_URL" >/dev/null || fail "ui check failed: $UI_URL"
}

check_bucket_exists() {
    log "Check MinIO bucket directory exists in container data"
    docker exec crin_minio sh -lc 'test -d /data/cr-artifacts' || fail "bucket directory not found in minio data: /data/cr-artifacts"
}

check_migrations_current() {
    log "Check alembic current revision equals head"
    [[ -x "$PYTHON_BIN" ]] || fail "python not found: $PYTHON_BIN"

    local current_rev
    local head_rev

    current_rev="$($PYTHON_BIN -m alembic -c "$ROOT_DIR/alembic.ini" current 2>/dev/null | awk 'NR==1 {print $1}')"
    head_rev="$($PYTHON_BIN -m alembic -c "$ROOT_DIR/alembic.ini" heads 2>/dev/null | awk 'NR==1 {print $1}')"

    [[ -n "$current_rev" ]] || fail "unable to read alembic current revision"
    [[ -n "$head_rev" ]] || fail "unable to read alembic head revision"

    if [[ "$current_rev" != "$head_rev" ]]; then
        fail "alembic mismatch: current=$current_rev head=$head_rev"
    fi
}

main() {
    log "Start pilot preflight"
    check_command docker
    check_command curl
    check_command rg

    cd "$ROOT_DIR"

    check_compose_config
    check_env_file
    check_disk_space
    check_containers_running
    check_postgres
    check_redis
    check_minio
    check_api_ui
    check_bucket_exists
    check_migrations_current

    log "PASS: pilot preflight completed"
}

main "$@"
