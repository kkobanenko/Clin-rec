# Runtime Profile Runbook

## Purpose

This runbook defines how to run API and worker in a consistent runtime profile and verify queue routing before running sync jobs.

## Allowed Profiles

- `host-only`: API + worker are both started on host.
- `docker-compose-only`: API + worker are both started from this repository's `docker-compose.yml`.

Do not mix profiles for one active run.

## Quick Checklist

1. Confirm working directory:
```bash
pwd
# expected: /home/kobanenkokn/Clin-rec
```

2. Confirm isolation scope before Docker actions:
```bash
docker compose ps
docker ps -a --filter "label=com.docker.compose.project=crin" --format "table {{.Names}}\t{{.Status}}"
```

3. Confirm broker/result backend alignment:
- API and worker must use same values for:
  - `CRIN_CELERY_BROKER_URL`
  - `CRIN_CELERY_RESULT_BACKEND`

4. Run smoke only after alignment is confirmed.

## Profile A: host-only

### Start API
```bash
/home/kobanenkokn/Clin-rec/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start worker
```bash
/home/kobanenkokn/Clin-rec/.venv/bin/celery -A app.workers.celery_app worker -l info -Q discovery,probe,fetch,normalize,extract,score,reindex
```

### Verify broker from process env (optional)
```bash
ss -ltnp | rg ':8000'
ps -ww -p <uvicorn_pid> -o pid,ppid,cmd
tr '\0' '\n' < /proc/<uvicorn_pid>/environ | rg '^CRIN_CELERY_BROKER_URL|^CRIN_CELERY_RESULT_BACKEND|^PWD'
```

## Profile B: docker-compose-only

Публикация API на **хосте: `8008`** → контейнер `app` слушает `8000` (см. `ISOLATION_POLICY.md`). Swagger: `http://127.0.0.1:8008/docs`.

### Start stack
```bash
docker compose up -d --build app worker
```

### Verify containers
```bash
docker logs --tail=80 crin_app
docker logs --tail=80 crin_worker
curl -sSf http://127.0.0.1:8008/health
```

### Verify task consumption
```bash
docker logs --tail=200 crin_worker | rg 'Task app.workers.tasks.discovery.run_full_sync|received|succeeded'
```

## Smoke Execution

```bash
/home/kobanenkokn/Clin-rec/.venv/bin/python scripts/e2e_smoke.py
```

Pass criteria:
- `/sync/full` returns `202` with `run_id`
- `/runs/{id}` reaches `completed` (after possible `pending/running`)
- `stats_json` contains minimum required fields: `discovery_service_version`, `run_type`, `wall_time_seconds`, `total_discovered`, `duplicates_detected`, `coverage_percent`
- `/documents` returns consistent records
- `completed` with `discovered_count = 0` is valid for smoke when lifecycle and observability checks pass

## Troubleshooting

### Symptom: run stays `pending`
Possible cause:
- Worker not running or not connected to same broker.

Checks:
```bash
ps -ef | rg 'celery -A app.workers.celery_app worker' | rg -v rg
docker logs --tail=120 crin_worker
```

### Symptom: worker crashes on startup with psycopg2 error
Possible cause:
- Missing sync PostgreSQL driver.

Action:
- Ensure dependency includes `psycopg2-binary`.
- Rebuild runtime environment (venv or image) and restart worker.

### Symptom: app container fails to start (port binding)
Possible cause:
- Host port **8008** already in use (published API), or Docker cannot bind.

Checks:
```bash
ss -ltnp | rg ':8008'
docker compose ps
```

Resolution:
- Free **8008** or change the host side in `docker-compose.yml` (`\"8010:8000\"` etc.). Внутри сети compose по-прежнему `http://app:8000`.

## Safety Notes

- Follow `ISOLATION_POLICY.md` for all container and port operations.
- Do not operate on non-`crin_*` containers.
