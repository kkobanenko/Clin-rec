# Clin-rec

Зависимости фиксируются через [`uv.lock`](uv.lock) (`uv sync`).

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
