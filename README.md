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

### Admin UI

Streamlit UI в `app/ui/app.py` поддерживает:

- reviewer queue со stats, фильтром по document version, bulk approve и history filter
- scoring model readiness overview, active model view, refresh, activate и version diff
