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

5. Quality smoke semantics for manual evaluation readiness
- Baseline structural smoke remains sufficient for MVP lifecycle acceptance.
- A run is not considered quality-ready for manual document evaluation unless at least one valid document produces non-empty normalized content (`sections` and `fragments`) or the system emits an explicit degraded/failed outcome with diagnostic reason.
- A run with `discovered_count > 0` and empty normalized content for all checked documents must not be treated as quality-green.

6. Data/API consistency
- Registry is idempotent on repeated sync.
- `/documents`, `/documents/{id}/content`, `/documents/{id}/fragments` return mutually consistent document-version data.

7. Runtime dependencies
- Worker runtime contains required dependencies, including sync PostgreSQL driver for sync engine (`psycopg2-binary` or equivalent).

8. Operational safety
- Docker and port operations comply with `ISOLATION_POLICY.md` and remain limited to `crin_*` resources.

9. Quality outcome observability
- Degraded or failed content-processing cases must be diagnosable through stage-level status, event, or reason metadata rather than appearing as silent success.

## Phase 2 — Knowledge compilation tranche (non-blocking for baseline smoke)

Baseline критерии §1–§9 достаточны для зелёного structural smoke корпуса и pipeline. Следующий объём приёмки соответствует PRD §13 (MVP foundation KB) и TZ v1.3 ([TZ_CR_Intelligence_Platform_v1_2_kb.md](TZ_CR_Intelligence_Platform_v1_2_kb.md)): миграции и модели по §7.7–§7.11 и §7.15, endpoints §17 для `/kb/*` и `/outputs/*`, фоновые задачи §19 (`compile_kb`, `lint_kb`, и др.), минимальные UI-элементы §21 по мере появления backend. Конкретные PR и порядок — по плану спринтов TZ §24; до закрытия Phase 2 отсутствие этих маршрутов в коде не считается регрессией baseline DoD.

Quality-ready переход сверх baseline DoD фиксируется в [PRD_CR_Intelligence_Platform_v1_5.md](PRD_CR_Intelligence_Platform_v1_5.md) и [TZ_CR_Intelligence_Platform_v1_4.md](TZ_CR_Intelligence_Platform_v1_4.md).
