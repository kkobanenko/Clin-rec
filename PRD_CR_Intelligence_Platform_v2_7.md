# PRD v2.7 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform обеспечивает воспроизводимый локальный контур ingest/normalize/extract/score/audit для клинических рекомендаций с подтверждаемым evidence trail.

## 2. Current Product Stage

```text
Evidence-rich internal pilot operations in progress.
```

## 3. Product Objective For v2.7

Сделать candidate diagnostics операционно пригодной для ежедневного мониторинга, а не только для оффлайн анализа event log.

## 4. Users

### Operator

Отслеживает skip-rate и причины деградации candidate generation по версиям документов.

### Pharma Analyst

Видит, какие версии системно теряют candidate pairs, и может инициировать rerun/inspection.

### Medical Expert

Получает более прозрачную картину, насколько полно evidence candidate-поверхность покрывает корпус.

### Technical Administrator

Использует агрегированный diagnostics report для release decision и post-incident triage.

## 5. Functional Requirements

### FR-1. Stage Integrity

Stage claims подтверждаются runtime evidence.

### FR-2. JSON-First Baseline Preservation

JSON remains canonical source; HTML/PDF fallback only.

### FR-3. Evidence Density Visibility

Состояние evidence доступно для версии и корпуса.

### FR-4. Operator Explanation Layer

UI объясняет причины empty/degraded states.

### FR-5. Release Evidence Completeness

Релизные отчёты содержат traceability и runtime counters.

### FR-6. Additive API Guarantees

Изменения не ломают существующие contracts.

### FR-7. Pilot Operations Repeatability

Операционный цикл должен быть повторяемым по runbook.

### FR-8. Candidate Diagnostics Telemetry

Extract stage пишет candidate diagnostics в `PipelineEventLog.detail_json`.

### FR-9. Corpus Quality Monitoring

`/outputs/corpus-quality` предоставляет health/flags/coverage.

### FR-10. Content-Kind-Aware Scoring

Image fragments не дают положительного score.

### FR-11 (NEW). Candidate Diagnostics Aggregate Report

Система должна предоставлять агрегированный diagnostics report по последним extraction событиям:

- `GET /outputs/candidate-diagnostics` (JSON summary);
- `GET /outputs/candidate-diagnostics/markdown` (human-readable report);
- report содержит `avg_skip_rate`, `max_skip_rate`, `high_skip_versions`, `total_candidate_pairs`, top-versions by skip-rate.

### FR-12 (NEW). Operator Candidate Diagnostics Surface

Operator UI (`Outputs` page) должен отображать:

- окно версий (N recent runs);
- configurable high-skip threshold;
- top-N high-skip versions;
- markdown diagnostics report for handoff.

## 6. Success Metrics

| Metric | Target |
|---|---:|
| Candidate diagnostics JSON endpoint availability | 100% |
| Candidate diagnostics Markdown endpoint availability | 100% |
| UI display for candidate diagnostics summary | 100% |
| High-skip versions correctly counted (`skip_rate >= threshold`) | 100% |
| Additive API compatibility | 100% |

## 7. Acceptance Gate

v2.7 tranche считается принятой при выполнении:

1. `GET /outputs/candidate-diagnostics` возвращает валидный JSON report;
2. `GET /outputs/candidate-diagnostics/markdown` возвращает markdown report;
3. UI Outputs показывает summary и top high-skip versions;
4. unit tests для report service и outputs API проходят;
5. изменения аддитивны и не ломают существующие endpoints.

## 8. Out Of Scope For v2.7

1. External alert delivery (email/webhook/telegram).
2. Full release gate auto-blocker.
3. Multi-tenant governance.
