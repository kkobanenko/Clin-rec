# PRD v3.1 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform обеспечивает воспроизводимый internal evidence & governance runtime для клинических рекомендаций.

## 2. Current Product Stage

```text
Pilot governance hardening with queue-backed quality-gate notification delivery.
```

## 3. Product Objective For v3.1

Обеспечить устойчивую доставку quality gate notifications при временной недоступности webhook endpoint.

## 4. Functional Requirements

### FR-1..FR-23

Требования v3.0 сохраняются.

### FR-24 (NEW). Local Spool Queue Fallback

При сбое webhook delivery notifier должен уметь складывать payload в локальную очередь для последующей доставки.

### FR-25 (NEW). Queue Drain Mechanism

Должен существовать CLI-механизм controlled replay queued payloads в webhook endpoint с retries и max-items.

### FR-26 (NEW). Best-Effort Success-On-Enqueue Policy

В best-effort release режиме enqueue fallback может считаться допустимым успешным исходом уведомления.

### FR-27 (NEW). Release Workflow Queue Awareness

Release workflow должен поддерживать:

- pre-notify queue drain;
- strict vs best-effort поведение queue delivery;
- конфигурируемый spool location.

## 5. Success Metrics

| Metric | Target |
|---|---:|
| enqueue fallback activation on notify failure | 100% |
| queued payload replay success path validated | 100% |
| best-effort notification does not block release on enqueue success | 100% |
| strict mode remains blocking on unrecoverable errors | 100% |
| delivery queue test coverage | 100% |

## 6. Acceptance Gate For v3.1

v3.1 accepted when:

1. queue utility module exists and used by notifier;
2. drain CLI exists and tested;
3. release script wired for drain + queue-aware notify;
4. deterministic policy behavior validated by tests;
5. docs (analysis/plan/TZ) updated.

## 7. Out Of Scope For v3.1

1. distributed/centralized message queue backend;
2. incident escalation workflows;
3. long-term queue metrics dashboards.
