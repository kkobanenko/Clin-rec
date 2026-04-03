PRD v1.4

CR Intelligence Platform

| Версия | v1.4 |
| --- | --- |
| Дата | 03.04.2026 |
| Статус | Рабочая версия |
| Назначение | Внутренний продуктовый и технический контур проекта |

> Документ описывает CR Intelligence Platform как **внутреннюю LLM-native платформу знаний** для фармы и клинических исследований. Продукт строит и поддерживает **compiled knowledge base** (markdown-like) из официальных источников клинических рекомендаций Минздрава РФ и связанных артефактов; поверх неё — **evidence layer** и **analytic outputs**. **Матрица клинической заменяемости МНН** остаётся **приоритетным производным продуктовым артефактом**, но не единственной конечной целью: она рассчитывается **ниже по конвейеру** и опирается на устойчивый слой знаний и провенанса.

# 1. Видение продукта

CR Intelligence Platform — внутренняя **knowledge-compilation** платформа: сбор официальных источников, **source vault**, **normalized corpus**, компиляция **compiled knowledge base**, построение **evidence layer**, выпуск **analytic outputs** и **matrix output** как производных, объяснимых артефактов.

Ключевая цепочка данных:

`official sources → source vault → normalized corpus → compiled knowledge base → evidence layer → analytic outputs → matrix output`

Платформа должна не только хранить документы и извлекать сущности, но и поддерживать версионируемую **Markdown-based knowledge base** — рабочую память продукта, которую LLM и сервисы могут безопасно пополнять, переиспользовать и проверять.

Переиспользуемые выходы продукта (не исчерпывающий список):

1. **Source digests** — краткие сводки по источникам.
2. **Entity pages** и **concept pages** (включая индексные страницы).
3. **Comparative notes** / synthesis — сравнительные и сводные заметки.
4. **Reports**, **Markdown memos**, **slide decks**.
5. **Substitution matrix** (explainable matrix output) и связанные экспорты.

## 1.1 Почему сейчас (Why now)

- **Long-context LLM** и **markdown-native** инструменты делают практичным хранение и компиляцию знаний в виде управляемых артефактов, а не только разовых ответов.
- **Compiled KB** снижает повторные затраты токенов и повторный ручной разбор одних и тех же документов.
- **Одна инфраструктура** обслуживает и исследовательские ad hoc запросы, и **production scoring** матрицы на одном провенансе и версионировании.

# 2. Контекст и проблема

- Клинические рекомендации — ключевой официальный источник для оценки терапевтических альтернатив и ограничений.
- Простого скачивания PDF и парсинга недостаточно: нужны версия документа, структура, клинические контексты, связи сущностей, **provenance** и механизм накопления промежуточного знания.
- **Сырые документы сами по себе не создают переиспользуемое организационное знание**: без компиляции и артефактов знание не становится активом команды.
- **Аналитические ответы растворяются** в чатах, документах и временных выгрузках вместо того, чтобы становиться версионируемыми артефактами с провенансом.
- **Нет устойчивого слоя** для понятий (concepts), сущностей (entities), явных **противоречий** и **открытых вопросов**, на который можно опираться в продуктах и исследованиях.
- **Скоринг матрицы без поддерживаемого knowledge layer** хрупок и дорог в эволюции: смена правил и моделей требует полного пересмотра без накопленного слоя утверждений и ссылок на источники.
- Разрозненные скрипты не дают воспроизводимой внешней памяти проекта.
- Команде нужен контур, где результаты запросов становятся новыми управляемыми артефактами базы знаний.

# 3. Цели

## 3.1 Бизнес-цель

| Поле | Описание |
| --- | --- |
| Главная цель | Сократить время от публикации или обновления клинической рекомендации до появления пригодного для анализа, аудируемого и повторно используемого знания во внутреннем контуре. |
| Ожидаемый эффект | Ускорение фарма-исследований, снижение ручного труда, институциональная память и устойчивые explainable-матрицы заменяемости МНН поверх compiled KB. |

## 3.2 Продуктовая цель

| Поле | Описание |
| --- | --- |
| Целевая способность | Превращать внешний корпус рекомендаций в управляемый knowledge layer: source vault, normalized corpus, source digests, entity/concept pages, **provenance-aware claims**, evidence по парам МНН, directed score и confidence score; **генерация матрицы** — как направленный downstream-результат. |
| Конечный результат | Аналитик получает traceable knowledge outputs (статьи, summaries, conflicts, gaps) и при необходимости **matrix output** с провалом до фрагмента, claim, артефакта и raw source. |

## 3.3 Knowledge-цель

| Поле | Описание |
| --- | --- |
| Целевая память | Накапливать результаты в **compiled knowledge base**, а не только выдавать одноразовые ответы; поддерживать артефакты и их версии. |
| Целевая дисциплина | Нетривиальные выводы — как **fact**, **inference** или **hypothesis** с **provenance** или цепочкой evidence. |

## 3.4 Цели уровня платформы (дополнительно)

| Цель | Описание |
| --- | --- |
| Source vault | Воспроизводимое хранение официальных raw-артефактов и метаданных ingestion. |
| Compiled knowledge base | Постоянное ведение страниц, индексов, связей и health-процессов вокруг KB. |
| Provenance-aware claims | Явная типизация и привязка утверждений к источникам и фрагментам. |
| Reusable artifacts | Memos, отчёты, слайды, сравнительные заметки и др. как повторно используемые продукты. |
| Knowledge health checks | Lint, противоречия, пробелы, устаревание — часть нормальной эксплуатации. |
| Matrix generation (downstream) | Матрица как производный, объяснимый артефакт поверх evidence и KB. |

# 4. Принципы продукта

- Official-source first: только официальный источник и официально опубликованные артефакты как основание корпуса.
- Raw-first storage: сначала raw и сетевые метаданные, затем нормализация и knowledge artifacts.
- **Knowledge compilation over raw retrieval**: система компилирует знание, а не ограничивается поиском по документам.
- **Provenance-first**: нетривиальные утверждения без основания в источнике/evidence не считаются готовым продуктом.
- **Separate fact / inference / hypothesis**: тип claim обязан быть явным.
- **Outputs are reusable artifacts**: memo, отчёты, слайды оформляются как артефакты с метаданными и провенансом.
- **Conflicts must stay visible**: противоречия фиксируются записями (conflict reports / notes), а не скрываются правками текста.
- **Health checks are part of normal operation**: lint и проверки качества KB — не разовый проект.
- **Reviewed knowledge must not be silently overwritten**: пересборка не затирает проверенное знание без явного процесса (версия, review log, политика recompile).
- Compile, don’t just retrieve (синонимично knowledge compilation): компилировать промежуточные представления знания.
- Version everything: версионировать источник, парсер, normalizer, extractor, knowledge compiler, scoring-модели, reviewer overrides и output artifacts.
- Context before score: не считать общую заменяемость без клинического контекста.
- Explainability over black box: **matrix output** и существенные тезисы KB ведут к evidence layer и источникам.
- Confidence is first-class: score, summary или synthesis без confidence и provenance не являются готовыми продуктами.
- Human-in-the-loop: спорные cases, конфликты и релизы проходят ручную валидацию где требуется.
- Keep the corpus alive: ответы, отчёты и слайды могут **output filing** в KB после quality gate.

# 5. Пользователи и их задачи

| Роль | Задача | Что получает |
| --- | --- | --- |
| Data engineer | Поддерживать ingestion, storage и обновление корпуса | Стабильный pipeline, логи, ретраи, идемпотентность, object lineage |
| NLP/ML engineer | Извлекать МНН, контексты и relation signals | Section/fragment dataset, entity layer, evidence schema, gold sets |
| Knowledge engineer / research operator | Компилировать KB, канонические страницы, индексы, политики recompile | Шаблоны артефактов, индексы, traceability, automated checks |
| LLM workflow operator | Настраивать и запускать LLM-конвейеры компиляции и генерации при соблюдении guardrails | Промпты, версии генераторов, очереди compile/generate, отчёты о прогонах |
| Reviewer (claims / conflicts) | Валидировать спорные утверждения, конфликты источников, high-impact claims | Reviewer UI, очередь конфликтов, audit trail до фрагмента |
| Фарма-аналитик | Искать альтернативы, ограничения, рыночные импликации; потреблять memos, слайды, сравнительные синтезы | Matrix views, top substitutes, knowledge pages, comparative syntheses, exports |
| Медицинский эксперт | Проверять сложные клинические интерпретации | Reviewer UI, полный trace до фрагмента, conflict queue |
| Руководитель продукта / исследования | Получать устойчивые аналитические артефакты | Markdown briefs, deck-ready summaries, diffs версий знаний и матрицы |

# 6. Scope

## 6.1 In scope

| Поле | Описание |
| --- | --- |
| Источник | Рубрикатор КР Минздрава РФ и связанные официальные артефакты. |
| Source vault | Discovery, загрузка HTML/JSON/PDF, raw storage, сетевые payloads, технические метаданные. |
| Normalized corpus | Очистка, секционирование, фрагменты, quality scoring, canonical document representation. |
| Knowledge compilation | Source digests, entity pages, concept pages, synthesis notes, **conflict tracking**, **open questions / gap registry**, индексы, glossary. |
| **Artifact generation and filing back** | Генерация outputs и контролируемое помещение в KB (output filing) после quality gate. |
| **Health / lint workflows** | Противоречия, пробелы, устаревание, orphans, дубликаты — см. operational requirements в TZ. |
| Clinical intelligence | Извлечение МНН, нозологий, линий терапии, популяций, УУР/УДД, relation signals. |
| Evidence и **matrix output** | Candidate pairs, pair evidence, context score, matrix cells, confidence score, reviewer loop; матрица остаётся **priority product output**. |
| Analytic outputs | Markdown memo, report, slide decks, chart specs, выгрузки. |
| Knowledge QA | Явные проверки качества KB и output layer (см. TZ). |

## 6.2 Out of scope

| Поле | Описание |
| --- | --- |
| Медицинские решения | Не замена врачебной экспертизы и не инструмент клинических решений. |
| Юридическая взаимозаменяемость | Регуляторная ВЗ в смысле 61-ФЗ вне scope. |
| Полностью автономное авторство LLM | High-impact артефакты без traceability и release-check невалидны. |
| **Public-facing wiki portal** | Внешняя витрина корпуса и публичная wiki не входят в продукт. |
| **Open collaborative editing внешними пользователями** | Совместное редактирование KB неавторизованными внешними пользователями вне scope. |
| **Early-stage finetuning как core deliverable** | Обучение/дообучение моделей как обязательный результат релиза платформы не входит в core scope (возможны точечные эксперименты вне обещаний поставки). |

# 7. Целевая модель продукта

## 7.1 Шесть capability-слоёв (A–F)

| Слой | Назначение | Основной артефакт |
| --- | --- | --- |
| **Layer A — Source ingestion и source vault** | Официальный воспроизводимый слой raw | Raw HTML/JSON/PDF + metadata |
| **Layer B — Normalization and structuring** | Нормализованный текст, секции, фрагменты | Normalized corpus, sections, fragments |
| **Layer C — Knowledge compilation** | Управляемые страницы и артефакты знания | Source digests, entity/concept pages, indexes, conflicts, open questions |
| **Layer D — Clinical extraction и evidence modeling** | Извлечение сущностей и построение evidence | Clinical entities, pair_evidence, context evidence |
| **Layer E — Analytic outputs и publishing** | Продукты для людей и downstream-систем | Memos, slides, reports, chart specs, **matrix exports/snapshots** |
| **Layer F — Review, linting, governance, release control** | Качество, конфликты, релизы | Review queues, lint reports, release gates, audit log |

**Матрица заменяемости** остаётся **приоритетным product output**: **compiled knowledge base** и **evidence layer** существуют для того, чтобы **matrix output** был устойчивее, переиспользуемее и **объяснимее** (explainable substitution matrix).

## 7.2 Почему knowledge base — отдельный слой

Knowledge base — рабочая память платформы, а не витрина PDF. Она должна:

- уменьшать повторное чтение полного корпуса;
- переводить raw в устойчивые представления;
- накапливать промежуточные результаты анализа;
- хранить открытые вопросы и противоречия явно;
- обеспечивать reuse между extraction, scoring и ad hoc research.

# 8. Типы knowledge artifacts

| Тип артефакта | Назначение | Пример |
| --- | --- | --- |
| Source digest | Краткая нормализация одного источника | Страница по одной клинической рекомендации |
| Entity page | Каноническая карточка сущности | МНН, нозология, схема терапии |
| Concept page | Понятие или методика | УУР/УДД, clinical context, relation taxonomy |
| Synthesis note | Сводка / сравнение по нескольким документам | Сравнение терапевтических альтернатив |
| Conflict report / note | Явная фиксация противоречий | Несогласованность рекомендаций или версий |
| Open question | Явная фиксация пробела | Недостаточно данных по линии терапии |
| Decision note | Обоснование решений модели/процесса | Изменение scoring weights |
| Output note / slide deck | Производные аналитические документы | Memo, deck, chart spec |

# 9. Функциональные требования

1. Система должна автоматически обнаруживать документы, карточки, версии и признаки обновления в рубрикаторе.
2. Система должна собирать и сохранять HTML, JSON и PDF-артефакты, а также технические метаданные запросов и ответов.
3. Для каждого документа система должна классифицировать доступность контента: html_only, pdf_only, html_plus_pdf или unknown.
4. Система должна строить нормализованный текст документа и разрезать его на разделы и фрагменты с устойчивыми идентификаторами.
5. Система должна формировать knowledge artifacts по шаблонам: source digest, entity page, concept page, synthesis notes, conflict records, open questions.
6. Каждый knowledge artifact должен хранить **provenance**: использованные источники, тип утверждения (**fact / inference / hypothesis**), confidence и дату последней проверки где применимо.
7. Система должна извлекать МНН, disease-context, терапевтическую линию, ограничения популяции, УУР/УДД и текстовые сигналы альтернативности.
8. Система должна формировать candidate pairs только внутри релевантных клинических контекстов и хранить directed evidence по парам МНН.
9. Система должна рассчитывать context score, global matrix score и confidence score по версии формулы (**matrix output** как downstream).
10. Система должна поддерживать **output filing** производных outputs в knowledge base после прохождения quality checks.
11. Система должна выполнять **knowledge health checks**: противоречия, пробелы, устаревшие артефакты, orphans, кандидаты на новые статьи.
12. Система должна предоставлять API и internal UI для чтения, фильтрации, пересчёта, QA и ручной валидации.

# 10. Нефункциональные требования

| Поле | Описание |
| --- | --- |
| Надёжность | Идемпотентные запуски, безопасные ретраи, отсутствие потери корпуса и knowledge artifacts. |
| Воспроизводимость | Одинаковый raw при одинаковых версиях парсера и compiler даёт согласованный normalized/compiled результат. |
| Наблюдаемость | Логи ingest, compile, extract, score, review; run status; счётчики discovered/fetched/parsed/compiled/failed. |
| Масштабируемость | Full и incremental обход; масштабирование по документам, сущностям и типам артефактов. |
| Аудируемость | Две воспроизводимые цепочки (см. §18): **output artifact → claims → fragments/sources → document → raw source**; **matrix cell → evidence → claims/artifacts → fragments → document → raw source**. |
| Управление качеством знания | Явные conflicts, gaps, stale artifacts, reviewer-approved resolutions. |
| Операционная согласованность | API, worker и compiler в одном runtime profile; единые брокеры/хранилища. |
| Безопасность | Ролевой доступ, audit log reviewer actions, ограничение внешнего распространения корпуса. |

# 11. Источниковая стратегия

- HTML/JSON-first discovery: каталог, фильтры, карточки, метаданные, признаки обновления.
- PDF-safe full text: при неполноте HTML primary — PDF.
- Гибридный режим: карточка из web-app, полный текст из лучшего полного источника.
- Classification: html, pdf, html+pdf или unknown.
- Ни один knowledge artifact не ссылается на unofficial source как на первичное основание.

# 12. Основные пользовательские сценарии

- Аналитик выбирает МНН и получает top-N замен в нозологии, confidence, evidence summary и связанные knowledge pages (**matrix output** + KB).
- Аналитик задаёт вопрос и получает memo в Markdown с выводами, конфликтами и ссылками на source digests.
- Data engineer запускает инкрементальный sync и видит обновлённые документы, **recompile** затронутых KB-страниц и падения этапов.
- Knowledge engineer / research operator запускает health check и получает inconsistent pages, missing links, stale summaries, gap suggestions.
- LLM workflow operator отслеживает прогоны compile/generate и версии генераторов.
- Reviewer открывает спорную ячейку матрицы или conflict report, читает evidence и подтверждает/правит relation или claim.
- NLP engineer выгружает fragments, entities и reviewer labels для оценки extractors.

# 13. MVP

## 13.1 Что входит в MVP

| Поле | Описание |
| --- | --- |
| Source vault | Discovery, fetch, raw storage, версии документов, базовый audit raw layer. |
| Normalized corpus | Normalized text, section/fragment split, базовый API документов/фрагментов. |
| Compiled KB (foundation) | Source digests, entity pages, concept pages / index pages, master index. |
| Artifact provenance | Модель связей артефактов с источниками и фрагментами; типизация claims где внедрено. |
| Basic health checks | Минимальный lint: provenance gaps, orphan/stale сигналы согласно [DOD_MVP.md](DOD_MVP.md) фазы расширения. |
| Basic output generation | Минимальная генерация memo/report/slide outline с manifest (контур согласуется с DoD: baseline vs phase 2). |
| Admin и мониторинг | Internal UI baseline, история run, контроль completeness. |

Канонические критерии приёмки **baseline** MVP (smoke, pipeline, corpus) — в [DOD_MVP.md](DOD_MVP.md). Расширения KB/output перечислены там как **Phase 2** цели без нарушения текущего зелёного smoke.

## 13.2 Что намеренно не входит в baseline MVP

| Поле | Описание |
| --- | --- |
| Полноценный scoring product | Промышленная **matrix output** со всеми product gates — **post-MVP**, если не реализована частично. |
| Зрелый reviewer governance | Полный adjudication и formal release gating для всех artifacts — post-MVP / Phase 2+. |
| Полностью автоматическое output filing | Автопубликация любого generated output без проверок — вне scope. |

# 14. Детализированный roadmap

| № | Фаза | Цель | Ключевые deliverables | Критерий перехода |
| --- | --- | --- | --- | --- |
| 1 | Source Vault Foundation | Воспроизводимый vault | Discovery, probe, fetch, raw storage, metadata | Стабильный ingest, audit trail к raw |
| 2 | Compiled KB Foundation | Минимальная KB | Digests, entity/concept pages, indexes, templates | KB используется для навигации и повторных запросов |
| 3 | Provenance and Health Checks | Качество KB | Claim typing, provenance coverage, lint rules, stale/orphan | Контролируемые health metrics |
| 4 | Clinical Extraction on top of KB | Структурирование корпуса | МНН, contexts, extractors, gold set | Baseline precision/recall |
| 5 | Evidence Modeling and Scoring | Explainable evidence | Pair evidence, scoring v1, confidence v1, explanations | Reviewer понимает числа без кода |
| 6 | Matrix Productization | **Matrix output** как продукт | Matrix API, exports, snapshots, top-N UX | Устойчивые substitutes и explanations |
| 7 | Reviewer Governance | Управляемые релизы | Adjudication, audit log, release gates | Повторяемый QA cycle |
| 8 | Advanced Intelligence / Warehouse / BI | Интеграции | Warehouse, BI exports, ML-assisted loops | Регулярные бизнес-сценарии |

Содержательные детали прежних Phase 1–8 (пары, relation taxonomy, analytic outputs) **перенесены** внутрь строк таблицы выше без потери смысла.

# 15. Quality gates

| Поле | Описание |
| --- | --- |
| Gate A — Source quality | Стабильный discovery, низкие дубли, полнота raw. |
| Gate B — Text quality | Полнота normalized text, качество section split, низкая регрессия парсеров. |
| Gate C — Knowledge quality | Provenance, orphan rate, согласованность индексов, stale rate. |
| Gate D — Clinical extraction quality | Precision/recall, canonicalization МНН. |
| Gate E — Relation quality | Reviewer agreement, качество candidates. |
| Gate F — Score quality | Explanations, sensitivity, confidence vs reviewer. |
| Gate G — Output usefulness | Reuse memos/slides/**matrix views** vs ручная сборка. |

# 16. Риски и меры снижения

| Риск | Описание | Снижение риска |
| --- | --- | --- |
| Галлюцинации compiler | Смешение fact/inference/hypothesis | Шаблоны, provenance, claim typing, reviewer gates |
| Semantic drift | Ухудшение при переписывании | Immutable raw, versioned compiled, diff review, health checks |
| Knowledge pollution | Засорение KB outputs | Output filing только через quality gate, отдельный output layer |
| Нестабильный web | DOM меняется | XHR/JSON, raw payloads, fallback PDF |
| Неполный HTML | Неполный текст | Правило полноты, PDF primary |
| Завышение score | Путаница отношений | Directed evidence, taxonomy, confidence, reviewer |

# 17. Метрики успеха

- Platform: coverage discovery, raw fetch success, normalized completeness, section split quality.
- Knowledge: число usable digests; **доля источников с digest**; **доля canonical entities со страницами**; страницы с provenance; orphan rate; **stale artifact rate**; **contradiction detection rate**; resolution rate.
- **Provenance completeness**: доля non-trivial claims с валидными source links.
- **Reviewer acceptance rate** for generated claims (где применимо).
- **Output reuse rate**: повторное использование memo/slides/reports vs разовые генерации.
- **Снижение повторного ручного ресёрча** (время/число итераций на типовой вопрос).
- Clinical: precision/recall МНН, disease-context, УУР/УДД.
- Evidence: candidate precision, reviewer agreement, usable evidence share.
- Matrix: доля ячеек с usable confidence, стабильность top substitutes, качество explanations.
- Business: время ответа на substitution-вопрос, число сценариев, встроенность в отчёты.

# 18. Acceptance criteria

1. Продукт стабильно собирает и версионирует корпус клинических рекомендаций (**source vault** + **normalized corpus**).
2. Платформа поддерживает **compiled knowledge base** с индексами, digests, entity/concept pages.
3. Для любого high-impact тезиса и **matrix cell** существует воспроизводимый audit trail:  
   - **output artifact → claims → fragments/sources → document → raw source**;  
   - **matrix cell → evidence → claims/artifacts → fragments → document → raw source**.
4. После roadmap-фаз платформа строит directed explainable **matrix output** и confidence score.
5. Есть reviewer workflow и quality gates перед релизом knowledge artifacts и версий матрицы.
6. KB и **matrix output** — используемые аналитические артефакты, не разовые скрипты.

# 19. Операционные требования MVP

- Для production-подобного smoke допускается только согласованный профиль: host-only или docker-compose-only.
- API, worker и compiler используют одинаковые `CRIN_CELERY_BROKER_URL` и `CRIN_CELERY_RESULT_BACKEND`; смешивание `localhost` и docker hostnames запрещено.
- Worker с sync SQLAlchemy: обязателен `psycopg2-binary` или эквивалент.
- Smoke: полный sync → `completed`, `stats_json` с полями (`discovery_service_version`, `run_type`, `wall_time_seconds`, `total_discovered`, `duplicates_detected`, `coverage_percent`), `/documents` согласован с данными registry.
- Эндпоинты KB/output (например `/kb/indexes/master`, `/kb/artifacts`) — по мере реализации согласно [TZ_CR_Intelligence_Platform_v1_2_kb.md](TZ_CR_Intelligence_Platform_v1_2_kb.md); baseline DoD не требует их для зелёного smoke, см. [DOD_MVP.md](DOD_MVP.md).
- Run `completed` с `discovered_count = 0` валиден для smoke при структурных проверках.
- Контейнеры и порты — [ISOLATION_POLICY.md](ISOLATION_POLICY.md).

# 20. Definition of Done (MVP)

- Канонический DoD — [DOD_MVP.md](DOD_MVP.md) (baseline + Phase 2 цели).
- PRD не дублирует конфликтующие критерии; изменения DoD — сначала в DOD_MVP.md.

# 21. Глоссарий

| Термин | Описание |
| --- | --- |
| Source vault | Слой raw-источников и технических артефактов; основание для всех производных. |
| Normalized corpus | Нормализованный текст, секции и фрагменты поверх vault. |
| Compiled knowledge base | Версионируемые knowledge artifacts, собираемые из corpus и процессов компиляции. |
| Knowledge artifact | Управляемая страница или запись KB: digest, entity/concept page, synthesis, conflict report и т.д. |
| Claim | Атомарное утверждение с типом **fact / inference / hypothesis** и provenance. |
| Provenance | Связь утверждения/артефакта с источником: документ, версия, фрагмент, evidence. |
| Evidence layer | Фрагментно-опирающиеся основания для scoring и объяснений (**matrix output** включая). |
| Health check | Автоматические проверки качества KB: lint, stale, orphans, contradictions, gaps. |
| Output filing | Контролируемое помещение generated output обратно в KB с linkage и quality gate. |
| Matrix output | Explainable матрица клинической заменяемости МНН и связанные экспорты/snapshots (**downstream** от KB и evidence). |
