# Definition of Done (MVP)

This document is the canonical Definition of Done for MVP baseline acceptance.
PRD and TZ must reference this file and must not duplicate conflicting DoD lists.

## DoD Criteria

1. Runtime profile consistency
- System runs in one selected profile only: `host-only` or `docker-compose-only`.
- API and worker use identical `CRIN_CELERY_BROKER_URL` and `CRIN_CELERY_RESULT_BACKEND`.

2. Pipeline run lifecycle
- `POST /sync/full` creates a run and polling continues through `pending` and `running` states.
- Run reaches terminal state: `completed` or `failed`.

3. Observability contract for completed runs
- Completed runs contain stage counters and `stats_json` with the minimum required fields:
  - `discovery_service_version`
  - `run_type`
  - `wall_time_seconds`
  - `total_discovered`
  - `duplicates_detected`
  - `coverage_percent`

4. Smoke validity semantics
- A completed run with `discovered_count = 0` is valid for smoke if lifecycle, queue routing, and observability contract checks pass.
- Smoke failure is structural/integration failure, not data-volume failure.

5. Data/API consistency
- Registry is idempotent on repeated sync.
- `/documents`, `/documents/{id}/content`, `/documents/{id}/fragments` return mutually consistent document-version data.

6. Runtime dependencies
- Worker runtime contains required dependencies, including sync PostgreSQL driver for sync engine (`psycopg2-binary` or equivalent).

7. Operational safety
- Docker and port operations comply with `ISOLATION_POLICY.md` and remain limited to `crin_*` resources.

## Phase 2 — Knowledge compilation tranche (non-blocking for baseline smoke)

Baseline критерии §1–§7 достаточны для зелёного smoke корпуса и pipeline. Следующий объём приёмки соответствует PRD §13 (MVP foundation KB) и TZ v1.3 ([TZ_CR_Intelligence_Platform_v1_2_kb.md](TZ_CR_Intelligence_Platform_v1_2_kb.md)): миграции и модели по §7.7–§7.11 и §7.15, endpoints §17 для `/kb/*` и `/outputs/*`, фоновые задачи §19 (`compile_kb`, `lint_kb`, и др.), минимальные UI-элементы §21 по мере появления backend. Конкретные PR и порядок — по плану спринтов TZ §24; до закрытия Phase 2 отсутствие этих маршрутов в коде не считается регрессией baseline DoD.
