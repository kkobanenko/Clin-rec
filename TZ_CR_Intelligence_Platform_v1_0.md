Техническое задание

CR Intelligence Platform — платформа сбора и расчёта матриц заменяемости МНН

| Версия | v1.0 |
| --- | --- |
| Дата | 31.03.2026 |
| Статус | Рабочая версия |
| Назначение | Внутренний продуктовый и технический контур проекта |

> Документ описывает платформу CR Intelligence Platform для получения, нормализации и интерпретации клинических рекомендаций Минздрава РФ с последующим расчётом explainable-матриц клинической заменяемости МНН.

# 1. Назначение документа

Настоящее техническое задание определяет состав системы, архитектуру, данные, API, фоновые процессы, критерии качества и план реализации платформы CR Intelligence Platform. Документ предназначен для команды разработки, data engineering, NLP/ML и internal QA.

# 2. Предмет разработки

- Система индексирования и загрузки корпуса клинических рекомендаций Минздрава РФ.

- Система нормализации документов до sections и text fragments.

- Система clinical extraction: МНН, disease-context, УУР/УДД, relation signals.

- Система расчёта evidence records, context scores, matrix cells и confidence score.

- Система reviewer validation, QA и versioned releases матрицы.

# 3. Границы системы

## 3.1 Входы

| Поле | Описание |
| --- | --- |
| Основной источник | Рубрикатор КР Минздрава РФ и официальные артефакты, доступные через web-app, HTML/JSON и PDF. |
| Справочники | Справочник МНН и синонимов, таблицы disease taxonomy, правила извлечения и relation taxonomy. |
| Ручные данные | Reviewer annotations, gold set, manual overrides, конфигурации scoring-моделей. |

## 3.2 Выходы

| Поле | Описание |
| --- | --- |
| Data outputs | Каталог документов, raw-артефакты, normalized corpus, section/fragment tables, clinical entities. |
| Product outputs | Pair evidence, pair context scores, matrix cells, confidence scores, explanation JSON, exports в CSV/Parquet/JSONL. |
| Operational outputs | Логи, метрики pipeline, run history, dashboards качества, reviewer audit trail. |

# 4. Технологический стек

| Поле | Описание |
| --- | --- |
| Backend API | Python 3.12 + FastAPI |
| Асинхронные задачи | Celery или RQ + Redis |
| База данных | PostgreSQL 15+ |
| Хранение артефактов | S3-совместимое хранилище: MinIO или облачный S3 |
| Браузерная автоматизация | Playwright |
| NLP / parsing | pandas/polars, regex, словари, spaCy / natasha по необходимости |
| Векторный поиск | pgvector — опционально |
| Внутренний UI | Streamlit или React + отдельный backend facade |
| Мониторинг | Prometheus + Grafana, Sentry или эквивалент |

# 5. Логическая архитектура

- Discovery service — обходит рубрикатор, собирает карточки документов и network payloads.

- Fetch service — забирает raw HTML/JSON/PDF и складывает в object storage.

- Normalize service — строит clean text, sections и fragments.

- Clinical extraction service — извлекает МНН, disease-context, УУР/УДД и relation signals.

- Scoring engine — считает pair evidence, context scores, matrix cells и confidence.

- Reviewer service — хранит review actions, adjudication и overrides.

- API service — отдаёт документы, фрагменты, evidence и матрицы.

- Scheduler / queue layer — управляет полными и инкрементальными заданиями.

# 6. Архитектурный контур обработки

| Этап | Компонент | Результат |
| --- | --- | --- |
| 1 | Discovery run | Открыть rubricator, получить DOM и XHR/Fetch payloads, извлечь registry records. |
| 2 | Document probe | Для каждого нового или изменённого документа определить html/pdf availability и источник primary content. |
| 3 | Fetch raw artifacts | Сохранить raw HTML, raw JSON, PDF, headers, hash и ссылку на run. |
| 4 | Normalize | Очистить текст, выделить разделы, таблицы, списки и фрагменты. |
| 5 | Clinical extraction | Извлечь МНН, disease-context, УУР/УДД, relation signals и присвоить extractor confidence. |
| 6 | Candidate generation | Сформировать directed пары МНН только внутри релевантных контекстов. |
| 7 | Evidence and scoring | Сохранить pair_evidence, pair_context_score, matrix_cell и explanation JSON. |
| 8 | Review and release | Показать uncertain cases reviewer, применить overrides и опубликовать release матрицы. |

# 7. Требования к данным и БД

Канонический формат хранения матрицы — long format. Wide matrix допускается только как экспортный слой. Ниже приводится минимально необходимый набор таблиц.

## 7.1 document_registry

| Поле | Описание |
| --- | --- |
| id | PK |
| external_id | Внешний идентификатор документа, если доступен |
| title | Название документа |
| card_url | URL карточки или detail page |
| html_url | URL HTML-представления, если есть |
| pdf_url | URL PDF, если есть |
| specialty | Специальность / рубрика |
| age_group | Возрастная группа |
| status | Статус или тип публикации |
| version_label | Текст версии |
| publish_date | Дата публикации |
| update_date | Дата обновления |
| source_payload_json | Сырой JSON/metadata с discovery |
| discovered_at / last_seen_at | Служебные timestamps |

## 7.2 document_version

| Поле | Описание |
| --- | --- |
| id | PK |
| registry_id | FK на document_registry |
| version_hash | Хэш содержимого или сочетания артефактов |
| source_type_primary | html \| pdf \| html+pdf \| unknown |
| source_type_available | Список доступных source types |
| detected_at | Когда найдена версия |
| is_current | Флаг актуальной версии |

## 7.3 source_artifact

| Поле | Описание |
| --- | --- |
| id | PK |
| document_version_id | FK на document_version |
| artifact_type | html \| json \| pdf |
| raw_path | Путь в object storage |
| content_hash | Хэш артефакта |
| content_type | MIME тип |
| headers_json | HTTP headers |
| fetched_at | Время загрузки |

## 7.4 document_section и text_fragment

| Поле | Описание |
| --- | --- |
| id | PK |
| document_version_id / section_id | Связь с документом и разделом |
| section_path | Путь в иерархии документа |
| section_title | Заголовок секции |
| fragment_order | Порядок фрагмента |
| fragment_type | paragraph \| bullet \| table_row \| caption |
| fragment_text | Нормализованный текст фрагмента |

## 7.5 molecule и molecule_synonym

| Поле | Описание |
| --- | --- |
| molecule_id | PK |
| inn_ru / inn_en | Каноническое название МНН |
| atc_code | Дополнительный классификатор |
| synonym_text | Синоним или вариант написания |
| source | manual \| extracted \| external registry |

## 7.6 clinical_context

| Поле | Описание |
| --- | --- |
| context_id | PK |
| disease_id или disease_name | Нозология |
| line_of_therapy | Линия терапии |
| treatment_goal | Цель лечения |
| population_json | Подгруппа пациентов |
| context_signature | Нормализованный уникальный ключ |

## 7.7 pair_evidence

| Поле | Описание |
| --- | --- |
| evidence_id | PK |
| context_id | FK на clinical_context |
| molecule_from_id / molecule_to_id | Directed пара |
| fragment_id | Опорный фрагмент |
| relation_type | Тип связи |
| uurr / udd | Сила рекомендации и уровень доказательств |
| component scores | role / text / population / parity / practical / penalty |
| final_fragment_score | Итоговый score на уровне фрагмента |
| review_status | auto \| reviewed \| rejected |

## 7.8 pair_context_score

| Поле | Описание |
| --- | --- |
| pair_context_score_id | PK |
| model_version_id | Версия формулы |
| context_id | Контекст |
| molecule_from_id / molecule_to_id | Directed пара |
| substitution_score | Итог по контексту |
| confidence_score | Доверие |
| evidence_count | Число evidence |
| explanation_json | Полное обоснование |

## 7.9 matrix_cell

| Поле | Описание |
| --- | --- |
| matrix_cell_id | PK |
| model_version_id | Версия формулы |
| scope_type / scope_id | global \| disease \| specialty и идентификатор скоупа |
| molecule_from_id / molecule_to_id | Directed пара |
| substitution_score | Итоговая заменяемость |
| confidence_score | Итоговое доверие |
| contexts_count | Число контекстов |
| supporting_evidence_count | Количество supporting evidence |
| explanation_short / explanation_json | Короткое и полное объяснение |

# 8. Правила выбора источника текста

1. Если HTML-представление содержит полный структурированный текст документа, допускается использование HTML как primary source.

2. Если HTML содержит только карточку, витрину, описание или неполный текст, primary source должен быть PDF.

3. Если доступны и HTML, и PDF, система должна сохранять оба артефакта и фиксировать классификацию html+pdf.

4. Выбор primary source хранится в document_version и подлежит пересмотру при обновлении алгоритма оценки полноты.

# 9. Требования к discovery и crawling

- Использовать Playwright для browser automation, потому что ресурс может быть JS-driven.

- Для каждого discovery run логировать XHR/Fetch payloads, HTTP-метаданные, DOM snapshot при необходимости и итоги извлечения.

- Поддерживать два режима: full sync и incremental sync.

- Инкрементальный режим должен сравнивать last_seen, update_date, version_label, хэши артефактов и признаки обновления.

- Следует применять ограничение параллелизма и экспоненциальные ретраи, чтобы не создавать избыточную нагрузку на источник.

# 10. Требования к нормализации текста

| Поле | Описание |
| --- | --- |
| Очистка | Удалять элементы интерфейса, служебные блоки, навигацию, cookie banners и несодержательный шум. |
| Структура | Сохранять иерархию заголовков, абзацев, списков, таблиц и приложений. |
| Фрагментация | Минимальная единица анализа — text_fragment с устойчивым идентификатором. |
| Качество | Каждый документ получает completeness/quality score extraction. |
| Версионирование | Normalizer version обязателен и хранится рядом с normalized artifact. |

# 11. Требования к clinical extraction

- Extractor МНН должен выполнять canonicalization и поддержку синонимов/вариантов написания.

- Extractor disease-context должен определять нозологию, линию терапии, терапевтическую цель и ограничения популяции.

- Extractor УУР/УДД должен поддерживать шаблоны обозначений, встречающиеся в тексте и таблицах.

- Relation-signal extractor должен находить фразы типа «или», «альтернатива», «при непереносимости», «при неэффективности», «в комбинации с», «не рекомендуется».

- Каждое извлечение должно сопровождаться extractor_confidence и version extractor-а.

# 12. Требования к генерации пар и scoring engine

## 12.1 Candidate generation

| Поле | Описание |
| --- | --- |
| Ограничение области | Пары формируются только внутри релевантных disease-contexts, а не по всему корпусу вслепую. |
| Направленность | Система должна хранить i→j и j→i отдельно; асимметрия является нормой. |
| Negative evidence | Должны храниться и случаи, когда текст указывает на отсутствие или ограниченность заменяемости. |

## 12.2 Relation taxonomy

| Поле | Описание |
| --- | --- |
| Минимальный набор | explicit_alternative_same_line, same_line_option, switch_if_intolerance, switch_if_failure, later_line_only, add_on_only, combination_only, different_population, no_substitution_signal |
| Хранение | Relation type хранится отдельно от final score и может быть переопределён reviewer-ом. |

## 12.3 Scoring model

| Поле | Описание |
| --- | --- |
| Компоненты | role overlap, text signal, population overlap, evidence parity via УУР/УДД, practical similarity, penalty |
| Версии | Каждая версия формулы хранится в scoring_model_version с weights_json и code commit hash |
| Confidence | Confidence score рассчитывается отдельно от substitution score и обязателен для product release |

# 13. API-контракты

| Метод | Endpoint | Назначение | Ответ |
| --- | --- | --- | --- |
| GET | /documents | Список документов с фильтрами | paged list registry records |
| GET | /documents/{id} | Карточка документа, версии и source trail | document detail JSON |
| GET | /documents/{id}/content | Нормализованный текст документа | normalized document |
| GET | /documents/{id}/fragments | Фрагменты документа | fragment list |
| POST | /sync/full | Полный обход источника | run_id и статус |
| POST | /sync/incremental | Инкрементальный обход | run_id и статус |
| GET | /matrix | Получить matrix cells по scope/model | long or wide export |
| GET | /matrix/cell | Получить одну directed ячейку с evidence | score, confidence, explanation |

# 14. Форматы обмена данными

- Канонический формат матрицы — long table: from_inn, to_inn, scope, model_version, substitution_score, confidence_score.

- Экспорт для BI — CSV/Parquet long и wide matrix CSV по требованию.

- Полные обоснования — JSONL или JSON API с explanation_json.

- Raw payloads и normalized artifacts хранятся отдельно в object storage и адресуются через metadata в PostgreSQL.

# 15. Очереди задач и scheduler

| Очередь | Задача | Триггер |
| --- | --- | --- |
| discovery | Полный и инкрементальный обход каталога | Планировщик или ручной запуск |
| probe | Определение source availability для документа | Новый или изменённый document_registry record |
| fetch | Загрузка raw артефактов | Результат probe |
| normalize | Построение clean text, sections, fragments | Успешный fetch |
| extract | Clinical extraction | Готовый normalized document |
| score | Расчёт evidence и матриц | Готовый extraction batch или reviewer release |
| reindex | Поисковая и BI-подготовка | После score release |

# 16. Логирование, мониторинг и аудит

- Для каждого run хранить start/finish/status, счётчики discovered/fetched/parsed/failed и подробный stats_json.

- Ошибки сетевого уровня, парсинга и scoring записывать с привязкой к документу и этапу.

- Экспортировать системные метрики в Prometheus/Grafana: run duration, fetch success, parsing completeness, extraction coverage, queue depth.

- Reviewer actions и overrides хранить как неизменяемый audit trail с автором, временем и причиной.

# 17. Требования к внутреннему UI

- Список документов с фильтрами и статусами pipeline.

- Карточка документа: raw source trail, normalized text, sections, fragments, extracted entities.

- Карточка matrix cell: score, confidence, components, evidence list, reviewer history.

- Reviewer queue: uncertain cases, low-confidence cells, конфликтные relation types.

- Dashboard качества: discovery coverage, extraction metrics, scorer drift, release history.

# 18. Тестирование и QA

| Поле | Описание |
| --- | --- |
| Unit tests | Парсеры, normalizer, extractors, scoring components, API serializers. |
| Integration tests | Полный pipeline на фикстурах документов и тестовом object storage. |
| Regression tests | Сравнение результатов extraction и scoring между версиями парсеров и формул. |
| Golden set | Ручная разметка для оценки МНН, contexts, relation types и reviewer agreement. |
| Release QA | Выборочная ручная проверка top matrix shifts и uncertain cases перед релизом версии матрицы. |

# 19. Критерии приёмки по модулям

1. Discovery module: новый документ появляется в registry, повторный запуск не создаёт дубликаты.

2. Fetch module: raw-артефакты сохраняются с hash, headers и ссылкой на document_version.

3. Normalize module: документ разбивается на sections и fragments без критичных потерь структуры.

4. Extraction module: сущности и контексты записываются в БД с extractor version и confidence.

5. Scoring module: directed matrix cell воспроизводимо пересчитывается из evidence и версии модели.

6. API module: выдаёт документы, фрагменты, evidence и matrix cells в согласованных форматах.

7. Reviewer module: ручные overrides сохраняются, аудируются и участвуют в пересчёте релиза.

# 20. План реализации на 8–12 недель

| Этап | Недели | Основные задачи | Результат |
| --- | --- | --- | --- |
| Sprint 1 | 1–2 | Инфраструктура, БД, object storage, базовый FastAPI, discovery prototype | Skeleton platform |
| Sprint 2 | 3–4 | Fetch + raw storage + versioning + normalize v1 + admin screens | Corpus foundation |
| Sprint 3 | 5–6 | Clinical extraction v1, словари МНН, disease-context builder, benchmark set | Clinical corpus |
| Sprint 4 | 7–8 | Candidate generation, relation taxonomy, pair evidence schema | Evidence foundation |
| Sprint 5 | 9–10 | Scoring v1, confidence v1, matrix API, exports | First usable matrix |
| Sprint 6 | 11–12 | Reviewer queue, QA dashboards, release gating, hardening | Governed release |

# 21. Ограничения и допущения

- Источник может менять DOM и frontend-логику; это закладывается как технологический риск.

- HTML не считается полным источником автоматически; полнота должна быть доказана на уровне document probe.

- Матрица не должна интерпретироваться как регуляторное заключение о взаимозаменяемости.

- Релизы матрицы без confidence score и reviewer loop не считаются production-ready.

# 22. Финальные deliverables

| Поле | Описание |
| --- | --- |
| Код | Backend, workers, extraction/scoring modules, admin/reviewer UI |
| Данные | PostgreSQL schema, object storage layout, migrations, fixtures |
| API | Документированные endpoints и форматы ответов |
| Документация | Runbook, guide по релизам матрицы, описание data lineage |
| Качество | Набор тестов, golden set, dashboards и release checklist |
