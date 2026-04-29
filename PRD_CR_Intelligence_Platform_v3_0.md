# PRD v3.0 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform обеспечивает локально воспроизводимую internal platform для evidence extraction, scoring и release governance clinical recommendation corpus.

## 2. Current Product Stage

```text
Pilot release governance hardening with external quality-gate notifications.
```

## 3. Product Objective For v3.0

Добавить внешний канал оповещения по quality gate verdict в release workflow, чтобы результаты gate не оставались только внутри локального лога.

## 4. Functional Requirements

### FR-1..FR-19

Требования v2.9 сохраняются.

### FR-20 (NEW). External Gate Notification

После quality gate enforcement система должна отправлять gate verdict во внешний webhook endpoint.

### FR-21 (NEW). Notification Delivery Policies

Должны поддерживаться режимы:

- best-effort (не блокирует release pack при отсутствии webhook);
- required (блокирует release pack при провале уведомления).

### FR-22 (NEW). Deterministic Notification Exit Codes

Webhook notifier должен возвращать стабильные коды завершения:

- `0` success / allowed skip;
- `1` notification delivery failure;
- `2` configuration/fetch failure.

### FR-23 (NEW). Notification Payload Contract

Webhook payload должен включать:

- event metadata (`event`, `created_at`, `runtime_profile`, `operator`);
- verdict summary;
- rule counters (`rules_total`, `rules_warn`, `rules_failed`);
- full gate report snapshot.

## 5. Success Metrics

| Metric | Target |
|---|---:|
| release_ready_check executes notification step | 100% |
| required notification mode blocks on delivery failure | 100% |
| best-effort mode passes when webhook missing | 100% |
| notifier retry behavior validated | 100% |
| test coverage for notify layer | 100% |

## 6. Acceptance Gate For v3.0

v3.0 accepted when:

1. webhook notifier script merged;
2. release script includes notification step with policy knobs;
3. deterministic exit-code behavior validated by tests;
4. targeted test pack green;
5. analysis/plan/TZ updated.

## 7. Out Of Scope For v3.0

1. guaranteed delivery queue infrastructure;
2. incident escalation management integration;
3. secret vault automation for webhook credentials.
