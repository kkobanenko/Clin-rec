# TZ v3.1 — Quality Gate Queue Observability

## 1. Goal

Добавить операционную наблюдаемость backlog-очереди quality gate notifications.

## 2. Baseline

На старте tranche уже были:

1. queue-backed notifier fallback;
2. drain CLI;
3. release workflow queue wiring;
4. tests for delivery fallback and drain.

## 3. Technical Objective

Реализовать:

1. queue status service;
2. queue status outputs API (json/markdown);
3. queue status UI section;
4. endpoint/service test coverage.

## 4. Work Packages

### WP-1. Queue Status Service (DELIVERED)

Файл: [app/services/quality_gate_queue_status.py](app/services/quality_gate_queue_status.py)

Сделано:

- queue_size/age/size aggregates;
- per-item summaries;
- verdict counters;
- markdown rendering.

Acceptance criteria:

1. missing spool dir handled as empty queue;
2. invalid JSON queue files marked distinctly;
3. max_items preview limit respected.

### WP-2. API Endpoints (DELIVERED)

Файл: [app/api/outputs.py](app/api/outputs.py)

Сделано:

- `GET /outputs/quality-gate/queue-status`;
- `GET /outputs/quality-gate/queue-status/markdown`.

Acceptance criteria:

1. JSON and markdown responses available;
2. max_items/spool_dir parameters supported;
3. additive compatibility preserved.

### WP-3. UI Integration (DELIVERED)

Файл: [app/ui/app.py](app/ui/app.py)

Сделано:

- queue metrics panel;
- queue items table;
- markdown queue status loader.

Acceptance criteria:

1. operator sees queue backlog and age;
2. empty queue handled gracefully;
3. markdown view available.

### WP-4. Tests (DELIVERED)

Файлы:

- [tests/test_quality_gate_queue_status.py](tests/test_quality_gate_queue_status.py)
- [tests/test_outputs_api.py](tests/test_outputs_api.py)

Validation pack:

```bash
.venv/bin/pytest -q tests/test_quality_gate_queue_status.py tests/test_outputs_api.py tests/test_quality_gate_delivery_queue.py tests/test_quality_gate_notify_drain.py tests/test_quality_gate_notify.py tests/test_quality_gate_check.py tests/test_quality_gate.py
```

Observed result:

- `61 passed`.

## 5. Constraints

1. additive-only changes;
2. no breakage in existing outputs contracts;
3. no changes to JSON-first canonical ingestion behavior.

## 6. Acceptance

Tranche accepted when:

1. service/API/UI queue status surfaces merged;
2. tests green;
3. docs updated (analysis/plan/PRD/TZ).
