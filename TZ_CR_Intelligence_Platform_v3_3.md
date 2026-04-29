# TZ v3.3 — Incident Escalation Governance Layer

## 1. Goal

Реализовать incident escalation слой поверх quality gate + queue policy для release governance.

## 2. Baseline

На входе уже были реализованы:

1. automated quality gate
2. queue fallback/replay
3. queue observability
4. queue policy/SLO verdict

## 3. Delivered Work Packages

### WP-1. Incident Domain Service

Файл: [app/services/quality_gate_incident.py](app/services/quality_gate_incident.py)

Сделано:

1. escalation decision from gate + queue policy
2. severity mapping (`info/high/critical`)
3. normalized actions/tags/details payload
4. markdown rendering

### WP-2. Incident API

Файл: [app/api/outputs.py](app/api/outputs.py)

Сделано:

1. incident JSON endpoint
2. incident markdown endpoint
3. additive integration without route breakage

### WP-3. Operator UI

Файл: [app/ui/app.py](app/ui/app.py)

Сделано:

1. dedicated incident section
2. severity/escalation visual status
3. actions/tags/details rendering
4. markdown loader

### WP-4. Release Orchestration

Файлы:

1. [scripts/quality_gate_incident_check.py](scripts/quality_gate_incident_check.py)
2. [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

1. policy-aware incident checker
2. strict/best-effort wiring in release script
3. configurable fail-on-high/allow-info behavior

### WP-5. Test Coverage

Файлы:

1. [tests/test_quality_gate_incident.py](tests/test_quality_gate_incident.py)
2. [tests/test_quality_gate_incident_check.py](tests/test_quality_gate_incident_check.py)
3. [tests/test_outputs_api.py](tests/test_outputs_api.py)

Result:

- `87 passed`

## 4. Acceptance

Транш принят при выполнении:

1. end-to-end incident flow implemented
2. regression green
3. docs synchronized
