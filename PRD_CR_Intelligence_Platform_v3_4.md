# PRD v3.4 — CR Intelligence Platform

## 1. Product Stage

```text
Incident-aware governance over quality gate and queue SLO signals.
```

## 2. Objective For v3.4

Добавить формализованную incident escalation логику в release governance runtime, чтобы критические и деградированные состояния автоматически формировали управляемые escalation reports и проверялись в release pipeline.

## 3. Functional Requirements

### Existing FR Scope

FR предыдущих версий сохраняются (JSON-first pipeline, quality gate, queue fallback/replay/status/policy).

### FR-37 (NEW). Incident Escalation Report

Система должна вычислять escalation report на основе:

1. quality gate verdict
2. queue policy verdict
3. агрегированных operational signals

### FR-38 (NEW). Incident API Surface

Система должна предоставлять:

1. `GET /outputs/quality-gate/incident`
2. `GET /outputs/quality-gate/incident/markdown`

### FR-39 (NEW). Incident Operator Console

UI должен отображать:

1. severity (`info/high/critical`)
2. should_escalate flag
3. reason, actions, tags, key details

### FR-40 (NEW). Incident Governance Check

Release workflow должен запускать incident checker с настраиваемыми policy knobs:

1. fail-on-high
2. allow-info

## 4. Success Metrics

| Metric | Target |
|---|---:|
| incident endpoint availability | 100% |
| incident markdown endpoint availability | 100% |
| incident checker in release workflow | 100% |
| operator incident panel availability | 100% |
| incident regression pack | 100% pass |

## 5. Acceptance Criteria

v3.4 accepted when:

1. incident service/API/UI/checker merged
2. release script wiring completed
3. target tests pass
4. docs and implementation plan updated

## 6. Out Of Scope

1. persistent incident management datastore
2. on-call routing integrations (PagerDuty/Opsgenie)
3. automatic remediation executor
