# PRD v2.8 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform предоставляет локально воспроизводимую платформу evidence engineering для клинических рекомендаций: ingest, normalize, extract, score, audit и operator-ready diagnostics.

## 2. Current Product Stage

```text
Evidence-rich internal pilot operations in progress.
```

## 3. Product Objective For v2.8

Перейти от разрозненных диагностик к единому автоматическому quality gate verdict, пригодному для release decision.

## 4. Users

### Operator

Получает единый verdict для go/no-go оценки перед релизным прогоном.

### Pharma Analyst

Оценивает качество candidate coverage и evidence density по правилам gate.

### Medical Expert

Получает прозрачный индикатор зрелости evidence-поверхности корпуса.

### Technical Administrator

Использует gate-report как обязательный артефакт release evidence пакета.

## 5. Functional Requirements

### FR-1..FR-12

Все требования v2.7 сохраняются без изменений и обратной несовместимости.

### FR-13 (NEW). Automated Quality Gate Verdict

Система должна предоставлять объединенный quality gate report, который:

- интегрирует corpus quality и candidate diagnostics;
- вычисляет rule-based verdict: `pass | warn | fail | no-data`;
- возвращает evaluated rules с threshold/value/comparator/message.

### FR-14 (NEW). Quality Gate API Surface

Должны быть доступны endpoints:

- `GET /outputs/quality-gate` (JSON);
- `GET /outputs/quality-gate/markdown` (Markdown).

### FR-15 (NEW). Operator Quality Gate Panel

Streamlit Outputs page должна отображать:

- gate verdict и summary;
- настраиваемые пороги rule evaluation;
- таблицу правил;
- markdown gate report.

## 6. Success Metrics

| Metric | Target |
|---|---:|
| `/outputs/quality-gate` availability | 100% |
| `/outputs/quality-gate/markdown` availability | 100% |
| Rule evaluation completeness (all configured rules present) | 100% |
| UI gate panel availability | 100% |
| Additive API compatibility | 100% |

## 7. Acceptance Gate For v2.8

v2.8 tranche считается принятой, если:

1. quality gate endpoints доступны и возвращают валидный payload;
2. verdict корректно формируется для pass/warn/fail/no-data сценариев;
3. UI корректно отображает verdict/rules/markdown;
4. unit tests для сервиса и endpoints зелёные;
5. контрактная совместимость с текущими outputs API сохранена.

## 8. Out Of Scope For v2.8

1. External alert delivery channels.
2. CI-level mandatory stop-the-line enforcement.
3. Multi-tenant release governance.
