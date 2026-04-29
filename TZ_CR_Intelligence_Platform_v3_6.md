# TZ v3.6 — Unified Governance Score Layer

## 1. Goal

Реализовать unified governance score для release decision support.

## 2. Baseline

До tranche были доступны:

1. quality gate governance
2. queue policy and incident escalation
3. durable incident registry and retention

## 3. Delivered Work Packages

### WP-1. Score Service

Файл: [app/services/quality_gate_governance_score.py](app/services/quality_gate_governance_score.py)

Сделано:

1. weighted multi-component scoring
2. status mapping (`good/warning/critical`)
3. markdown report output

### WP-2. Score Checker CLI

Файл: [scripts/quality_gate_governance_score_check.py](scripts/quality_gate_governance_score_check.py)

Сделано:

1. score fetch and threshold policy
2. deterministic exit code behavior

### WP-3. Score API

Файл: [app/api/outputs.py](app/api/outputs.py)

Сделано:

1. score JSON endpoint
2. score markdown endpoint

### WP-4. Score Release Step

Файл: [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

1. score min-threshold env knob
2. score check step in workflow

### WP-5. Score UI

Файл: [app/ui/app.py](app/ui/app.py)

Сделано:

1. score status panel
2. component contribution table
3. markdown loader

### WP-6. Tests

Файлы:

1. [tests/test_quality_gate_governance_score.py](tests/test_quality_gate_governance_score.py)
2. [tests/test_quality_gate_governance_score_check.py](tests/test_quality_gate_governance_score_check.py)
3. [tests/test_outputs_api.py](tests/test_outputs_api.py)

Validation result:

- `115 passed`

## 4. Acceptance

Tranche accepted with end-to-end score computation, enforcement, and visibility.
