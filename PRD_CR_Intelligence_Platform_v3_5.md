# PRD v3.5 — CR Intelligence Platform

## 1. Product Stage

```text
Durable incident governance with local incident registry.
```

## 2. Objective For v3.5

Внедрить долговременную (file-backed) фиксацию incident escalation сигналов для release governance, чтобы получить auditable историю эскалаций и агрегированную операционную аналитическую поверхность.

## 3. Functional Requirements

### Existing Scope

Все требования v3.4 сохраняются.

### FR-41 (NEW). Incident Registry Persistence

Система должна сохранять incident report events в локальный JSONL registry.

### FR-42 (NEW). Incident Registry Aggregate Report

Система должна выдавать агрегаты по incident registry:

1. total incidents
2. escalation count
3. severity counters
4. latest timestamp
5. recent items list

### FR-43 (NEW). Incident Registry API

Система должна предоставлять:

1. `GET /outputs/quality-gate/incident/registry`
2. `GET /outputs/quality-gate/incident/registry/markdown`

### FR-44 (NEW). Incident Registry In Release Workflow

Release orchestration должна выполнять registry update step для фиксации текущего incident state.

### FR-45 (NEW). Incident Registry Operator Visibility

Operator UI должен показывать registry counters и recent entries.

## 4. Success Metrics

| Metric | Target |
|---|---:|
| registry persistence step availability | 100% |
| registry API endpoint availability | 100% |
| registry markdown endpoint availability | 100% |
| operator registry panel availability | 100% |
| regression coverage for registry | 100% pass |

## 5. Acceptance Criteria

v3.5 accepted when:

1. registry service/script/API/UI/release-step merged
2. targeted governance regression pack is green
3. PRD/TZ/analysis/plan synchronized

## 6. Out Of Scope

1. centralized incident database
2. retention and archival automation
3. multi-channel on-call integrations
