# Phase 2 backlog: расхождения TZ/PRD с реализацией

Документ фиксирует **некритичные** gap'ы (после закрытия блокеров pipeline и наполнения корпуса). Канонические требования — [TZ_CR_Intelligence_Platform_v1_2_kb.md](../TZ_CR_Intelligence_Platform_v1_2_kb.md), [PRD_CR_Intelligence_Platform_v1_3_kb.md](../PRD_CR_Intelligence_Platform_v1_3_kb.md), DoD — [DOD_MVP.md](../DOD_MVP.md).

## Операционные заметки (важно для развёртывания)

1. `**CRIN_RUBRICATOR_API_USER_AGENT`** — API `apicr.minzdrav.gov.ru` отвечает **451**, если User-Agent не браузероподобный. В [.env](../.env) задан Mozilla-префикс; после смены `.env` нужен `**docker compose up -d --force-recreate`** (restart не подхватывает новые переменные из env_file).
2. `**CRIN_DISCOVERY_MAX_RECORDS**` (по умолчанию 20) — ограничение числа карточек за один full sync; поле добавлено в config и применяется только для `full`-режима.
3. **Метрики discovery** — `failed_count` в `pipeline_run` означает число записей **без `external_id`**, а не сбой fetch; `coverage_percent` считается по реально обработанным записям после dedupe/limit.

## Справочник МНН (`molecule`)

- Извлечение МНН в `MnnExtractor` **словарное**: совпадения только с теми названиями, что уже есть в `molecule` / `molecule_synonym`.
- Дополнительно включена эвристика **латинских названий в круглых скобках** (типичный формат КР): новые строки создаются в `molecule` до основного извлечения (`inn_heuristic.py` + `ExtractionPipeline`). Полный импорт госреестра ЛП — вне текущего объёма; при необходимости — отдельный импорт CSV/API.

## Модель данных (TZ §7)


| Gap                                                        | Комментарий                                                                   |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `document_version.normalizer_version` / `compiler_version` | Поля добавлены и пишутся normalize/compile стадиями; дальнейшее расширение — только если понадобятся дополнительные stage-level version markers. |
| `text_fragment.fragment_hash`                              | Используется `stable_id` (MD5).                                               |
| `pair_evidence` vs TZ `component_scores_json`              | В коде — отдельные числовые колонки.                                          |


## Discovery / crawl (TZ §10)

- Нет персистентных DOM-снапшотов / полного лога XHR в object storage.
- Incremental sync: кандидаты probe без сравнения хэшей уже версионированных документов.

## Нормализация (TZ §11)

- Нет агрегированного quality/completeness score в БД.
- Для SPA-страниц добавлен fallback: **Playwright** + извлечение `innerText` после загрузки; при повторной нормализации удаляются `**pair_evidence`**, ссылающиеся на старые фрагменты (обход FK).

## Knowledge compilation (TZ §12)

- Нет отдельного типа `concept_page` (частично закрыто `glossary_term`).
- Базовый YAML frontmatter добавлен в compiler-generated Markdown (`source_digest`, `entity_page`, `glossary_term`, `open_question`, `master_index`); operator search now covers artifact title/summary/slug/body, but richer schema frontmatter остаётся как doc-polish/backlog.
- Компилятор теперь создаёт минимальные детерминированные `**knowledge_claim**` для `source_digest` / `entity_page` / `glossary_term` / `open_question`; richer claim graph и conflict semantics остаются в бэклоге.

## Lint / health (TZ §13)

- Реализованы не все проверки: дубликаты, общие orphan, stale vs даты источника, gap discovery — в основном в бэклоге; при этом базовый lint уже ловит digest без provenance, non-hypothesis claims без provenance и compiler artifacts без claims.

## Clinical extraction / scoring (TZ §14–15)

- Confidence экстрактора не пишется в `PairEvidence`.
- `explanation_json` теперь содержит context/pair/evidence/fragment ids для scoring traceability, но claim ids по TZ по-прежнему не покрыты.
- Negative evidence не смоделирован явно.

## Outputs (TZ §16)

- Генерация кроме memo — заглушки; accepted file-back теперь может создавать и линковать `KnowledgeArtifact`, а Streamlit показывает structured output detail и compact list filter/search/artifact/review-status/released/generator-version/scope/has-file drill-down с linked artifact follow-up, но broader output productization остаётся в бэклоге.

## Очереди Celery (TZ §19)

- Очередь `reindex` объявлена в `celery_app`, отдельных задач `reindex.*` нет — используется `rebuild_indexes`.

## UI (TZ §21)

- Нет единого linkage-view и gap suggestions; Streamlit теперь покрывает базовые operator сценарии, system health, release-gate snapshot, compact reviewer queue/history surfaces, scoring diff summary tables, KB master-index preview, KB artifact type/status/review/generator/body-search, KB claims list/type/review/conflicted filters with conflict flags, KB conflict summaries with artifact/review scoping and artifact ids, KB entity type/status/canonical+alias+refs search/detail, compact KB artifact/entity/output tables with richer KB artifact/entity/output detail, backward-compatible RU/EN language switch с persisted preference для admin/operator UI, recent UI task tracking на async workflows, pipeline run detail picker, pipeline stage filter, matrix list/detail filters, review quick-pick controls для queue/history/submit follow-up и Tasks-page quick-pick/origin-filter/label-search/sort controls. Полная productized health dashboard, единый linkage-view и перевод framework-provided Streamlit chrome остаются вне текущего tranche.

## Текущая стадия проекта

- Текущий статус: **release-ready MVP подтвержден**, активная стадия работ — **phase-2 operator hardening**.
- Full-pack compose-backed validation уже зафиксирован в `docs/RELEASE_SUMMARY_2026-04-24.md`; текущие backlog items больше не трактуются как release blockers по умолчанию.
- Ближайший фокус: additive UI/API follow-up, уменьшающий operator friction без ломки release contract.

## Ближайшие шаги

- Расширять async follow-up и cross-surface linkage между pipeline, tasks, outputs, KB и review.
- Держать PRD/TZ/VERSIONING/backlog синхронными с validated head после каждого заметного tranche.
- Оставлять full dashboard redesign, gap suggestions и более глубокую Streamlit chrome localization в post-MVP polish.

## Версионирование документов

- [VERSIONING.md](../VERSIONING.md) синхронизирован с текущими release evidence и release-hardening tranche; KB-specific historical entries и cross-links можно расширять дальше как doc-polish, но это больше не blocker-gap.

---

*Последнее обновление: 2026-04-24 — после full-pack release-ready sync и последующего operator-hardening tranche с recent task tracking, pipeline run detail picker, pipeline stage filter, matrix filters, review quick-pick controls и Tasks-page quick-pick/filter/search/sort follow-up; предыдущие operator-surface closure items сохранены.*