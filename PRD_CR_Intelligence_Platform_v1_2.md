PRD v1.2

CR Intelligence Platform

| Версия | v1.2 |
| --- | --- |
| Дата | 01.04.2026 |
| Статус | Рабочая версия |
| Назначение | Внутренний продуктовый и технический контур проекта |

> **Superseded:** актуальная концепция knowledge-compilation и matrix output как downstream — в [PRD_CR_Intelligence_Platform_v1_3_kb.md](PRD_CR_Intelligence_Platform_v1_3_kb.md).

> Документ описывает платформу CR Intelligence Platform для получения, нормализации и интерпретации клинических рекомендаций Минздрава РФ с последующим расчётом explainable-матриц клинической заменяемости МНН.

# 1. Видение продукта

CR Intelligence Platform — внутренняя платформа для обнаружения, загрузки, нормализации, структурирования и клинической интерпретации корпуса клинических рекомендаций Минздрава РФ. Итоговый продукт должен поддерживать расчёт explainable-матриц клинической заменяемости МНН, а не только хранить документы.

# 2. Контекст и проблема

- Клинические рекомендации являются ключевым официальным текстовым источником для оценки терапевтических альтернатив и ограничений их применения.

- Сбор документов вручную не масштабируется, плохо аудируется и не позволяет быстро отслеживать обновления.

- Для расчёта матрицы заменяемости недостаточно скачать PDF: нужны версия документа, структура текста, секции, фрагменты, клинические контексты и явные текстовые сигналы замены.

- Команде нужен воспроизводимый pipeline: официальный источник → корпус → evidence layer → матрица заменяемости.

# 3. Цели

## 3.1 Бизнес-цель

| Поле | Описание |
| --- | --- |
| Главная цель | Сократить время от публикации или обновления клинической рекомендации до появления пригодного для анализа, аудируемого и структурированного текста во внутреннем контуре. |
| Ожидаемый эффект | Ускорение исследований рынка, снижение ручного труда, повышение воспроизводимости выводов и подготовка основы для продуктовой матрицы заменяемости МНН. |

## 3.2 Продуктовая цель

| Поле | Описание |
| --- | --- |
| Целевая способность | Платформа должна уметь превращать внешний корпус рекомендаций в knowledge layer: документы, контексты, evidence по парам МНН, directed score и confidence score. |
| Конечный результат | Аналитик выбирает МНН или заболевание и получает объяснимую матрицу заменяемости с провалом до фрагмента текста и версии документа. |

# 4. Принципы продукта

- Official-source first: использовать только официальный источник и его официально опубликованные артефакты.

- Raw-first storage: сначала хранить сырой контент и метаданные, затем строить нормализованные представления.

- Version everything: версионировать источник, парсер, нормализацию, scoring-модели и reviewer overrides.

- Context before score: не считать общую заменяемость без клинического контекста.

- Explainability over black box: каждая ячейка матрицы должна вести к evidence layer.

- Confidence is a first-class artifact: score без confidence не является готовым продуктом.

- Human-in-the-loop: спорные cases и релизные версии матрицы проходят ручную валидацию.

# 5. Пользователи и их задачи

| Роль | Задача | Что получает |
| --- | --- | --- |
| Data engineer | Поддерживать ingestion и обновление корпуса | Стабильный pipeline, логи, ретраи, идемпотентность |
| NLP/ML engineer | Извлекать МНН, контексты и relation signals | Section/fragment dataset, entity layer, evidence schema |
| Фарма-аналитик | Искать клинические альтернативы и ограничения | Матрицу, top substitutes, пояснения и confidence |
| Медицинский эксперт | Проверять сложные интерпретации | Reviewer UI и полный trace до фрагмента |

# 6. Scope

## 6.1 In scope

| Поле | Описание |
| --- | --- |
| Источник | Рубрикатор КР Минздрава РФ и связанные с ним официальные артефакты. |
| Сбор данных | Discovery каталога, загрузка HTML/JSON/PDF, определение доступных типов контента, хранение raw-артефактов. |
| Подготовка текста | Очистка, секционирование, разбиение на фрагменты, версионирование и quality scoring. |
| Clinical intelligence | Извлечение МНН, нозологий, линий терапии, ограничений популяции, УУР/УДД и relation signals. |
| Evidence и matrix | Candidate pairs, pair evidence, context score, matrix cells, confidence score и reviewer loop. |

## 6.2 Out of scope

| Поле | Описание |
| --- | --- |
| Медицинские решения | Платформа не заменяет врачебную экспертизу и не является инструментом принятия клинических решений. |
| Юридическая взаимозаменяемость | Регуляторное определение взаимозаменяемости в смысле 61-ФЗ находится вне scope продукта. |
| Публичный портал | Внешний пользовательский портал и публикация корпуса наружу не входят в MVP и ближайшие фазы. |

# 7. Ключевые capability layers

| Поле | Описание |
| --- | --- |
| Layer A — Source ingestion | Каталог документов, метаданные, raw-артефакты, версии, html/pdf classification. |
| Layer B — Text structuring | Нормализация текста, sections, fragments, quality score extraction. |
| Layer C — Clinical extraction | МНН, disease/context, линия терапии, популяционные ограничения, УУР/УДД. |
| Layer D — Evidence modeling | Candidate pairs, relation types, fragment-level evidence, audit trail. |
| Layer E — Scoring | Context score, global score, confidence score, versioned scoring model. |
| Layer F — Review & governance | Reviewer workflow, overrides, QA dashboards, release gates. |

# 8. Функциональные требования

1. Система должна автоматически обнаруживать документы, карточки, версии и признаки обновления в рубрикаторе.

2. Система должна уметь собирать и сохранять HTML, JSON и PDF-артефакты, а также технические метаданные запросов и ответов.

3. Для каждого документа система должна классифицировать доступность контента: html_only, pdf_only, html_plus_pdf или unknown.

4. Система должна уметь строить нормализованный текст документа и разрезать его на разделы и фрагменты с устойчивыми идентификаторами.

5. Система должна извлекать МНН, disease-context, терапевтическую линию, ограничения популяции, УУР/УДД и текстовые сигналы альтернативности.

6. Система должна формировать candidate pairs только внутри релевантных клинических контекстов и хранить directed evidence по парам МНН.

7. Система должна уметь рассчитывать context score, global matrix score и confidence score по версии формулы.

8. Система должна предоставлять API и reviewer UI для чтения, фильтрации, пересчёта и ручной валидации.

# 9. Нефункциональные требования

| Поле | Описание |
| --- | --- |
| Надёжность | Идемпотентные запуски, безопасные ретраи, отсутствие потери ранее собранного корпуса. |
| Воспроизводимость | Одинаковый raw-артефакт при одинаковой версии парсера даёт одинаковый нормализованный результат. |
| Наблюдаемость | Логи по этапам, статус run, счётчики discovered/fetched/parsed/failed, алерты на рост ошибок. |
| Масштабируемость | Поддержка полного и инкрементального обхода; масштабирование по документам и терапевтическим областям. |
| Аудируемость | Для любого matrix cell доступен путь: версия матрицы → evidence → фрагмент → документ → raw source. |
| Операционная согласованность | API и worker должны работать в одном runtime profile и использовать один и тот же broker/result backend для очередей. |
| Безопасность | Ролевой доступ к raw-артефактам, audit log reviewer actions, ограничение на внешнее распространение корпуса. |

# 10. Источниковая стратегия

- HTML/JSON-first discovery: для каталога, фильтров, карточек документов, метаданных и признаков обновления.

- PDF-safe full text: если HTML не доказывает полноту и структурированность, PDF рассматривается как основной источник текста.

- Гибридный режим допустим и предпочтителен: карточка и метаданные из web-app, полный текст — из лучшего доступного полного источника.

- Каждый документ получает classification источника: html, pdf, html+pdf или unknown.

# 11. Основные пользовательские сценарии

- Аналитик выбирает МНН и получает список top-N клинических замен в заданной нозологии, а также confidence и обоснование.

- Data engineer запускает инкрементальную синхронизацию и видит, какие документы обновились и какие этапы упали.

- Medical reviewer открывает спорную ячейку матрицы, читает supporting evidence и подтверждает/исправляет relation type.

- NLP engineer выгружает fragments + extracted entities для обучения и оценки новых extractors.

# 12. MVP

## 12.1 Что входит в MVP

| Поле | Описание |
| --- | --- |
| Corpus foundation | Discovery каталога, загрузка raw-артефактов, normalized text, section/fragment split, базовый API. |
| Admin и мониторинг | Внутренний admin UI, история запусков, quality dashboards, контроль completeness. |
| Выходы | Корпус документов и фрагментов, пригодный для начала clinical extraction в следующей фазе. |

## 12.2 Что намеренно не входит в MVP

| Поле | Описание |
| --- | --- |
| Clinical extraction | Полноценное извлечение МНН, disease-context, relation signals и УУР/УДД. |
| Матрица | Финальная матрица заменяемости как продуктовый артефакт. |
| Reviewer governance | Зрелый reviewer workflow и formal release gating. |

# 13. Детализированный Post-MVP roadmap

| Фаза | Цель | Ключевые deliverables | Выходной артефакт | Критерий перехода |
| --- | --- | --- | --- | --- |
| Phase 2<br>Clinical Structuring | Разметить корпус клиническими сущностями и контекстами | Словари МНН, extractors, context builder, gold set | Clinical corpus | Приемлемые baseline precision/recall и usable coverage |
| Phase 3<br>Pair Candidate & Relation | Научить систему генерировать осмысленные directed пары | Candidate engine, relation taxonomy, reviewer queue | Candidate pairs | Допустимая доля мусорных пар и usable relation baseline |
| Phase 4<br>Evidence & Scoring | Построить explainable evidence layer и версии формулы | Pair evidence, scoring v1, confidence v1, explanation JSON | Context scores | Reviewer понимает происхождение чисел без чтения кода |
| Phase 5<br>Matrix Productization | Сделать матрицу рабочим продуктом для аналитиков | Matrix builder, exports, matrix explorer UI, diffs | Matrix releases | Аналитики используют матрицу без участия разработчика |
| Phase 6<br>Governance | Встроить QA, reviewer workflows и release gates | Reviewer UI, adjudication flow, audit log, golden set governance | Governed product | Есть repeatable QA cycle и quality gates |
| Phase 7–8<br>Advanced Intelligence & Integration | Усилить product ML/LLM и интегрировать в бизнес-аналитику | ML-assisted classifier, active learning, warehouse/API integration | Business-grade product | Матрица используется в регулярных аналитических сценариях |

# 14. Quality gates

| Поле | Описание |
| --- | --- |
| Gate A — Source quality | Стабильный discovery, низкая доля дублей, высокая полнота raw-артефактов. |
| Gate B — Text quality | Приемлемая полнота normalized text, качественный section split, низкая регрессия парсеров. |
| Gate C — Clinical extraction quality | Baseline precision/recall extractors и качественная canonicalization МНН. |
| Gate D — Relation quality | Reviewer agreement по relation types и приемлемая точность candidate generation. |
| Gate E — Score quality | Понятность explanations, управляемая чувствительность формулы, confidence коррелирует с уверенностью reviewer. |
| Gate F — Product usefulness | Аналитики действительно отвечают на substitution-вопросы через продукт, а не вручную. |

# 15. Риски и меры снижения

| Риск | Описание | Снижение риска |
| --- | --- | --- |
| Недооценка reviewer effort | Часть сложных клинических связей невозможно надежно закрыть без ручной экспертизы. | Узкий пилот, triage ambiguous cases, QA sampling с раннего этапа. |
| Нестабильный web-интерфейс | Фронтенд или DOM сайта может измениться. | Опора на XHR/JSON, raw capture network payloads, fallback на DOM и PDF. |
| Неполный HTML | Карточка документа может не содержать полный нормативный текст. | Правило HTML if proven complete, иначе PDF primary. |
| Завышение score | Система может путать заменяемость, комплементарность и последовательное применение. | Directed evidence, relation taxonomy, confidence score, reviewer approval. |

# 16. Метрики успеха

- Platform metrics: coverage discovery, raw fetch success, normalized completeness, section split quality.

- Clinical metrics: precision/recall извлечения МНН, disease-context и УУР/УДД.

- Evidence metrics: candidate precision, reviewer agreement, share of usable evidence.

- Matrix metrics: доля ячеек с usable confidence, устойчивость top substitutes, качество explanations.

- Business metrics: время ответа на substitution-вопрос, число реальных аналитических сценариев, встроенность в регулярные отчёты.

# 17. Acceptance criteria

1. Продукт стабильно собирает и версионирует корпус клинических рекомендаций.

2. Для любого фрагмента и matrix cell существует воспроизводимый audit trail.

3. После Post-MVP roadmap платформа строит directed explainable matrix и отдельный confidence score.

4. Есть reviewer workflow и quality gates перед релизом новой версии матрицы.

5. Матрица становится используемым аналитическим артефактом, а не экспериментальным скриптом.

# 18. Операционные требования MVP

- Для production-подобного smoke допускается только согласованный профиль запуска: host-only или docker-compose-only.

- API и worker обязаны использовать одинаковые значения `CRIN_CELERY_BROKER_URL` и `CRIN_CELERY_RESULT_BACKEND`; смешивание `localhost` и docker network hostnames в одном запуске запрещено.

- Для worker, использующего sync SQLAlchemy engine, обязательна зависимость совместимого PostgreSQL драйвера (`psycopg2-binary` или эквивалент).

- Smoke-проход считается валидным, если полный sync переходит в `completed`, `stats_json` содержит минимум полей (`discovery_service_version`, `run_type`, `wall_time_seconds`, `total_discovered`, `duplicates_detected`, `coverage_percent`), а `/documents` возвращает согласованные записи.

- Run со статусом `completed` и `discovered_count = 0` считается валидным для smoke при выполнении структурных и интеграционных проверок.

- Любые операции с контейнерами и портами должны соответствовать политике из [ISOLATION_POLICY.md](ISOLATION_POLICY.md).

# 19. Definition of Done (MVP)

- Канонический DoD определяется в [DOD_MVP.md](DOD_MVP.md).

- PRD использует этот DoD без дублирования критериев; любые изменения DoD вносятся сначала в канонический файл.

# 20. Глоссарий

| Поле | Описание |
| --- | --- |
| МНН | Международное непатентованное наименование действующего вещества. |
| Clinical context | Нормализованный контекст применения: заболевание, линия терапии и ограничения. |
| Directed score | Оценка заменяемости i → j, которая не обязана совпадать с j → i. |
| Confidence score | Отдельная метрика доверия к substitution score. |
