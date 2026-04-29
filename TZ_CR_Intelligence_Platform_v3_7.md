# TZ v3.7 — Governance Trends Analytics Layer

## 1. Goal

Реализовать trend analytics для governance quality drift detection.

## 2. Baseline

До tranche существовали:

1. governance score layer
2. incident registry and retention controls
3. release-time policy checks

## 3. Delivered Work Packages

### WP-1. Trends Service

Файл: [app/services/quality_gate_governance_trends.py](app/services/quality_gate_governance_trends.py)

Сделано:

1. baseline-window trend points
2. drift status mapping
3. markdown report generation

### WP-2. Trends CLI Checker

Файл: [scripts/quality_gate_governance_trends_check.py](scripts/quality_gate_governance_trends_check.py)

Сделано:

1. trend fetch and policy contract
2. fail-on-degrading behavior

### WP-3. Trends API

Файл: [app/api/outputs.py](app/api/outputs.py)

Сделано:

1. trends JSON endpoint
2. trends markdown endpoint

### WP-4. Trends Workflow Enforcement

Файл: [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

1. baseline window env knob
2. trends fail policy knob
3. trends workflow step

### WP-5. Trends UI

Файл: [app/ui/app.py](app/ui/app.py)

Сделано:

1. trends metrics panel
2. trend points table
3. markdown load action

### WP-6. Tests

Файлы:

1. [tests/test_quality_gate_governance_trends.py](tests/test_quality_gate_governance_trends.py)
2. [tests/test_quality_gate_governance_trends_check.py](tests/test_quality_gate_governance_trends_check.py)
3. [tests/test_outputs_api.py](tests/test_outputs_api.py)

Result:

- `124 passed`

## 4. Acceptance

Tranche accepted with validated trend analytics and integration coverage.
