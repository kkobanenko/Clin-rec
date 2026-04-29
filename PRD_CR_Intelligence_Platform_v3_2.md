# PRD v3.2 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform обеспечивает reproducible internal runtime для evidence extraction и release governance clinical recommendation corpus.

## 2. Current Product Stage

```text
Resilient pilot governance with observable queue-backed signaling.
```

## 3. Product Objective For v3.2

Добавить observability-поверхность для quality gate notification queue, чтобы оператор мог контролировать backlog и риски недоставки.

## 4. Functional Requirements

### FR-1..FR-27

Требования v3.1 сохраняются.

### FR-28 (NEW). Queue Status API

Система должна предоставлять queue status endpoints (JSON + Markdown), отражающие backlog и возраст очереди.

### FR-29 (NEW). Queue Verdict Counters

Queue status report должен включать распределение queued payloads по verdict/status.

### FR-30 (NEW). Operator Queue Visibility

Outputs UI должен отображать queue metrics и preview элементов очереди для оперативной диагностики.

### FR-31 (NEW). Queue Spool Override For Diagnostics

Оператор должен иметь возможность диагностически указать alternate spool dir для чтения queue status.

## 5. Success Metrics

| Metric | Target |
|---|---:|
| queue status JSON endpoint availability | 100% |
| queue status markdown endpoint availability | 100% |
| UI queue status panel availability | 100% |
| queue status endpoint parameter forwarding correctness | 100% |
| queue status service unit coverage | 100% |

## 6. Acceptance Gate For v3.2

v3.2 accepted when:

1. queue status service merged;
2. queue status endpoints merged;
3. Outputs UI queue panel merged;
4. test pack green;
5. analysis/plan/TZ updated.

## 7. Out Of Scope For v3.2

1. centralized message broker migration;
2. automatic queue cleanup/SLO enforcement;
3. incident escalation platform integration.
