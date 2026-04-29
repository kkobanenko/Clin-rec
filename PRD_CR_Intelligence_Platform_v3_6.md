# PRD v3.6 — CR Intelligence Platform

## 1. Product Stage

```text
Retention-governed incident registry for release operations.
```

## 2. Objective For v3.6

Добавить retention lifecycle control для incident registry, чтобы ограничить рост исторических данных и стандартизировать cleanup policy в release governance.

## 3. Functional Requirements

### Existing Scope

Требования v3.5 сохраняются.

### FR-46 (NEW). Incident Retention Evaluation

Система должна оценивать retention policy по правилам:

1. `max_items`
2. `max_age_days`

### FR-47 (NEW). Incident Retention Apply Mode

Система должна поддерживать dry-run и apply режимы для cleanup incident registry.

### FR-48 (NEW). Incident Retention API

Система должна предоставлять:

1. `GET /outputs/quality-gate/incident/retention`
2. `GET /outputs/quality-gate/incident/retention/markdown`

### FR-49 (NEW). Incident Retention In Release Workflow

Release workflow должен запускать retention check/apply с policy knobs.

### FR-50 (NEW). Incident Retention UI Controls

Operator UI должен показывать retention параметры и отчет.

## 4. Success Metrics

| Metric | Target |
|---|---:|
| retention API availability | 100% |
| retention markdown availability | 100% |
| retention workflow step availability | 100% |
| retention UI panel availability | 100% |
| retention regression tests pass | 100% |

## 5. Acceptance Criteria

v3.6 accepted when:

1. retention service + CLI + API + UI + workflow merged
2. targeted regression bundle is green
3. docs updated and versioned

## 6. Out Of Scope

1. long-term cold storage archiver
2. distributed locking for multi-writer cleanup
3. centralized incident DB migration
