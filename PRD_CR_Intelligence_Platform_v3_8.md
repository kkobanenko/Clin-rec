# PRD v3.8 — CR Intelligence Platform

## 1. Stage

```text
Trend-aware governance for release reliability decisions.
```

## 2. Objective For v3.8

Добавить governance trend analytics для оценки дрейфа operational quality относительно baseline period.

## 3. Functional Requirements

### Existing Scope

FR v3.7 сохраняются.

### FR-55 (NEW). Governance Trends Model

Система должна вычислять:

1. trend status (`improving/stable/degrading`)
2. score delta vs baseline
3. escalated ratio delta vs baseline

### FR-56 (NEW). Governance Trends API

Система должна предоставить:

1. `GET /outputs/quality-gate/governance-trends`
2. `GET /outputs/quality-gate/governance-trends/markdown`

### FR-57 (NEW). Governance Trends Check

Release workflow должен поддерживать fail policy для degrading trend status.

### FR-58 (NEW). Governance Trends UI

UI должен показывать status, deltas и trend points table.

## 4. Success Metrics

| Metric | Target |
|---|---:|
| governance-trends API availability | 100% |
| governance-trends markdown availability | 100% |
| trends workflow check availability | 100% |
| trends UI panel availability | 100% |
| trends regression pass | 100% |

## 5. Acceptance Criteria

v3.8 accepted when trends stack is merged, validated, and documented.

## 6. Out Of Scope

1. advanced anomaly detection
2. external time-series DB integration
3. adaptive baseline computation
