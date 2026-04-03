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

### Start stack
```bash
docker compose up -d --build app worker
```

### Verify containers
```bash
docker logs --tail=80 crin_app
docker logs --tail=80 crin_worker
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

## KB compile, lint, matrix rebuild, статус Celery

| Действие | HTTP | Примечание |
| --- | --- | --- |
| Очередь полной перекомпиляции KB | `POST /kb/compile` | В ответе `task_id` (Celery `run_compile_kb`). |
| Очередь lint KB | `POST /kb/lint` | `task_id` для `lint_kb`. |
| Пересчёт scores и матрицы | `POST /matrix/rebuild` | Тело JSON: `{"model_version_id": <int>, "scope_type": "global"\|"disease"}`. Цепочка: `score_pairs` → `build_matrix`. Ответ `202` + `task_id`. |
| Опрос задачи (read-only) | `GET /tasks/{task_id}` | Поля `state`, `ready`; тело результата задачи не отдаётся. Для UI (Streamlit) — после POST сохранить `task_id` и опрашивать этот маршрут. |
| Список PairEvidence (обзор) | `GET /matrix/pair-evidence` | Query: `page`, `page_size`, опционально `document_version_id`, `molecule_from_id`, `molecule_to_id`, `review_status`. |

**Streamlit — вкладка Outputs (Sprint 7):** список и деталь `GET /outputs`, постановка `POST /outputs/memo` или `/outputs/generate`, filing `POST /outputs/file`, опрос задач `GET /tasks/{task_id}`. В Docker базовый URL API задаётся **`CRIN_STREAMLIT_API_BASE`** (в [docker-compose.yml](docker-compose.yml) для `streamlit`: `http://app:8000`).

**Streamlit — вкладка Matrix (Sprint 8, explorer):** блок **Pair evidence** вызывает `GET /matrix/pair-evidence` с теми же query-параметрами, что в таблице выше; история ревью — `GET /reviews` (ответ — JSON-массив).

**Pair evidence:** после успешного `extract_document` в worker вызывается `CandidateEngine.generate_pairs(version_id)` — появляются строки `pair_evidence` (см. `docs/STORAGE_STAGES.md`).

**Страницы МНН:** при `compile` для версии документа `KnowledgeCompileService` создаёт недостающие `entity_page` для `entity_registry` с `entity_type=molecule`, чтобы закрыть lint `missing_entity_page_molecule`.

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

### Symptom: app container fails to start on port 8000
Possible cause:
- Port conflict with host process.

Checks:
```bash
ss -ltnp | rg ':8000'
ps -ww -p <pid> -o pid,ppid,cmd
```

Resolution:
- Stop conflicting process or use a single selected profile.

## Safety Notes

- Follow `ISOLATION_POLICY.md` for all container and port operations.
- Do not operate on non-`crin_*` containers.
