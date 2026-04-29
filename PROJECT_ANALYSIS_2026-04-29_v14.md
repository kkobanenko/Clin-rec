# Project Analysis — 2026-04-29 v14

## 1. Current Stage

```text
Unified governance scoring over gate, queue, incident, and registry signals.
```

Стадия реализации: введен сводный governance score, который агрегирует quality gate, queue policy, incident escalation и incident registry в единый operational KPI.

## 2. Cycle Deliverables

1. Governance score domain service:
   - [app/services/quality_gate_governance_score.py](app/services/quality_gate_governance_score.py)
2. Governance score checker CLI:
   - [scripts/quality_gate_governance_score_check.py](scripts/quality_gate_governance_score_check.py)
3. Governance score API endpoints:
   - [app/api/outputs.py](app/api/outputs.py)
   - `GET /outputs/quality-gate/governance-score`
   - `GET /outputs/quality-gate/governance-score/markdown`
4. Governance score panel in UI:
   - [app/ui/app.py](app/ui/app.py)
5. Governance score enforcement in release workflow:
   - [scripts/release_ready_check.sh](scripts/release_ready_check.sh)

## 3. Validation

Targeted regression pack result:

- `115 passed`

Coverage includes:

1. governance score weighted model
2. checker threshold behavior and exit codes
3. endpoints and param forwarding
4. compatibility with full governance pipeline

## 4. Risks

1. score weighting is static and currently heuristic
2. no historical trend modeling in score computation
3. no ML calibration of thresholds

## 5. Summary

```text
Implementation reached unified governance scoring stage.
Next stage: score trend analytics and adaptive thresholds.
```
