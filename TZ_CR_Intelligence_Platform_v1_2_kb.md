Техническое задание

CR Intelligence Platform — knowledge-compilation платформа для клинических рекомендаций; **matrix output** — приоритетный производный артефакт поверх compiled KB и evidence layer

| Версия | v1.3 |
| --- | --- |
| Дата | 03.04.2026 |
| Статус | Рабочая версия |
| Назначение | Внутренний продуктовый и технический контур проекта |

> Документ определяет архитектуру в концепции: **official sources → source vault → normalized corpus → compiled knowledge base → evidence layer → analytic outputs → matrix output**. Продуктовые цели — [PRD_CR_Intelligence_Platform_v1_3_kb.md](PRD_CR_Intelligence_Platform_v1_3_kb.md).

# 1. Назначение документа

ТЗ задаёт состав системы, архитектуру, data contracts, knowledge artifacts, API, фоновые процессы, требования к UI/QA и план реализации. Аудитория: разработка, data engineering, NLP/ML, knowledge engineering, internal QA.

# 2. Предмет разработки

Подсистемы (логически; до выделения микросервисов допускается совмещение в одном процессе):

- Индексирование и загрузка корпуса (**source vault**).
- Нормализация до sections и **text fragments** (**normalized corpus**).
- **Knowledge compilation** (Markdown-like артефакты, индексы, backlinks).
- **Artifact registry** (типизированные knowledge artifacts, версии, статусы).
- **Claim / provenance** (fact / inference / hypothesis, привязки к источникам).
- **Artifact linting и health-check**.
- **Clinical extraction**: МНН, disease-context, УУР/УДД, relation signals.
- **Evidence и scoring**, включая **matrix_cell** и **matrix output**.
- **Analytic output generation** и **output filing**.
- Reviewer validation, QA, versioned releases.

# 3. Границы системы

## 3.1 Входы

| Поле | Описание |
| --- | --- |
| Основной источник | Рубрикатор КР Минздрава РФ и официальные артефакты (web-app, HTML/JSON, PDF). |
| Справочники | МНН и синонимы, disease taxonomy, relation taxonomy, правила нормализации, шаблоны artifacts. |
| Ручные данные | Reviewer annotations, gold set, overrides, конфигурации scoring, шаблоны output filing, quality rules. |

## 3.2 Выходы

### Data outputs

Каталог документов, raw-артефакты, **normalized corpus**, section/fragment tables, clinical entities.

### Knowledge outputs (compiled KB)

| Выход | Описание |
| --- | --- |
| Source digests | Сводки по источнику |
| Entity pages | Канонические карточки сущностей |
| Concept pages | Понятия, методики, индексные страницы |
| Synthesis notes | Сравнительные и сводные заметки |
| Conflict reports | Явные противоречия |
| Open question registries | Пробелы и открытые вопросы |
| Indexes | В т.ч. master index |

### Artifact outputs

| Выход | Описание |
| --- | --- |
| Markdown memos / reports | Текстовые аналитические артефакты |
| Slide decks | Презентации |
| Comparative tables | Сравнительные таблицы |
| Chart specs / rendered charts | Визуализации |
| Matrix exports / snapshots | Экспорты и снапшоты **matrix output** |

### Operational / product outputs

Логи, метрики, run history, health reports, reviewer audit trail; pair evidence, context scores, **matrix_cell**, explanation JSON (см. §15).

# 4. Технологический стек

| Поле | Описание |
| --- | --- |
| Backend API | Python 3.12 + FastAPI |
| Асинхронные задачи | Celery или RQ + Redis |
| База данных | PostgreSQL 15+ |
| Sync DB driver | `psycopg2-binary` (или эквивалент) для sync SQLAlchemy в worker |
| Хранение raw | S3-совместимое: MinIO или облачный S3 |
| Хранение KB artifacts | Git, object storage + manifests; опционально `content_md` в БД |
| Браузерная автоматизация | Playwright |
| NLP / parsing | pandas/polars, regex, словари, spaCy / natasha |
| Knowledge compilation | LLM gateway + Markdown-шаблоны + валидаторы |
| Поиск | PostgreSQL FTS, trigram; pgvector — опционально |
| Внутренний UI | Streamlit или React + facade |
| Мониторинг | Prometheus + Grafana, Sentry или эквивалент |

# 5. Логическая архитектура (сервисы)

| Сервис | Назначение |
| --- | --- |
| Discovery service | Рубрикатор, карточки, network payloads |
| Fetch service | Raw HTML/JSON/PDF в object storage |
| Normalize service | Текст, sections, fragments |
| Knowledge Compilation service | Digests, entity/concept pages, indexes, synthesis |
| Artifact Registry service | Реестр artifacts, slug, статусы версий |
| Claim Registry service | Claims, fact / inference / hypothesis, связь с evidence |
| Backlink / Link Resolution service | Ссылки между artifacts, auto-linking |
| Lint / Health Check service | Противоречия, gaps, stale, orphans, дубликаты |
| Clinical extraction service | Сущности и relation signals |
| Scoring engine | Evidence, context scores, **matrix_cell** |
| Reviewer service | Adjudication, overrides |
| Output Generation service | Memos, reports, decks, charts |
| Output Filing service | Возврат outputs в KB с quality gate |
| API service | REST/JSON контракты |
| Scheduler / queue layer | Очереди и расписание |

# 6. Архитектурный контур обработки (10 шагов)

| Шаг | Этап | Результат |
| --- | --- | --- |
| 1 | Discovery | Registry records, payloads |
| 2 | Document probe | html/pdf availability, primary content |
| 3 | Fetch raw artifacts | Immutable raw в storage |
| 4 | Normalize | Sections, **text_fragment** |
| 5 | Compile knowledge artifacts | Digests, pages, indexes (слой compiled KB) |
| 6 | Lint / contradiction / gap checks | Health reports, очереди исправлений |
| 7 | Clinical extraction | МНН, contexts, УУР/УДД, relations; при необходимости candidate pairs |
| 8 | Build evidence and scoring | pair_evidence, scores, **matrix_cell** |
| 9 | Generate outputs | Memos, decks, exports, snapshots |
| 10 | Review / release / publish | Релиз KB и/или **matrix output**, audit trail |

**Data lineage (аудит):**  
- **Output artifact → claims → fragments/sources → document → raw source**  
- **matrix cell → evidence → claims/artifacts → fragments → document → raw source**

# 7. Требования к данным и БД

Канонический формат **matrix output** — long format; wide — только экспорт. **Compiled knowledge base** — отдельный слой с манифестами и provenance.

## 7.1 document_registry

| Поле | Описание |
| --- | --- |
| id | PK |
| external_id | Внешний id документа |
| title | Название |
| card_url | URL карточки |
| html_url / pdf_url | При наличии |
| specialty, age_group, status | Классификация |
| version_label, publish_date, update_date | Версия и даты |
| source_payload_json | Сырой JSON discovery |
| discovered_at / last_seen_at | Служебные метки |

## 7.2 document_version

| Поле | Описание |
| --- | --- |
| id | PK |
| registry_id | FK document_registry |
| version_hash | Хэш содержимого / артефактов |
| source_type_primary | html \| pdf \| html+pdf \| unknown |
| source_type_available | Список типов |
| detected_at, is_current | Версионирование |
| normalizer_version, compiler_version | Версии компонентов |

## 7.3 source_artifact

| Поле | Описание |
| --- | --- |
| id | PK |
| document_version_id | FK |
| artifact_type | html \| json \| pdf |
| raw_path | Object storage |
| content_hash, content_type, headers_json | Целостность и метаданные |
| fetched_at | Время загрузки |

## 7.4 document_section и text_fragment

| Поле | Описание |
| --- | --- |
| id | PK |
| document_version_id / section_id | Связи |
| section_path, section_title | Структура |
| fragment_order, fragment_type | Упорядочивание и тип |
| fragment_text, fragment_hash | Контент |

## 7.5 molecule и molecule_synonym

| Поле | Описание |
| --- | --- |
| molecule_id | PK |
| inn_ru / inn_en, atc_code | Идентификация |
| synonym_text, source | Синонимы |

## 7.6 clinical_context

| Поле | Описание |
| --- | --- |
| context_id | PK |
| disease_id / disease_name | Нозология |
| line_of_therapy, treatment_goal | Линия и цель |
| population_json, context_signature | Популяция и ключ |

## 7.7 knowledge_artifact

| Поле | Описание |
| --- | --- |
| artifact_id | PK |
| artifact_type | `source_digest`, `entity_page`, `concept_page`, `synthesis_note`, `conflict_report`, `open_question`, `output_note`, `slide_deck`, `decision_note` (расширяемо) |
| title | Заголовок |
| canonical_slug | Уникальный стабильный ключ URL/файла |
| status | `draft`, `reviewed`, `deprecated`, `archived` |
| content_md | Тело Markdown (если хранится в БД; иначе см. storage_path) |
| summary | Краткое резюме |
| confidence | Число или enum low/medium/high — по согласованной шкале |
| review_status | Состояние ревью workflow |
| generator_version | Версия компилятора/генератора (= compiler_version в продуктовых метриках) |
| storage_path | Путь к объекту/файлу, если контент вне БД |
| manifest_json | Backlinks, теги, доп. метаданные |
| created_at, updated_at | Временные метки |

## 7.8 artifact_source_link

| Поле | Описание |
| --- | --- |
| id | PK |
| artifact_id | FK knowledge_artifact |
| source_kind | `document_version`, `source_artifact`, `document_section`, `text_fragment`, `external_reference` |
| source_id | ID сущности согласно source_kind |
| support_type | `primary`, `secondary`, `derived` |
| notes | Пояснения |

Семантически покрывает связи с `document_version_id` / `fragment_id` через `source_kind` + `source_id`.

## 7.9 knowledge_claim

| Поле | Описание |
| --- | --- |
| claim_id | PK |
| artifact_id | FK knowledge_artifact |
| claim_type | `fact`, `inference`, `hypothesis` |
| claim_text | Нормализованный тезис |
| confidence | Доверие к тезису |
| review_status | Прохождение ревью |
| conflict_group_id | Группа противоречащих claims (nullable) |
| provenance_json | Детали: fragments, evidence ids, reviewer notes |
| is_conflicted | Быстрый флаг (дублирует/дополняет conflict_group_id) |
| created_at, updated_at | Временные метки |

## 7.10 entity_registry

| Поле | Описание |
| --- | --- |
| entity_id | PK |
| entity_type | `molecule`, `disease`, `therapy_line`, `population`, `regimen`, `manufacturer`, `concept` |
| canonical_name | Канон |
| aliases_json | Синонимы |
| external_refs_json | Внешние справочники |
| status | Актуальность записи |

Связь с `molecule` / клиническими таблицами — через согласованные FK или маппинг в коде.

## 7.11 artifact_backlink

| Поле | Описание |
| --- | --- |
| id | PK |
| from_artifact_id | FK knowledge_artifact |
| to_artifact_id | FK knowledge_artifact |
| link_type | `mentions`, `depends_on`, `contradicts`, `expands`, `derived_from` |

## 7.12 pair_evidence

| Поле | Описание |
| --- | --- |
| evidence_id | PK |
| context_id | FK clinical_context |
| molecule_from_id / molecule_to_id | Directed пара |
| fragment_id | Опорный фрагмент |
| relation_type | Таксономия связи |
| uurr / udd | УУР/УДД |
| component_scores_json | Компоненты score |
| final_fragment_score | Score на фрагменте |
| review_status | auto \| reviewed \| rejected |

## 7.13 pair_context_score

| Поле | Описание |
| --- | --- |
| pair_context_score_id | PK |
| model_version_id | Версия формулы |
| context_id | Контекст |
| molecule_from_id / molecule_to_id | Пара |
| substitution_score | Итог по контексту |
| confidence_score | Доверие |
| evidence_count | Количество evidence |
| explanation_json | Обоснование |

## 7.14 matrix_cell

| Поле | Описание |
| --- | --- |
| matrix_cell_id | PK |
| model_version_id | Версия формулы |
| scope_type / scope_id | global \| disease \| specialty … |
| molecule_from_id / molecule_to_id | Directed |
| substitution_score, confidence_score | Итоги |
| contexts_count, supporting_evidence_count | Агрегаты |
| explanation_short / explanation_json | Объяснения |

## 7.15 output_release

| Поле | Описание |
| --- | --- |
| output_release_id | PK |
| output_type | `memo`, `slides`, `report`, `matrix_snapshot`, `export`, … |
| title | Название релиза |
| artifact_id | FK на knowledge_artifact (если output оформлен как artifact), nullable |
| file_pointer | Путь в storage при отсутствии единого artifact_id |
| scope_json | Область применимости / фильтры |
| generator_version | Версия генератора |
| review_status | Состояние ревью |
| released_at | Время публикации |
| file_back_status | `pending` \| `accepted` \| `rejected` (если применимо) |

## 7.16 Правила хранения (storage rules)

- **Raw-артефакты immutable**: перезапись запрещена; новая версия — новые записи/хэши.
- **Compiled artifacts versioned**: пересборка создаёт новую версию или явный diff; политика в `generator_version` / манифестах.
- **Reviewed artifacts** не заменяются молча: требуется явный процесс (новая версия, review log, override).
- Каждый **non-trivial claim** хранит **provenance** (см. artifact_source_link, provenance_json).
- **Конфликты** — отдельные записи (`conflict_report`, `conflict_group_id`), не маскируются правками текста.
- **Outputs** хранятся отдельно от обязательного слоя wiki/KB файлов; **output filing** добавляет linkage в KB при прохождении quality gate.

# 8. Структура knowledge base на файловом уровне

```text
kb/
  raw/
    clinical_guidelines/
    discovery_payloads/
    pdf/
    html/
  normalized/
    documents/
    fragments/
  wiki/
    indexes/
    glossary/
    entities/
      mnn/
      diseases/
      contexts/
    concepts/
    syntheses/
    conflicts/
    open_questions/
    decisions/
  outputs/
    memos/
    reports/
    slides/
    charts/
```

- `raw/` — immutable; `wiki/` — versioned recompilation; `outputs/` — отдельно; file-back только через quality gate; каждый Markdown — frontmatter (type, status, confidence, sources, timestamps).

# 9. Правила выбора источника текста

1. Полный структурированный HTML допускается как primary.
2. Неполный HTML → primary PDF.
3. Оба артефакта сохраняются при html+pdf.
4. Выбор primary в `document_version`; пересмотр при смене правил полноты.
5. Knowledge artifacts ссылаются только на валидированный **source vault**.

# 10. Требования к discovery и crawling

- Playwright для JS-driven UI.
- Логировать XHR/Fetch, HTTP metadata, при необходимости DOM snapshot.
- Full и incremental sync; сравнение last_seen, дат, хэшей.
- Ограничение параллелизма, ретраи.
- Изменение документа → очереди пересборки зависимых KB artifacts.

# 11. Требования к нормализации текста

Очистка шума; сохранение иерархии; фрагментация с устойчивыми id; quality/completeness score; normalizer version; детерминизм при фиксированной версии.

# 12. Требования к knowledge compilation

## 12.1 Общие

- Типизированные шаблоны артефактов.
- Frontmatter: `title`, `type`, `status`, `sources`, `updated_at`, `confidence`, при необходимости `canonical_slug`, `generator_version`.
- Явная маркировка тезисов: `fact` \| `inference` \| `hypothesis`.
- Нет silent delete reviewer-approved claims без записи в review/diff log.
- Incremental rebuild при изменении источников или шаблонов.

## 12.2 Функциональные требования компиляции

- **Source digest generation** для каждого релевантного document_version.
- **Entity page maintenance** при появлении новых сущностей/алиасов.
- **Concept page maintenance** и **index page generation** (в т.ч. master index).
- **Backlinks и auto-linking** между страницами; синхронизация с `artifact_backlink`.
- **Canonical naming и alias resolution** (согласование с `entity_registry` и molecule tables).
- **Claim typing** в теле артефакта и в `knowledge_claim`.
- **Markdown + frontmatter** для каждого артефакта.
- **Recompile policies** после обновления источников: триггеры из sync/normalize и из явных POST `/kb/compile`.

## 12.3 Обязательные типы (MVP foundation — согласовать с [DOD_MVP.md](DOD_MVP.md))

| Тип | Назначение |
| --- | --- |
| source_digest | Обязательно |
| entity_page | Обязательно |
| glossary_term / concept | Обязательно |
| master_index | Обязательно |
| open_question | Обязательно |
| conflict_report | По мере зрелости lint |
| synthesis_note | Post-MVP или Phase 2 |

## 12.4 Provenance

- У каждого artifact — список source links (`artifact_source_link`).
- Non-trivial claim — привязка к fragment_id и/или evidence_id в `provenance_json`.
- Reviewer-approved: автор, timestamp, причина.

# 13. Требования к health / lint

- **Duplicate artifact detection** (slug, near-duplicate content).
- **Orphan artifact detection** (нет входящих/исходящих связей там, где ожидаются).
- **Unsupported claims** (claim без минимального provenance).
- **Stale artifact detection** (источник обновлён, artifact нет).
- **Contradiction clustering** (группы claims / conflict_group_id).
- **Missing entity page** для извлечённых canonical entities.
- **Low-confidence artifact review queues**.
- **Gap discovery / suggested new article generation**.

# 14. Требования к clinical extraction

Extractors для МНН (canonicalization), disease-context, УУР/УДД, relation-signal phrases; extractor_confidence и версия; результаты доступны scoring и compiler.

# 15. Требования к генерации пар и scoring engine

## 15.1 Candidate generation

Ограничение контекстом; directed пары i→j vs j→i; negative evidence; KB-aware вспомогательно, не заменяет fragment evidence.

## 15.2 Relation taxonomy

Минимальный набор типов; relation отдельно от score; reviewer override.

## 15.3 Scoring model

Компоненты и веса versioned; confidence отдельно; `explanation_json` ссылается на evidence ids, **claims**, supporting artifacts — для **matrix output** и аудита.

# 16. Требования к output generation и output filing

- Генерация memo, report, deck, chart spec, comparative tables.
- Manifest: использованные artifacts, evidence, generator_version.
- **Output filing** только по quality rules; без provenance — не approved.
- Статусы accepted / rejected / needs_review.

# 17. API-контракты

Минимальный набор; расширение по мере реализации. Baseline smoke см. [DOD_MVP.md](DOD_MVP.md).

| Метод | Endpoint | Назначение |
| --- | --- | --- |
| GET | /documents | Список документов |
| GET | /documents/{id} | Деталь карточки |
| GET | /documents/{id}/content | Нормализованный текст |
| GET | /documents/{id}/fragments | Фрагменты |
| POST | /sync/full | Полный sync |
| POST | /sync/incremental | Инкрементальный sync |
| GET | /runs, GET /runs/{id} | Статусы pipeline (см. реализацию) |
| GET | /kb/indexes/master | Корневой индекс KB |
| GET | /kb/artifacts | Список artifacts |
| GET | /kb/artifacts/{id} | Деталь artifact |
| GET | /kb/entities/{id} | Сущность из entity_registry / связка |
| GET | /kb/claims | Фильтруемый список claims |
| GET | /kb/conflicts | Конфликты / conflict groups |
| POST | /kb/compile | Запуск компиляции KB |
| POST | /kb/lint | Запуск health/lint |
| GET | /matrix | Ячейки матрицы |
| GET | /matrix/cell | Одна ячейка + evidence |
| POST | /outputs/generate | Унифицированная генерация (тип в теле запроса) |
| POST | /outputs/file | Output filing workflow |
| GET | /outputs | Список output_release / drafts |
| GET | /outputs/{id} | Деталь output |

**Совместимость:** `POST /outputs/memo` может оставаться алиасом к `POST /outputs/generate` с `output_type=memo`; `POST /outputs/file-back/{id}` — алиас к `POST /outputs/file`.

# 18. Форматы обмена данными

- Матрица long: `from_inn`, `to_inn`, `scope`, `model_version`, `substitution_score`, `confidence_score`.
- KB artifact: Markdown + YAML frontmatter + JSON manifest.
- BI: CSV/Parquet; обоснования: JSONL / JSON API.

# 19. Очереди задач и scheduler

| Очередь (канон) | Назначение | Примечание |
| --- | --- | --- |
| discovery | Обход каталога | |
| probe | Доступность источников | |
| fetch | Загрузка raw | |
| normalize | Нормализация | |
| **compile_kb** | Компиляция KB | ≈ прежний `kb_compile` |
| **lint_kb** | Health/lint | ≈ `kb_lint` |
| **refresh_backlinks** | Пересчёт backlinks | |
| **detect_conflicts** | Кластеризация противоречий | |
| extract | Clinical extraction | |
| score | Evidence и **matrix** | |
| **generate_outputs** | Генерация артефактов | ≈ `output_generate` |
| **file_outputs** | Output filing | |
| **rebuild_indexes** | Индексы, BI prep | ≈ `reindex` |

## 19.1 Профили развёртывания

- host-only или docker-compose-only; единые `CRIN_CELERY_BROKER_URL` и `CRIN_CELERY_RESULT_BACKEND`; `pending` не терминален для polling.

# 20. Логирование, мониторинг и аудит

stats_json для completed runs (как в PRD); метрики compile/lint; ошибки с привязкой к document_id / artifact_id; Prometheus; неизменяемый audit reviewer.

# 21. Требования к внутреннему UI

- Список документов, карточка документа (raw trail, fragments, extraction).
- **KB explorer**; **artifact detail**; **claim provenance panel**.
- **Conflict review queue**; **health dashboard**; **output library**; **gap suggestions**.
- **Linkage view**: raw source → fragment → claim → artifact → **matrix cell**.
- Карточка **matrix cell**; reviewer queue; dashboard качества.

# 22. Тестирование и QA

| Категория | Содержание |
| --- | --- |
| Unit / integration | Парсеры, normalizer, extractors, compiler, lint, scoring, API |
| Regression | Версии парсеров, шаблонов, формул |
| **Artifact compilation regression** | Дайджесты/страницы при фикстурах |
| **Provenance completeness** | Claim–source покрытие |
| **Claim-to-source integrity** | Ссылки валидны |
| **Conflict detection correctness** | Golden cases |
| **Stale detection** | Симуляция обновления источника |
| **Filing roundtrip** | generate → file → чтение из KB |
| **Reviewed artifact protection** | Нет silent overwrite |
| **Output generation consistency** | Детерминизм при фиксированном seed/версии |
| E2E smoke | См. DOD_MVP (baseline не требует всех `/kb/*` сразу) |

# 23. Критерии приёмки по модулям

1. Discovery: идемпотентность registry.  
2. Fetch: hash, headers, version link.  
3. Normalize: структура fragments.  
4. Compile: digest + frontmatter + links.  
5. Lint: provenance/orphan/stale сигналы.  
6. Extract: версии и confidence.  
7. Scoring: воспроизводимость **matrix cell**.  
8. API: согласованные форматы.  
9. Reviewer: overrides в релизах.  
10. Outputs: manifest + controlled filing.  
11. Runtime: единый broker/backend.

# 24. План реализации (спринты)

| Sprint | Фокус | Результат |
| --- | --- | --- |
| 1 | Source vault + БД + object storage + discovery | Фундамент корпуса |
| 2 | Normalization + versioning + fragment model | Normalized corpus |
| 3 | KB compilation v1 | Digests, базовые страницы |
| 4 | Provenance, backlinks, indexes, linting | Health + связность |
| 5 | Clinical extraction v1 | Сущности в БД |
| 6 | Evidence and scoring | **Matrix** v1 в контуре |
| 7 | Outputs, reviewer flow, artifact library | Продуктовые артефакты |
| 8 | Matrix explorer, release control, hardening | Готовность к релизам |

# 25. Ограничения и допущения

- Риски изменения DOM источника; HTML не auto-full без probe.
- Docker — [ISOLATION_POLICY.md](ISOLATION_POLICY.md).
- **Matrix output** не есть регуляторное заключение.
- Нет production-ready релизов без confidence и reviewer loop где требуется PRD.

# 26. Финальные deliverables

Код (backend, workers, compiler/lint, extract/score, UI), схема БД, migrations, API-документация, runbook, lineage, тесты, dashboards, checklists.

# 27. Definition of Done (MVP)

Канонический DoD — [DOD_MVP.md](DOD_MVP.md) (baseline + Phase 2); TZ не дублирует противоречащие критерии.
