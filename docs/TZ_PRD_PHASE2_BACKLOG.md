# Phase 2 backlog: расхождения TZ/PRD с реализацией

Документ фиксирует **некритичные** gap'ы (после закрытия блокеров pipeline и наполнения корпуса). Канонические требования — [TZ_CR_Intelligence_Platform_v1_2_kb.md](../TZ_CR_Intelligence_Platform_v1_2_kb.md), [PRD_CR_Intelligence_Platform_v1_3_kb.md](../PRD_CR_Intelligence_Platform_v1_3_kb.md), DoD — [DOD_MVP.md](../DOD_MVP.md).

## Операционные заметки (важно для развёртывания)

1. `**CRIN_RUBRICATOR_API_USER_AGENT`** — API `apicr.minzdrav.gov.ru` отвечает **451**, если User-Agent не браузероподобный. В [.env](../.env) задан Mozilla-префикс; после смены `.env` нужен `**docker compose up -d --force-recreate`** (restart не подхватывает новые переменные из env_file).
2. `**CRIN_DISCOVERY_MAX_RECORDS**` (по умолчанию 20) — ограничение числа карточек за один full sync.
3. **Метрики discovery** — `failed_count` в `pipeline_run` означает число записей **без `external_id`**, а не сбой fetch (исправлено относительно прежней ошибочной формулы `discovered - new_count`).

## Справочник МНН (`molecule`)

- Извлечение МНН в `MnnExtractor` **словарное**: совпадения только с теми названиями, что уже есть в `molecule` / `molecule_synonym`.
- Дополнительно включена эвристика **латинских названий в круглых скобках** (типичный формат КР): новые строки создаются в `molecule` до основного извлечения (`inn_heuristic.py` + `ExtractionPipeline`). Полный импорт госреестра ЛП — вне текущего объёма; при необходимости — отдельный импорт CSV/API.

## Модель данных (TZ §7)


| Gap                                                        | Комментарий                                                                   |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `document_version.normalizer_version` / `compiler_version` | В TZ указаны; в схеме частично покрыто полем `normalizer_version` на секциях. |
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
- Нет YAML frontmatter в Markdown.
- Компилятор не создаёт строки `**knowledge_claim**` автоматически.

## Lint / health (TZ §13)

- Реализованы не все проверки: дубликаты, общие orphan, stale vs даты источника, gap discovery — в основном в бэклоге.

## Clinical extraction / scoring (TZ §14–15)

- Confidence экстрактора не пишется в `PairEvidence`.
- `explanation_json` без полных id evidence/claims по TZ.
- Negative evidence не смоделирован явно.

## Outputs (TZ §16)

- Генерация кроме memo — заглушки; filing не создаёт `KnowledgeArtifact` автоматически.

## Очереди Celery (TZ §19)

- Очередь `reindex` объявлена в `celery_app`, отдельных задач `reindex.*` нет — используется `rebuild_indexes`.

## UI (TZ §21)

- Нет единого linkage-view и gap suggestions; Streamlit теперь покрывает базовые operator сценарии, system health и release-gate snapshot, но не full productized health dashboard.

## Версионирование документов

- [VERSIONING.md](../VERSIONING.md) синхронизирован с текущими release evidence и release-hardening tranche; KB-specific historical entries и cross-links можно расширять дальше как doc-polish, но это больше не blocker-gap.

---

*Последнее обновление: 2026-04-23 — после закрытия ORM FTS gap, dashboard release snapshot и синхронизации versioning/release evidence.*