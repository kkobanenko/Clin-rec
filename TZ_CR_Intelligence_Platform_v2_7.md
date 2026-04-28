# TZ v2.7 — Automated Quality Gate

## 1. Goal

Реализовать автоматический quality gate, который объединяет corpus quality и candidate diagnostics в единый release readiness verdict.

## 2. Baseline

До начала tranche на current head уже реализованы:

1. corpus quality report (`/outputs/corpus-quality`);
2. candidate diagnostics aggregate (`/outputs/candidate-diagnostics`);
3. outputs operator page в Streamlit;
4. test coverage для diagnostics/report endpoints.

## 3. Technical Objective

Добавить:

1. `QualityGateService` с rule-based evaluation;
2. outputs API endpoints для quality gate (json + markdown);
3. UI блок `Automated Quality Gate` в Outputs page;
4. unit tests для quality gate service и endpoints.

## 4. Work Packages

### WP-1. Service Layer (DELIVERED)

Файл: `app/services/quality_gate.py`

Сделано:

- dataclasses `QualityGateRuleResult`, `QualityGateReport`;
- `QualityGateService.evaluate(...)`;
- 4 правила оценки и общий verdict.

Acceptance criteria:

1. поддерживаются verdict `pass/warn/fail/no-data`;
2. rule payload содержит status/value/threshold/comparator/message;
3. доступны `to_dict()` и `to_markdown()`.

### WP-2. API Layer (DELIVERED)

Файл: `app/api/outputs.py`

Сделано:

- `GET /outputs/quality-gate`;
- `GET /outputs/quality-gate/markdown`.

Acceptance criteria:

1. оба endpoints работают и возвращают ожидаемые форматы;
2. параметры порогов валидируются через Query constraints;
3. изменения additive и не ломают outputs contracts.

### WP-3. UI Layer (DELIVERED)

Файл: `app/ui/app.py`

Сделано:

- блок `Automated Quality Gate` в page Outputs;
- controls для параметров gate;
- verdict + summary + rules table;
- markdown loading button.

Acceptance criteria:

1. UI рендерит verdict и rules;
2. UI не падает при API ошибках;
3. markdown report отображается в интерфейсе.

### WP-4. Tests (DELIVERED)

Файлы:

- `tests/test_quality_gate.py`;
- `tests/test_outputs_api.py` (new endpoint tests).

Acceptance criteria:

1. покрыты pass/warn/fail/no-data сценарии;
2. покрыт markdown path;
3. endpoint tests возвращают 200 и корректный формат.

## 5. Validation Pack

```bash
.venv/bin/pytest -q tests/test_quality_gate.py tests/test_candidate_diagnostics_report.py tests/test_outputs_api.py
```

Observed result:

- `31 passed`.

## 6. Constraints

1. additive-only API changes;
2. route precedence must not break `/{output_id}` path;
3. no changes to JSON-first ingestion contract;
4. graceful UI degradation on HTTP failures.

## 7. Acceptance

Tranche accepted when:

1. quality gate JSON and markdown endpoints available;
2. quality gate UI panel operational;
3. tests green;
4. PRD/analysis/implementation plan updated;
5. commit/push completed.
