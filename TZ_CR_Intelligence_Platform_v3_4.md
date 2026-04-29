# TZ v3.4 — Durable Incident Registry Layer

## 1. Goal

Добавить durable реестр инцидентов в governance pipeline для quality gate и queue policy эскалаций.

## 2. Baseline

До начала tranche были доступны:

1. incident escalation service
2. incident API and UI panel
3. incident checker in release workflow

## 3. Delivered Work Packages

### WP-1. Registry Service

Файл: [app/services/quality_gate_incident_registry.py](app/services/quality_gate_incident_registry.py)

Сделано:

1. append incident event into JSONL
2. aggregate report builder with counters
3. markdown report rendering

### WP-2. Registry Update CLI

Файл: [scripts/quality_gate_incident_registry_update.py](scripts/quality_gate_incident_registry_update.py)

Сделано:

1. fetch incident report from API
2. persist into registry
3. print aggregate snapshot and policy-safe exit codes

### WP-3. Registry API Surface

Файл: [app/api/outputs.py](app/api/outputs.py)

Сделано:

1. incident registry JSON endpoint
2. incident registry markdown endpoint

### WP-4. Registry In Release Workflow

Файл: [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

Сделано:

1. registry directory env knob
2. mandatory/optional registry persistence step

### WP-5. Registry In Operator UI

Файл: [app/ui/app.py](app/ui/app.py)

Сделано:

1. registry counters panel
2. recent entries table
3. markdown loader

### WP-6. Tests

Файлы:

1. [tests/test_quality_gate_incident_registry.py](tests/test_quality_gate_incident_registry.py)
2. [tests/test_quality_gate_incident_registry_update.py](tests/test_quality_gate_incident_registry_update.py)
3. [tests/test_outputs_api.py](tests/test_outputs_api.py)

Result:

- `96 passed`

## 4. Acceptance

Транш принят при выполнении:

1. registry layer implemented end-to-end
2. regression green
3. docs updated and versioned
