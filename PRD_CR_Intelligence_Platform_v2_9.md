# PRD v2.9 — CR Intelligence Platform

## 1. Product Purpose

CR Intelligence Platform обеспечивает воспроизводимую внутреннюю evidence-платформу для ingest/normalize/extract/score/audit clinical recommendation corpus.

## 2. Current Product Stage

```text
Internal pilot hardening with enforceable quality gate in release workflow.
```

## 3. Product Objective For v2.9

Сделать quality gate обязательной частью release-runbook, чтобы release pack не мог завершиться успешно при нарушении критичных quality rules.

## 4. Functional Requirements

### FR-1..FR-15

Все требования v2.8 сохраняются без изменений.

### FR-16 (NEW). Release Script Quality Gate Enforcement

Release-ready workflow должен содержать обязательный шаг quality gate enforcement перед regression pack.

### FR-17 (NEW). Deterministic Exit-Code Policy

Quality gate checker должен возвращать стабильные exit-codes для pipeline automation:

- `0` для pass/allowable states;
- `1` для policy failure;
- `2` для runtime/API failure.

### FR-18 (NEW). Configurable Gate Policy In Release Runs

Оператор должен иметь возможность настраивать в runbook:

- window size (`max_versions`);
- thresholds (`high_skip_threshold`, `max_avg_skip_rate`);
- minimal candidate volume (`min_candidate_pairs`);
- strictness policy (`fail_on_warn`, `allow_no_data`).

### FR-19 (NEW). Gate Evidence Artifactability

Quality gate output должен сохраняться в логах и быть пригоден для включения в release evidence artifacts.

## 5. Success Metrics

| Metric | Target |
|---|---:|
| Release run executes quality gate enforcement step | 100% |
| Gate step honors configured thresholds | 100% |
| Deterministic gate exit-code behavior | 100% |
| API threshold forwarding correctness | 100% |
| Additive compatibility with existing outputs APIs | 100% |

## 6. Acceptance Gate For v2.9

v2.9 tranche accepted when:

1. quality gate checker script exists and is usable from release runbook;
2. release_ready_check includes mandatory quality gate step;
3. thresholds/policy are configurable via env;
4. tests for script and endpoints are green;
5. stage and implementation docs are updated.

## 7. Out Of Scope For v2.9

1. External notification channels.
2. Centralized CI policy service.
3. Multi-tenant gate governance.
