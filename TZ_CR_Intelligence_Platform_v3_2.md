# TZ v3.2 — Queue SLO Policy Enforcement

## 1. Goal

Внедрить policy-driven queue SLO layer для quality gate notification backlog.

## 2. Baseline

На старте tranche уже были:

1. queue-backed notification fallback/replay;
2. queue status service/API/UI;
3. release workflow queue drain integration;
4. tests for queue observability.

## 3. Technical Objective

Реализовать:

1. queue policy service с verdict and actions;
2. queue policy endpoints (json/markdown);
3. queue policy UI block;
4. queue policy checker для release orchestration;
5. test coverage for service/checker/endpoints.

## 4. Work Packages

### WP-1. Queue Policy Service (DELIVERED)

Файл: [app/services/quality_gate_queue_policy.py](app/services/quality_gate_queue_policy.py)

Сделано:

- thresholds-based rule evaluation;
- verdict mapping (`healthy/degraded/critical/empty`);
- markdown report generation with actions.

Acceptance criteria:

1. queue metrics transformed into rule statuses;
2. verdict and summary deterministic;
3. actions list present.

### WP-2. API Surface (DELIVERED)

Файл: [app/api/outputs.py](app/api/outputs.py)

Сделано:

- `GET /outputs/quality-gate/queue-policy`;
- `GET /outputs/quality-gate/queue-policy/markdown`.

Acceptance criteria:

1. endpoints respond with expected payload types;
2. thresholds and spool/max-items params supported;
3. additive compatibility preserved.

### WP-3. UI Integration (DELIVERED)

Файл: [app/ui/app.py](app/ui/app.py)

Сделано:

- queue policy panel;
- threshold inputs;
- verdict/rules/actions rendering;
- markdown loader.

Acceptance criteria:

1. policy state visible to operator;
2. degraded/critical states readable;
3. markdown export available.

### WP-4. Release Workflow Check (DELIVERED)

Файлы:

- [scripts/quality_gate_queue_policy_check.py](scripts/quality_gate_queue_policy_check.py)
- [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

- CLI checker with policy-aware exit codes;
- release script step integration;
- strict/best-effort branching.

Acceptance criteria:

1. critical verdict can fail workflow;
2. degraded policy can be strict/optional;
3. empty queue handling policy configurable.

### WP-5. Tests (DELIVERED)

Файлы:

- [tests/test_quality_gate_queue_policy.py](tests/test_quality_gate_queue_policy.py)
- [tests/test_quality_gate_queue_policy_check.py](tests/test_quality_gate_queue_policy_check.py)
- [tests/test_outputs_api.py](tests/test_outputs_api.py)

Validation pack:

```bash
.venv/bin/pytest -q tests/test_quality_gate_queue_policy.py tests/test_quality_gate_queue_policy_check.py tests/test_quality_gate_queue_status.py tests/test_quality_gate_delivery_queue.py tests/test_quality_gate_notify_drain.py tests/test_quality_gate_notify.py tests/test_quality_gate_check.py tests/test_quality_gate.py tests/test_outputs_api.py
```

Observed result:

- `75 passed`.

## 5. Constraints

1. additive-only changes;
2. no breakage in existing outputs API contracts;
3. no changes to JSON-first ingestion canon.

## 6. Acceptance

Tranche accepted when:

1. queue policy service/API/UI/checker merged;
2. release script wiring completed;
3. tests green;
4. docs updated.
