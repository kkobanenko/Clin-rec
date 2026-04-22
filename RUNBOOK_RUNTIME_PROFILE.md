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

Recommended modes:
- `structural`: lifecycle, queue routing, `stats_json` contract, and mounted auxiliary operator routes.
- `quality`: includes content-layer validation plus downstream pair-evidence and matrix validation for manual evaluation readiness.

Structural pass criteria:
- `/sync/full` returns `202` with `run_id`
- `/runs/{id}` reaches `completed` (after possible `pending/running`)
- `stats_json` contains minimum required fields: `discovery_service_version`, `run_type`, `wall_time_seconds`, `total_discovered`, `duplicates_detected`, `coverage_percent`
- mounted operator routes answer successfully: `/outputs`, `/kb/indexes/master`, `/pipeline/storage-stages`
- task-status route answers for a freshly queued memo task via `/tasks/{task_id}`
- `/documents` returns consistent records
- `completed` with `discovered_count = 0` is valid for smoke when lifecycle and observability checks pass

Quality pass criteria for manual document evaluation:
- structural criteria already pass
- when `discovered_count > 0`, at least one checked document produces non-empty normalized content via `/documents/{id}/content` and `/documents/{id}/fragments`
- checked document also produces non-empty downstream pair evidence via `/matrix/pair-evidence`
- when a scoring model is active or activated by smoke, quality mode also validates `/matrix/cell`
- `matrix/cell.supporting_evidence_count` must not be smaller than the evidence returned for the checked pair
- if no document passes the content check, the run must be treated as degraded or failed for quality purposes, not as quality-green
- degraded or failed cases should be explainable through stage outcome and reason metadata when available

Operator rule:
- Use structural smoke for runtime/profile validation.
- Use quality smoke before asking analysts or reviewers to evaluate pipeline output on real documents.
- Use `/outputs` and the admin Outputs page to verify queued memo/output workflows are visible after runtime changes.
- Use the admin Tasks page when you need to inspect task ids returned by KB or output workflows.

## Release Verification Sequence

Use this sequence when evaluating whether the current build is release-ready for MVP purposes.

1. Confirm one active runtime profile and broker/result-backend alignment.
2. Run structural smoke and stop immediately if it fails.
3. Run quality smoke and stop immediately if it fails.
4. Run targeted API regression for operator surfaces: review, matrix model operations, outputs, and auxiliary mounts.
5. Run downstream verification for evidence/matrix and KB/output workflows.
6. Record a short go/no-go summary with residual risks and classify the build as `release-ready` or `blocked`.

If quality runs spend a long time in `pending`, increase the release-runner poll window, for example:

```bash
SMOKE_POLL_TIMEOUT=360 bash scripts/release_ready_check.sh
```

For `docker-compose-only` runtime, the release runner defaults `CRIN_INTEGRATION_POSTGRES_URL` to:

```bash
postgresql://crplatform:crplatform@localhost:5433/crplatform
```

If structural and quality smoke are already green on the same runtime/profile, use a late-stage rerun to repeat only the remaining regression gates:

```bash
SKIP_STRUCTURAL_SMOKE=1 SKIP_QUALITY_SMOKE=1 bash scripts/release_ready_check.sh
```

Each runner invocation also seeds `release_summary.md` with branch, commit, validation path and artifact-bundle metadata to speed up the final go/no-go writeup.

Interpretation rule:
- `structural` green means runtime and observability are valid.
- `quality` green means content-layer and downstream spot-checks are valid.
- `release-ready` requires structural green, quality green, targeted regression green, downstream verification green, and an explicit go/no-go review.

Documentation alignment:
- Product release contract: `PRD_CR_Intelligence_Platform_v1_6.md`
- Technical release-hardening tranche: `TZ_CR_Intelligence_Platform_v1_5.md`
- Operator checklist: `docs/RELEASE_READY_CHECKLIST.md`
- Baseline acceptance floor: `DOD_MVP.md`

VS Code task entrypoints:
- `UI Stack Up`
- `UI Stack Status`
- `UI Stack Health`
- `UI Stack Logs`
- `UI Stack Down`
- `Structural Smoke`
- `Quality Smoke`
- `Release Ready Check`
- `Release Late-Stage Rerun` (only after green structural+quality smoke on the same runtime/profile)

Local UI/API surface after `UI Stack Up`:
- UI: `http://localhost:8501`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

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

### Symptom: run is `completed` but content is empty
Possible causes:
- Source is an HTML shell or incomplete representation.
- PDF endpoint returned non-PDF payload.
- Normalize exhausted HTML/PDF paths without usable text.

Checks:
```bash
/home/kobanenkokn/Clin-rec/.venv/bin/python scripts/e2e_smoke.py
curl -s http://localhost:8000/documents/<id>/content | jq
curl -s http://localhost:8000/documents/<id>/fragments | jq
```

Resolution:
- Treat the run as structural-green but quality-red until content-layer issue is diagnosed.
- Inspect source validation and normalize-stage diagnostics before manual review.

## Safety Notes

- Follow `ISOLATION_POLICY.md` for all container and port operations.
- Do not operate on non-`crin_*` containers.
