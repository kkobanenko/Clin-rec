# PRD v3.7 — CR Intelligence Platform

## 1. Stage

```text
Unified governance score for release reliability control.
```

## 2. Objective For v3.7

Добавить сводную governance score метрику, консолидирующую ключевые governance сигналы в единую release decision surface.

## 3. Functional Requirements

### Existing Scope

Требования v3.6 сохраняются.

### FR-51 (NEW). Governance Score Model

Система должна вычислять weighted governance score по компонентам:

1. quality gate
2. queue policy
3. incident severity
4. incident registry risk

### FR-52 (NEW). Governance Score API

Система должна предоставлять:

1. `GET /outputs/quality-gate/governance-score`
2. `GET /outputs/quality-gate/governance-score/markdown`

### FR-53 (NEW). Governance Score Checker

Release workflow должен поддерживать score threshold check с policy `min_score`.

### FR-54 (NEW). Governance Score UI

UI должен отображать:

1. score value
2. status (`good/warning/critical`)
3. per-component contributions

## 4. Success Metrics

| Metric | Target |
|---|---:|
| governance-score API availability | 100% |
| governance-score markdown availability | 100% |
| governance-score release check | 100% |
| governance-score UI panel availability | 100% |
| regression pass rate | 100% |

## 5. Acceptance Criteria

v3.7 accepted when:

1. governance score stack merged end-to-end
2. regression pack green
3. docs synchronized

## 6. Out Of Scope

1. adaptive/ML weighting
2. trend forecasting model
3. automatic score self-tuning
