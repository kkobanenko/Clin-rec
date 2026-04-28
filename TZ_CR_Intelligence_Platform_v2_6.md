# TZ v2.6 — Candidate Diagnostics Aggregate Observability

## 1. Goal Of Tranche

Добавить операторский агрегированный слой candidate diagnostics поверх уже существующего extraction telemetry.

## 2. Baseline Assumption

На текущем head уже валидны:

1. JSON-first runtime pipeline;
2. Evidence diagnostics API и release evidence API;
3. Corpus quality service/API;
4. Candidate diagnostics в worker event logs (`candidate_skip_rate`, counters);
5. Streamlit operator UI pages (dashboard/documents/pipeline/matrix/reviews/outputs/kb/tasks).

## 3. Technical Objective

Реализовать:

1. новый сервис агрегации `pipeline_event_log` по candidate diagnostics;
2. новые outputs endpoints (JSON + Markdown report);
3. новый UI-блок на странице Outputs;
4. unit tests для сервиса и API.

## 4. Work Packages

### WP-1. Candidate Diagnostics Report Service (DELIVERED)

Файл: `app/services/candidate_diagnostics_report.py`

Сделано:

- dataclass-модели report и per-version diagnostics;
- агрегация recent extract success events;
- вычисление средних/максимальных skip-rate и high-skip counts;
- JSON/Markdown сериализация.

Acceptance criteria:

1. пустой корпус событий возвращает пустой report без ошибок;
2. skip-rate и counters корректно агрегируются по версиям;
3. отчёт содержит top-versions по skip-rate;
4. markdown содержит summary + top-table.

### WP-2. Outputs API Extensions (DELIVERED)

Файл: `app/api/outputs.py`

Сделано:

- `GET /outputs/candidate-diagnostics`;
- `GET /outputs/candidate-diagnostics/markdown`;
- корректный route priority перед `/{output_id}`.

Acceptance criteria:

1. оба endpoints отвечают 200 при валидном запросе;
2. endpoint JSON возвращает expected summary keys;
3. markdown endpoint возвращает `text/markdown`;
4. API расширение аддитивно.

### WP-3. Operator UI Candidate Diagnostics Panel (DELIVERED)

Файл: `app/ui/app.py` (page `Outputs`)

Сделано:

- controls: versions window, top-N, high-skip threshold;
- summary metrics блок;
- table with top high-skip versions;
- markdown report viewer.

Acceptance criteria:

1. UI получает JSON report и рендерит summary;
2. UI отображает список top versions;
3. markdown report доступен в интерфейсе;
4. ошибки API показываются без падения страницы.

### WP-4. Tests (DELIVERED)

Файлы:

- `tests/test_candidate_diagnostics_report.py`;
- `tests/test_outputs_api.py` (новые кейсы).

Acceptance criteria:

1. сервисные тесты покрывают empty/aggregate/filter/markdown;
2. API тесты покрывают JSON и markdown endpoints;
3. таргетированный pytest green.

## 5. Validation Pack

```bash
.venv/bin/pytest -q tests/test_candidate_diagnostics_report.py tests/test_outputs_api.py
```

Observed result:

- `24 passed`.

## 6. Constraints

1. Только additive changes.
2. Не ломать существующие outputs маршруты.
3. Не изменять контракт JSON-first обработки.
4. UI должен деградировать gracefully при сетевых ошибках.

## 7. Acceptance

Tranche принят, если:

1. оба новых outputs endpoints работают;
2. UI Diagnostics panel отображает данные;
3. pytest таргет-пакет зелёный;
4. route precedence не ломает `/{output_id}` семантику;
5. документация PRD/analysis/implementation plan обновлена.
