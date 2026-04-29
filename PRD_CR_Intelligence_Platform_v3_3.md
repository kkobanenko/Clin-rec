# PRD v3.3 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform обеспечивает reproducible internal runtime для evidence extraction и release governance clinical recommendation corpus.

## 2. Current Product Stage

```text
Policy-driven pilot governance with queue SLO enforcement.
```

## 3. Product Objective For v3.3

Добавить SLO/policy enforcement для notification queue, чтобы backlog состояние было формализовано в управляемый verdict и operational actions.

## 4. Functional Requirements

### FR-1..FR-31

Требования v3.2 сохраняются.

### FR-32 (NEW). Queue Policy Verdict API

Система должна предоставлять queue policy verdict endpoints (JSON + Markdown).

### FR-33 (NEW). Queue Policy Rule Set

Policy layer должна оценивать минимум:

- queue size;
- oldest item age;
- total queue size bytes.

### FR-34 (NEW). Queue Policy Actions

Policy report должен возвращать рекомендуемые действия для degraded/critical состояния.

### FR-35 (NEW). Queue Policy Operator Panel

UI должен отображать queue policy verdict, rules и actions с настраиваемыми thresholds.

### FR-36 (NEW). Queue Policy Orchestration Check

Release workflow должен выполнять queue policy checker step с configurable strictness.

## 5. Success Metrics

| Metric | Target |
|---|---:|
| queue policy JSON endpoint availability | 100% |
| queue policy markdown endpoint availability | 100% |
| UI queue policy panel availability | 100% |
| queue policy check integration in release workflow | 100% |
| queue policy test coverage | 100% |

## 6. Acceptance Gate For v3.3

v3.3 accepted when:

1. queue policy service/API/UI merged;
2. release workflow includes queue policy check;
3. policy checker script validated;
4. targeted test pack green;
5. analysis/plan/TZ updated.

## 7. Out Of Scope For v3.3

1. automatic remediation engine;
2. incident escalation workflows;
3. centralized queue backend migration.
