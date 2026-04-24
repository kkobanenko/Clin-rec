# Backup / Restore Runbook — Pilot v1

Date: 2026-04-25
Scope: pilot-compose-local runtime

## 1. Safety Rules

- Stop write-heavy operations before backup when possible.
- Never run restore against a live pilot DB without explicit approval.
- Keep original backup files read-only after creation.
- Do not run destructive Docker volume commands unless recovery plan is confirmed.

## 2. Postgres Backup

```bash
mkdir -p var/backups/postgres
docker exec crin_postgres pg_dump -U crplatform -d crplatform > var/backups/postgres/crplatform_$(date +%Y%m%d_%H%M%S).sql
```

Verification:

```bash
ls -lh var/backups/postgres
head -n 5 var/backups/postgres/crplatform_*.sql
```

## 3. Postgres Restore (Dangerous)

Warning: this overwrites DB state.

```bash
docker exec -i crin_postgres psql -U crplatform -d crplatform < var/backups/postgres/<backup_file>.sql
```

After restore:

```bash
docker exec crin_postgres psql -U crplatform -d crplatform -c "SELECT now();"
```

## 4. MinIO Artifact Backup

```bash
mkdir -p var/backups/minio
docker run --rm -v crin_minio_data:/data -v "$PWD/var/backups/minio:/backup" busybox sh -lc 'tar czf /backup/minio_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .'
```

Verification:

```bash
ls -lh var/backups/minio
tar tzf var/backups/minio/minio_*.tar.gz | head -n 20
```

## 5. MinIO Artifact Restore (Dangerous)

Warning: this can overwrite existing artifacts.

```bash
docker run --rm -v crin_minio_data:/data -v "$PWD/var/backups/minio:/backup" busybox sh -lc 'tar xzf /backup/<minio_backup>.tar.gz -C /data'
```

## 6. Dangerous Commands (Use Only With Approval)

- `docker compose down -v`
- `docker volume rm crin_pg_data`
- `docker volume rm crin_minio_data`
- any `DROP DATABASE` / `TRUNCATE` on pilot data

## 7. Post-Restore Validation Checklist

Run in order:

```bash
bash scripts/pilot_preflight.sh
RUNTIME_PROFILE=pilot-compose-local bash scripts/release_ready_check.sh
```

Then confirm:

- API `/health` is reachable.
- Latest pipeline runs are readable.
- KB master index loads.
- Outputs and tasks endpoints are readable.

## 8. Operational Notes

- Keep backup and restore timestamps in release notes.
- Store backup artifacts outside container lifecycle directories when possible.
- Use immutable storage or off-host copy for long-term retention.
