# TZ v2.8 — Enforced Quality Gate In Release Workflow

## 1. Goal

Интегрировать quality gate как обязательный исполняемый шаг release-ready сценария.

## 2. Baseline

На current head уже существовали:

1. `QualityGateService` (verdict computation);
2. outputs quality gate endpoints;
3. операторская quality gate панель в UI;
4. базовые тесты quality gate.

## 3. Technical Objective

Добавить:

1. runtime checker script с deterministic exit codes;
2. wiring в `release_ready_check.sh` как mandatory step;
3. расширенное API test coverage для threshold forwarding;
4. script-level unit tests.

## 4. Work Packages

### WP-1. Runtime Checker Script (DELIVERED)

Файл: [scripts/quality_gate_check.py](scripts/quality_gate_check.py)

Сделано:

- argparse CLI;
- fetch `/outputs/quality-gate`;
- policy matrix для verdict -> exit code;
- JSON output mode;
- rule lines for log readability.

Acceptance criteria:

1. `run()` возвращает 0/1/2 по policy;
2. поддержка `--fail-on-warn` и `--allow-no-data`;
3. корректная обработка HTTP ошибок.

### WP-2. Release Script Wiring (DELIVERED)

Файл: [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

- добавлены env vars для gate policy;
- добавлен mandatory run_step `quality_gate_enforcement`;
- gate выполняется после smoke и до regression tests.

Acceptance criteria:

1. quality gate step входит в normal release path;
2. падение gate step прерывает release check;
3. пороги настраиваются через env.

### WP-3. Test Coverage (DELIVERED)

Файлы:

- [tests/test_quality_gate_check.py](tests/test_quality_gate_check.py)
- [tests/test_outputs_api.py](tests/test_outputs_api.py)

Acceptance criteria:

1. покрыты policy paths pass/warn/fail/no-data;
2. покрыт JSON mode и HTTP failure;
3. покрыт forwarding threshold parameters на endpoints.

## 5. Validation Pack

```bash
.venv/bin/pytest -q tests/test_quality_gate.py tests/test_quality_gate_check.py tests/test_outputs_api.py
```

Observed result:

- `35 passed`.

## 6. Constraints

1. additive-only changes for API contracts;
2. release workflow remains local-runtime compatible;
3. no changes to JSON-first canonical ingestion logic.

## 7. Acceptance

Tranche accepted when:

1. checker script and release wiring merged;
2. gate threshold policies configurable;
3. tests green;
4. PRD/TZ/analysis/implementation plan updated.
