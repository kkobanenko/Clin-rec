# TZ v2.9 — External Quality Gate Notifications

## 1. Goal

Добавить внешний notification layer для quality gate verdict и встроить его в release-ready execution path.

## 2. Baseline

До начала tranche уже существовали:

1. quality gate service + outputs endpoints;
2. gate enforcement script;
3. release_ready_check mandatory gate step;
4. script/API coverage для gate enforcement.

## 3. Technical Objective

Реализовать:

1. webhook notifier script;
2. wiring notifier step в release_ready_check;
3. policy knobs required/best-effort mode;
4. unit tests для notifier и retry logic.

## 4. Work Packages

### WP-1. Webhook Notifier Script (DELIVERED)

Файл: [scripts/quality_gate_notify.py](scripts/quality_gate_notify.py)

Сделано:

- fetch gate report from API;
- build notification payload;
- post with retries;
- dry-run and missing-webhook modes;
- deterministic exit codes.

Acceptance criteria:

1. dry-run печатает payload;
2. missing webhook обрабатывается по policy;
3. webhook failures корректно сигнализируются.

### WP-2. Release Script Integration (DELIVERED)

Файл: [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

- новые env settings (`QUALITY_GATE_WEBHOOK_URL`, `QUALITY_GATE_NOTIFY_RETRIES`, `QUALITY_GATE_NOTIFY_REQUIRED`);
- шаг `quality_gate_notify` после gate enforcement;
- support required/best-effort policies.

Acceptance criteria:

1. шаг уведомления запускается в release check;
2. required mode блокирует pack при ошибке уведомления;
3. best-effort mode не блокирует при отсутствии webhook.

### WP-3. Tests (DELIVERED)

Файл: [tests/test_quality_gate_notify.py](tests/test_quality_gate_notify.py)

Сделано:

- policy path tests;
- failure mode tests;
- retry behavior test.

Acceptance criteria:

1. покрыты success/failure/skip scenarios;
2. retry logic tested;
3. exit codes проверены.

## 5. Validation Pack

```bash
.venv/bin/pytest -q tests/test_quality_gate.py tests/test_quality_gate_check.py tests/test_quality_gate_notify.py tests/test_outputs_api.py
```

Observed result:

- `42 passed`.

## 6. Constraints

1. additive changes only;
2. no breaking changes in outputs API;
3. no changes to JSON-first ingestion canon.

## 7. Acceptance

Tranche accepted when:

1. notifier script and release integration merged;
2. required/best-effort policies available;
3. tests green;
4. PRD/TZ/analysis/implementation plan updated.
