# TZ v3.5 — Incident Registry Retention Governance

## 1. Goal

Реализовать retention policy lifecycle для file-backed incident registry.

## 2. Baseline

До tranche были реализованы:

1. incident escalation service/check
2. durable incident registry persistence/report
3. incident and registry API/UI surfaces

## 3. Delivered Work Packages

### WP-1. Retention Service

Файл: [app/services/quality_gate_incident_retention.py](app/services/quality_gate_incident_retention.py)

Сделано:

1. evaluate/apply policy modes
2. age and count pruning logic
3. markdown reporting

### WP-2. Retention CLI

Файл: [scripts/quality_gate_incident_retention_check.py](scripts/quality_gate_incident_retention_check.py)

Сделано:

1. dry-run/apply flags
2. fail-on-removals policy
3. json output for orchestration

### WP-3. Retention API

Файл: [app/api/outputs.py](app/api/outputs.py)

Сделано:

1. retention JSON endpoint
2. retention markdown endpoint

### WP-4. Workflow Integration

Файл: [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

1. retention env knobs
2. retention step in strict/best-effort branches

### WP-5. UI Integration

Файл: [app/ui/app.py](app/ui/app.py)

Сделано:

1. retention controls
2. retention metrics
3. markdown load action

### WP-6. Tests

Файлы:

1. [tests/test_quality_gate_incident_retention.py](tests/test_quality_gate_incident_retention.py)
2. [tests/test_quality_gate_incident_retention_check.py](tests/test_quality_gate_incident_retention_check.py)
3. [tests/test_outputs_api.py](tests/test_outputs_api.py)

Result:

- `106 passed`

## 4. Acceptance

Tranche accepted when retention lifecycle works end-to-end and regression is green.
