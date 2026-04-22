# Clin-rec

Зависимости фиксируются через [`uv.lock`](uv.lock) (`uv sync`).

## Current Release Docs

- `PRD_CR_Intelligence_Platform_v1_6.md`: текущий продуктовый contract для transition к release-ready MVP
- `TZ_CR_Intelligence_Platform_v1_5.md`: текущий технический tranche release hardening
- `RUNBOOK_RUNTIME_PROFILE.md`: runtime profile, smoke semantics и release verification sequence
- `docs/RELEASE_READY_CHECKLIST.md`: операторский go/no-go checklist для MVP release decision
- `docs/RELEASE_REHEARSAL_2026-04-23.md`: current clean full-pack rehearsal record для compose-backed runtime после raw-artifact access и model-health fix
- `docs/RELEASE_SUMMARY_2026-04-23.md`: current clean full-pack go/no-go summary для rehearsal 2026-04-23
- `docs/RELEASE_REHEARSAL_2026-04-22.md`: clean full-pack rehearsal record для текущего compose-backed runtime
- `docs/RELEASE_SUMMARY_2026-04-22.md`: clean full-pack go/no-go summary для rehearsal 2026-04-22
- `docs/RELEASE_REHEARSAL_2026-04-21.md`: historical rehearsal record с поэтапной историей фиксов и закрытия blocker-ов
- `docs/RELEASE_SUMMARY_2026-04-21.md`: historical composite go/no-go summary для предыдущего release cycle
- `DOD_MVP.md`: baseline acceptance floor

## VS Code Tasks

- `UI Stack Up`: поднимает docker-compose runtime для локального UI/API тестирования
- `UI Stack Down`: останавливает локальный docker-compose runtime после тестирования
- `UI Stack Status`: показывает статус контейнеров и проброшенные порты текущего docker-compose runtime
- `UI Stack Health`: быстро проверяет `GET /health` и доступность Streamlit UI после старта стека
- `UI Stack Logs`: печатает последние логи `app`, `streamlit` и `worker` для быстрого UI/runtime debug
- `Structural Smoke`: быстрый entrypoint для runtime/profile validation, включая worker-backed memo/output completion
- `Quality Smoke`: entrypoint для content/downstream quality checks
- `Release Ready Check`: полный release pack через `scripts/release_ready_check.sh`
- `Release Late-Stage Rerun`: быстрый rerun regression-only path после уже зафиксированного green structural+quality smoke на том же runtime/profile
- Release-related tasks по умолчанию маркируют `RUNTIME_PROFILE=docker-compose-only` для seeded summary metadata.
- Для длинных queue delays используйте `SMOKE_POLL_TIMEOUT=360 bash scripts/release_ready_check.sh`.

## Local Runtime URLs

- UI: `http://localhost:8501`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- MinIO S3 API: `http://localhost:9010`
- MinIO console: `http://localhost:9011`

## Operator Surface

Проект теперь включает операторский контур для reviewer и scoring model lifecycle.

### Reviewer API

- `GET /review/queue`: очередь evidence на review, включая фильтр `document_version_id`
- `GET /review/stats`: агрегированные counts по review status
- `GET /review/history`: paginated audit trail с фильтрами `target_type` и `target_id`
- `POST /review`: approve, reject, override для `pair_evidence`
- `POST /review/bulk-approve`: массовое подтверждение evidence по списку ID

### Scoring Model API

- `GET /matrix/models/active`: текущая активная scoring model
- `GET /matrix/models/overview`: readiness overview по всем model versions
- `GET /matrix/models/{id}/summary`: summary + readiness по одной model version
- `GET /matrix/models/{id}/readiness`: release readiness checks
- `POST /matrix/models/{id}/refresh`: пересчёт pair-context scores и matrix cells
- `POST /matrix/models/{id}/activate`: активация model version
- `GET /matrix/models/diff`: diff между двумя model versions

### Outputs API

- `GET /outputs`: paginated list of output releases
- `GET /outputs/{id}`: detail for a single output release
- `POST /outputs/generate`: queue output generation
- `POST /outputs/memo`: queue memo generation alias
- `POST /outputs/file`: queue output filing by body payload
- `POST /outputs/file-back/{id}`: queue output filing alias with output ID in path

### Knowledge Base API

- `GET /kb/indexes/master`: KB master index or stub payload
- `GET /kb/artifacts`: paginated artifact list
- `GET /kb/artifacts/{id}`: artifact detail
- `GET /kb/entities`: paginated entity list
- `GET /kb/claims`: paginated claim list
- `GET /kb/conflicts`: grouped KB conflicts
- `POST /kb/compile`: queue KB compilation
- `POST /kb/lint`: queue KB lint

### Task Status API

- `GET /tasks/{task_id}`: Celery task state for UI polling, optionally with result payload

### Admin UI

Streamlit UI в `app/ui/app.py` поддерживает:

- reviewer queue со stats, фильтром по document version, bulk approve и history filter
- scoring model readiness overview, active model view, refresh, activate и version diff
- knowledge base page со списком artifacts/entities, conflict view, compile и lint actions
- task status page для polling queued background jobs
- outputs page со списком output releases, queue generation и file-back workflow
