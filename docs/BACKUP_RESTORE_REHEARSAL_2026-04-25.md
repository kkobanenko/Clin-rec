# Backup / Restore Rehearsal 2026-04-25

## Scope

- Runtime profile: `pilot-compose-local`
- Commit: `3bbe07a`
- Goal: verify backup procedures for Postgres and MinIO artifacts
- Restore: deferred (no explicit human approval to run restore on active pilot data)

## Executed Commands

```bash
mkdir -p var/backups/postgres var/backups/minio
docker exec crin_postgres pg_dump -U crplatform -d crplatform > var/backups/postgres/crplatform_20260425_015504.sql
docker run --rm -v crin_minio_data:/data -v "$PWD/var/backups/minio:/backup" busybox sh -lc 'tar czf /backup/minio_20260424_225505.tar.gz -C /data .'
```

## Verification Commands

```bash
ls -lh var/backups/postgres var/backups/minio
head -n 5 var/backups/postgres/crplatform_20260425_015504.sql
tar tzf var/backups/minio/minio_20260424_225505.tar.gz | head -n 20
```

## Verification Results

- Postgres backup created:
  - `var/backups/postgres/crplatform_20260425_015504.sql`
  - size: ~1.4 MB
  - header check: valid PostgreSQL dump preamble present
- MinIO backup created:
  - `var/backups/minio/minio_20260424_225505.tar.gz`
  - archive listing opens successfully (`./` present)

## Notes

- Initial write failure was caused by ownership/permission mismatch under `var/`.
- Rehearsal unblocked by creating and chown-ing `var/backups/*` to local workspace UID/GID (`1001:1001`) using a one-shot Docker container.
- No restore command was run in this rehearsal cycle.

## Decision

- Backup rehearsal status: `pass` (backup + verification complete)
- Restore rehearsal status: `deferred` (requires explicit human approval and disposable data scope)
