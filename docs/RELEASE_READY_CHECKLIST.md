# Release-Ready MVP Checklist

Этот checklist используется для формального решения `go/no-go` по текущей сборке MVP.

## 1. Scope and Runtime Freeze

- Подтвердить, что оценивается один конкретный commit / branch state.
- Подтвердить один active runtime profile: `host-only` или `docker-compose-only`.
- Подтвердить согласованность `CRIN_CELERY_BROKER_URL` и `CRIN_CELERY_RESULT_BACKEND` между API и worker.
- Подтвердить, что release evaluation не смешивается с unrelated локальными экспериментами.
- Для полного прогона можно использовать helper: `bash scripts/release_ready_check.sh`.
- По умолчанию helper сохраняет логи в `.artifacts/release_checks/<timestamp>`; этот каталог использовать как evidence bundle для summary.
- Helper также копирует `docs/RELEASE_SUMMARY_TEMPLATE.md` в bundle как стартовую заготовку `release_summary.md`.
- При необходимости operator может передать `SMOKE_POLL_TIMEOUT` как общий fallback или отдельно `STRUCTURAL_SMOKE_POLL_TIMEOUT` / `QUALITY_SMOKE_POLL_TIMEOUT`, а также `SMOKE_ACTIVATE_MODEL_ID`, `SMOKE_ACTIVATE_MODEL_AUTHOR` и `SMOKE_FORCE_ACTIVATE_MODEL=1`.
- Для быстрых late-stage rerun доступны `SKIP_STRUCTURAL_SMOKE=1` и `SKIP_QUALITY_SMOKE=1`, но использовать их можно только после уже зафиксированного smoke-green на том же runtime/profile.

## 2. Structural Gate

- Запустить structural smoke.
- Убедиться, что lifecycle проходит до terminal state.
- Убедиться, что `stats_json` содержит обязательный минимум.
- Убедиться, что auxiliary routes `/outputs`, `/kb/indexes/master`, `/pipeline/storage-stages`, `/tasks/{task_id}` отвечают корректно.

## 3. Quality Gate

- Запустить quality smoke.
- Убедиться, что при `discovered_count > 0` хотя бы один документ дает непустые `content` и `fragments`.
- Убедиться, что downstream pair evidence присутствует.
- Если есть active scoring model, убедиться, что `/matrix/cell` подтверждает downstream path.

## 4. API Regression Gate

- Прогнать `tests/test_pipeline_review_api.py`.
- Прогнать `tests/test_matrix_model_ops_api.py`.
- Прогнать `tests/test_outputs_api.py`.
- Прогнать `tests/test_aux_api_mounts.py`.

## 5. Integration Gate

- Прогнать `tests/test_kb_integration_postgres.py`.
- Проверить downstream extract -> candidate -> scoring -> matrix path.
- Проверить KB/output workflows и task visibility.
- Mandatory integration suites не должны завершаться как `skipped`; skip для этого gate трактуется как незакрытая проверка.

## 6. Governance Gate

- Подтвердить, что review queue/history/actions доступны и интерпретируемы.
- Подтвердить, что scoring model readiness/activation path контролируем и диагностируем.
- Подтвердить, что output/KB background workflows видимы через tasks/operator surfaces.

## 7. Go/No-Go Summary

- Зафиксировать статус: `release-ready` или `blocked`.
- Зафиксировать список blocker-ов, если они есть.
- Зафиксировать residual risks, допустимые для post-MVP.
- Зафиксировать, какие ограничения явно остаются вне scope: full matrix governance, full reviewer productization, external distribution.
- При оформлении summary использовать `docs/RELEASE_SUMMARY_TEMPLATE.md`.

## 8. Source of Truth

- Product contract: `PRD_CR_Intelligence_Platform_v1_6.md`
- Technical tranche: `TZ_CR_Intelligence_Platform_v1_5.md`
- Runtime procedure: `RUNBOOK_RUNTIME_PROFILE.md`
- Baseline acceptance floor: `DOD_MVP.md`