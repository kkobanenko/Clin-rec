# RUNBOOK PILOT RUNTIME PROFILE

## Purpose

This runbook defines single pilot runtime profile and repeatable preflight for pilot-stage release verification.

## Pilot Profile ID

- Name: `pilot-compose-local`
- Base: `docker-compose-only`
- Scope: single-host pilot runtime for internal operators

## Topology

- API container: `crin_app` (`8000:8000`)
- Worker container: `crin_worker`
- Streamlit container: `crin_streamlit` (`8501:8501`)
- Postgres container: `crin_postgres` (`5433:5432`)
- Redis container: `crin_redis` (`6380:6379`)
- MinIO container: `crin_minio` (`9010:9000`, `9011:9001`)

## Persistence Decisions

- Postgres: persistent volume `crin_pg_data` (required)
- MinIO/S3: persistent volume `crin_minio_data` (required)
- Redis: ephemeral acceptable for pilot runtime, not source of truth

## Backup Paths

- Postgres logical backup (example target): `var/backups/postgres/`
- MinIO artifact backup (example target): `var/backups/minio/`
- Release evidence bundle: `.artifacts/release_checks/<timestamp>`

## Required Environment

Minimum env vars for pilot profile:

- `CRIN_DATABASE_URL`
- `CRIN_DATABASE_URL_SYNC`
- `CRIN_CELERY_BROKER_URL`
- `CRIN_CELERY_RESULT_BACKEND`
- `CRIN_REDIS_URL`
- `CRIN_S3_ENDPOINT_URL`
- `CRIN_S3_ACCESS_KEY`
- `CRIN_S3_SECRET_KEY`
- `CRIN_S3_BUCKET`

Auth controls for non-local pilot deployment:

- `CRIN_API_AUTH_ENABLED=true` enables API key enforcement on all non-health endpoints.
- `CRIN_API_KEY=<strong-random-key>` sets required key value.
- Clients must pass header `X-CRIN-API-Key: <key>`.
- `/health` remains unauthenticated by design for probes.
- Streamlit internal calls may use the same `CRIN_API_KEY` via container env.

Key generation example:

```bash
openssl rand -hex 32
```

Current compose defaults should resolve to:

- broker: `redis://redis:6379/0`
- result backend: `redis://redis:6379/1`
- sync DB: `postgresql://crplatform:crplatform@postgres:5432/crplatform`
- bucket: `cr-artifacts`

## Restart Policy

Operator sequence for controlled restart:

```bash
docker compose down
docker compose up -d
```

Use only this repository compose project (`crin`).

## Ports

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`
- Postgres host port: `5433`
- Redis host port: `6380`
- MinIO S3 API: `9010`
- MinIO console: `9011`

## Preflight Command

Run before release pack:

```bash
bash scripts/pilot_preflight.sh
```

Preflight verifies:

1. `docker compose config` validity
2. required env vars presence
3. service availability (Postgres/Redis/MinIO/API/UI)
4. free disk threshold
5. MinIO bucket path present in container
6. alembic current revision equals head

## Release Verification

After successful preflight:

```bash
bash scripts/release_ready_check.sh
```

Release summary must explicitly include runtime profile used.

## Failure Policy

If preflight fails:

- do not start release-ready check;
- fix failed item;
- re-run preflight;
- only then run release pack.

## Notes

- This runbook does not replace `RUNBOOK_RUNTIME_PROFILE.md`; it narrows one selected pilot profile.
- Latest validated full-pack evidence remains `docs/RELEASE_SUMMARY_2026-04-24.md` until new real rerun.
