# Technical Specification v1.7 — CR Intelligence Platform

Status: current proposed TZ after `Clin-rec-v2.zip` review  
Stage: `release-ready MVP -> pilot hardening`  
Date: 2026-04-25

## 1. Purpose

This technical specification defines the next implementation tranche required to move the current release-ready MVP into a controlled internal pilot.

The goal is not to rebuild the platform. The goal is to close pilot-hardening gaps.

## 2. Existing Architecture

Keep the existing architecture:

- FastAPI backend
- Celery worker
- Redis broker/result backend
- PostgreSQL database
- Alembic migrations
- MinIO/S3 artifact storage
- Streamlit operator UI
- Docker Compose local/pilot runtime

## 3. Runtime Profile

Selected pilot profile:

```text
pilot-compose-local
```

Expected services:

| Service | Container | Port |
| --- | --- | --- |
| API | `crin_app` | `8000` |
| Worker | `crin_worker` | internal |
| Streamlit | `crin_streamlit` | `8501` |
| Postgres | `crin_postgres` | `5433:5432` |
| Redis | `crin_redis` | `6380:6379` |
| MinIO | `crin_minio` | `9010:9000`, `9011:9001` |

## 4. Required Workstreams

## 4.1 Output Release Governance

### Problem

Outputs can be generated and reviewed, but pilot-grade release transition is not yet strict enough.

### Required Implementation

Add explicit release operation:

```text
POST /outputs/{id}/release
```

### Rules

- Missing output: `404`.
- `pending_review` output: cannot release.
- `rejected` output: cannot release.
- `approved` output: can become `released`.
- legacy `accepted` may be treated as approved.
- response returns normalized status.

### Data Requirements

If existing model has no dedicated release fields, add minimally invasive fields only if needed:

- `released_at`
- `released_by`

Implementation note for current tranche:

- `released_at` is persisted in `output_release`.
- `released_by` is currently persisted in `output_release.scope_json.release_audit.released_by`
  to avoid non-essential schema migration in this pilot-hardening slice.

If migration is required, create new Alembic revision.

### Tests

Add/extend:

- `tests/test_outputs_api.py`
- `tests/test_output_memo.py`

Required cases:

- cannot release pending output
- cannot release rejected output
- can release approved output
- released output appears in list/detail as `released`
- legacy accepted status is normalized safely

## 4.2 Discovery Completeness Reporting

### Problem

Smoke discovery proves runtime path, not full source coverage.

### Required Implementation

Ensure every pipeline/discovery run stores a structured report:

```json
{
  "discovery_strategy_report": {
    "mode": "smoke",
    "strategy": "api|playwright_fallback|manual|mixed",
    "api_attempted": true,
    "api_status": "success|failed|skipped",
    "fallback_used": false,
    "limit_applied": true,
    "source_count": 5,
    "completeness_claim": "smoke_only"
  }
}
```

Allowed `completeness_claim` values:

- `smoke_only`
- `partial_corpus`
- `full_corpus_unverified`
- `full_corpus_verified`

### API Requirement

Expose the report either in existing pipeline run detail or via:

```text
GET /pipeline/{run_id}/discovery-report
```

### Tests

Add/extend:

- `tests/test_discovery.py`
- `tests/test_source_validation.py`
- `tests/test_pipeline_stages.py`

## 4.3 Backup and Restore Runbook

### Problem

Pilot runtime has persistence but lacks a canonical backup/restore procedure.

### Required Deliverable

Create:

```text
docs/BACKUP_RESTORE_PILOT_v1.md
```

Required sections:

- backup Postgres
- restore Postgres
- backup MinIO artifacts
- restore MinIO artifacts
- verification after restore
- dangerous commands
- operator checklist

### Optional Scripts

Optional helper scripts may be added later:

- `scripts/backup_pilot.sh`
- `scripts/restore_pilot.sh`

Do not add restore automation until manual procedure is validated.

## 4.4 API Key Auth Pilot Minimum

### Current Implementation

The project already includes:

- `CRIN_API_AUTH_ENABLED`
- `CRIN_API_KEY`
- `require_api_key`
- route-level protection for non-health routers

### Required Hardening

1. Ensure `.env.example` contains:

```env
CRIN_API_AUTH_ENABLED=false
CRIN_API_KEY=
```

2. Ensure tests cover:

- auth disabled
- auth enabled + no header
- auth enabled + wrong header
- auth enabled + correct header
- auth enabled + empty configured key -> 503
- `/health` open

3. Ensure Streamlit internal API calls can pass:

```text
X-CRIN-API-Key: <key>
```

## 4.5 KB Lint Severity Policy

### Problem

KB lint exists but needs operator-grade severity and recommended action.

### Required Schema

Each lint issue should expose:

```json
{
  "code": "missing_provenance",
  "severity": "warning",
  "message": "Human-readable explanation",
  "recommended_action": "Review source artifact linkage",
  "artifact_id": 123,
  "entity_id": null,
  "claim_id": null
}
```

Allowed severities:

- `info`
- `warning`
- `error`
- `blocker`

### Release Gate Rule

- `blocker`: pilot release blocked
- `error`: release requires explicit owner waiver
- `warning`: allowed with documented residual risk
- `info`: allowed

### Tests

Add/extend:

- `tests/test_knowledge_lint.py`
- `tests/test_knowledge_compile.py`
- `tests/test_kb_api.py`

## 4.6 Pilot Preflight Preservation

### Current Implementation

`script/pilot_preflight.sh` exists and checks:

- Docker Compose config
- env vars
- disk space
- required containers
- Postgres
- Redis
- MinIO
- API
- UI
- bucket directory
- Alembic current/head

### Required Rule

Do not weaken this script. Add checks only if they are deterministic and fast.

### Optional Improvements

- check API auth mode consistency
- check MinIO bucket through S3 API, not only container directory
- check backup directory writability

## 5. Database/Migration Rules

1. Any schema change requires a new Alembic migration.
2. Do not edit old migrations unless fixing syntax before deployment.
3. Migration must work from empty database.
4. Migration must work from current pilot database.
5. Add tests if model behavior changes.

## 6. API Compatibility Rules

1. Do not remove existing endpoints.
2. Do not change response fields incompatibly.
3. Normalize legacy statuses, but keep old rows readable.
4. Return clear HTTP errors:
   - 400 for invalid request
   - 401 for invalid auth
   - 404 for missing object
   - 409 for invalid state transition
   - 503 for auth misconfiguration

## 7. UI Requirements

Keep Streamlit.

Required UI additions only if backend feature is added:

- Output detail should show status and release eligibility.
- If release endpoint is added, add operator button only for approved outputs.
- KB lint page should show severity and recommended action.
- Discovery report should be visible from pipeline run detail.

Do not perform a UI redesign.

## 8. Release Verification

Before declaring done:

```bash
bash scripts/pilot_preflight.sh
RUNTIME_PROFILE=pilot-compose-local bash scripts/release_ready_check.sh
```

Then run targeted tests:

```bash
.venv/bin/pytest -q tests/test_auth.py tests/test_api_health.py
.venv/bin/pytest -q tests/test_outputs_api.py tests/test_output_memo.py
.venv/bin/pytest -q tests/test_discovery.py tests/test_source_validation.py tests/test_pipeline_stages.py
.venv/bin/pytest -q tests/test_knowledge_compile.py tests/test_knowledge_lint.py tests/test_knowledge_conflicts.py tests/test_kb_integration_postgres.py
.venv/bin/pytest -q tests/test_ui_i18n.py tests/test_ui_app.py tests/test_ui_regression_batches.py
```

## 9. Documentation Requirements

Update or create:

- `docs/IMPLEMENTATION_NOTES.md`
- `docs/RELEASE_SUMMARY_2026-04-25.md`
- `docs/BACKUP_RESTORE_PILOT_v1.md`
- `docs/RELEASE_READY_CHECKLIST.md`
- `README.md`

Do not overwrite old release summaries.

## 10. Acceptance Criteria

The tranche is accepted when:

1. Pilot preflight passes.
2. Release pack passes.
3. Output release transition is implemented.
4. Discovery report has explicit completeness claim.
5. Backup/restore runbook exists.
6. Auth minimum is documented and tested.
7. KB lint issues have severity and recommended action.
8. New release summary exists.
9. README points to current canonical documents.

## 11. Explicit Non-Goals

Do not implement in this tranche:

- OAuth
- RBAC
- multi-tenant architecture
- Kubernetes
- billing
- public customer UI
- full-text clinical search product
- medical/legal final approval system
- replacement of Streamlit

## 12. Final Technical Direction

The platform is technically credible as a pilot candidate. The next work is hardening, verification and governance, not architectural replacement.
