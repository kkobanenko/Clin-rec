# TZ v3.0 — Queue-Backed Quality Gate Delivery

## 1. Goal

Сделать внешний слой quality gate уведомлений устойчивым к временным отказам webhook через локальную spool-очередь и replay-механику.

## 2. Baseline

До начала tranche были доступны:

1. webhook notifier script;
2. release integration for notifier step;
3. best-effort/required delivery modes;
4. coverage for basic notifier behavior.

## 3. Technical Objective

Добавить:

1. file-backed queue utility module;
2. notifier fallback enqueue modes;
3. queue drain CLI;
4. release script queue-aware orchestration.

## 4. Work Packages

### WP-1. Queue Utility Module (DELIVERED)

Файл: [scripts/quality_gate_delivery_queue.py](scripts/quality_gate_delivery_queue.py)

Сделано:

- enqueue/list/load/remove primitives;
- JSON object validation;
- stable file naming for FIFO-like ordering.

Acceptance criteria:

1. enqueue creates file in spool dir;
2. load returns dict payload;
3. remove deletes delivered item.

### WP-2. Notifier Fallback Upgrade (DELIVERED)

Файл: [scripts/quality_gate_notify.py](scripts/quality_gate_notify.py)

Сделано:

- `--enqueue-on-failure`;
- `--enqueue-on-missing-webhook`;
- `--succeed-on-enqueue`;
- configurable `--spool-dir`.

Acceptance criteria:

1. delivery failure can enqueue payload;
2. missing webhook can enqueue in allowed mode;
3. policy supports success-on-enqueue in best-effort branch.

### WP-3. Drain CLI (DELIVERED)

Файл: [scripts/quality_gate_notify_drain.py](scripts/quality_gate_notify_drain.py)

Сделано:

- replay queued payloads to webhook;
- remove files on success;
- strict/soft-fail behavior.

Acceptance criteria:

1. successful replay removes queue files;
2. failure keeps file for future retry;
3. soft-fail mode returns 0 for best-effort pipelines.

### WP-4. Release Workflow Wiring (DELIVERED)

Файл: [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

- queue drain step before notify;
- optional-step execution for best-effort mode;
- queue-aware notifier flags and spool settings.

Acceptance criteria:

1. required mode remains blocking;
2. best-effort mode continues on optional failures;
3. queue fallback integrated in release path.

### WP-5. Tests (DELIVERED)

Файлы:

- [tests/test_quality_gate_delivery_queue.py](tests/test_quality_gate_delivery_queue.py)
- [tests/test_quality_gate_notify_drain.py](tests/test_quality_gate_notify_drain.py)
- [tests/test_quality_gate_notify.py](tests/test_quality_gate_notify.py)

Validation pack:

```bash
.venv/bin/pytest -q tests/test_quality_gate_delivery_queue.py tests/test_quality_gate_notify_drain.py tests/test_quality_gate_notify.py tests/test_quality_gate_check.py tests/test_quality_gate.py tests/test_outputs_api.py
```

Observed result:

- `53 passed`.

## 5. Constraints

1. additive-only changes;
2. no breaking changes to outputs API contracts;
3. no changes to JSON-first ingestion canon.

## 6. Acceptance

Tranche accepted when:

1. queue fallback and drain scripts merged;
2. release script queue-aware logic merged;
3. tests green;
4. PRD/TZ/analysis/implementation plan updated.
