# Когда появляются данные в хранилище и в БД

Краткая схема для операторов и разработчиков (соответствует текущему коду pipeline).

## PostgreSQL


| Стадия                                                                  | Что появляется                                                                                                                                                                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Discovery** (sync full/incremental)                                   | `pipeline_run`, строки `**document_registry`** — каталог: заголовки, URL карточек/HTML/PDF, метаданные рубрикатора. Полного текста документа в БД на этом шаге нет.                                                                                                                                                                                                                               |
| **Probe** (по цепочке после discovery)                                  | `**document_version`** (в т.ч. `source_type_primary`), при необходимости новые версии.                                                                                                                                                                                                                                                                                                            |
| **Fetch**                                                               | `**source_artifact`**: ссылка `raw_path` на объект в S3/MinIO, хэш, тип.                                                                                                                                                                                                                                                                                                                          |
| **Normalize**                                                           | `**document_section`**, `**text_fragment`** — нормализованный текст и структура (результат индексирования/парсинга в табличном виде).                                                                                                                                                                                                                                                             |
| **Compile KB** (Celery `compile_document_version` / `POST /kb/compile`) | `**entity_registry`** (тип `document` на `document_registry_id`), `**knowledge_artifact`**: `source_digest`, `entity_page` (в т.ч. страницы МНН `entity_page/molecule_{id}` для строк `entity_type=molecule` — см. `KnowledgeCompileService._ensure_molecule_entity_pages`), `glossary_term`, `open_question`, `**master_index`**; `**artifact_source_link`** (provenance на `document_version`). |
| **refresh_backlinks**                                                   | `**artifact_backlink`** — рёбра из `[[slug]]` / markdown-ссылок в `content_md`.                                                                                                                                                                                                                                                                                                                   |
| **rebuild_indexes** (после миграции 003)                                | обновление `**knowledge_artifact.search_vector`** (FTS, `simple`).                                                                                                                                                                                                                                                                                                                                |
| **Clinical extraction** (`extract_document` / очередь `extract`)        | `**clinical_context`**; при нахождении МНН — доп. строки `**entity_registry`** (`entity_type=molecule`, связь `external_refs_json.molecule_id`). После успешного `ExtractionPipeline.extract` вызывается `**CandidateEngine.generate_pairs(version_id)**` → строки `**pair_evidence**` (кандидатные пары TZ §15.1).                                                                               |
| **Scoring / matrix**                                                    | Celery `score_pairs`, `build_matrix` (очередь `score`). Явный запуск цепочки: `**POST /matrix/rebuild`** (`model_version_id`, `scope_type`) → `score_pairs` → `build_matrix`. `**pair_context_score`**, `**matrix_cell`**.                                                                                                                                                                        |
| **Output generate**                                                     | `**output_release`** — черновик записи аналитического output.                                                                                                                                                                                                                                                                                                                                     |
| **Output file**                                                         | обновление `**output_release`** (`file_back_status`, при `accepted` — `released_at`).                                                                                                                                                                                                                                                                                                             |


## Объектное хранилище (MinIO/S3, bucket из `CRIN_S3_BUCKET`)


| Стадия    | Что появляется                                                                                                                                                                                          |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fetch** | Байты **реальных документов**: HTML/PDF по ключам вида `documents/{registry_id}/versions/{version_id}/...` (см. `artifact_key` в `app/core/storage.py`). До выполнения fetch файл в bucket отсутствует. |


### Где смотреть файлы и почему внешняя ссылка «пустая»

- **Карточка / просмотр на сайте Минздрава** (`document_registry.card_url`, `html_url`, часто `https://cr.minzdrav.gov.ru/clin-rec/view/{CodeVersion}`): это **SPA** (одна HTML-оболочка + JS). **Fetch** сначала тянет HTML со страницы **`/view-cr/{external_id}`** (полный контент КР), при неудаче — с `html_url`. В браузере без выполнения скриптов или при блокировках может казаться, что «документа нет» — это не обязательно 404; контент подгружается клиентом.
- **Наши копии для пайплайна** лежат в **S3-совместимом хранилище**: таблица `source_artifact`, поле `raw_path`; полный URI: `s3://{CRIN_S3_BUCKET}/{raw_path}`. В API `GET /documents/{id}` у каждого артефакта возвращается вычисляемое поле `**storage_uri`** (см. `SourceArtifactOut`).
- **Текст для поиска и извлечения** — в PostgreSQL после **normalize**: `document_section`, `text_fragment` (эндпоинты `/documents/{id}/content`, `/fragments`).
- **Скачать сырьё в UI**: Streamlit **Documents** → **Load Document** → блок «Сырьё из MinIO» (HTTP `GET /documents/{document_id}/artifacts/{artifact_id}/download`). Альтернатива: curl/браузер на тот же путь при доступном API.
- **Список артефактов в API** (`GET /documents/{id}`): для **текущей версии** документа показываются только **последние валидные** записи по типу (`html` / `pdf`): SPA-заглушка и «pdf» с телом HTML отфильтровываются по байтам в MinIO.
- **Обновить сырьё и нормализацию без полного sync**: `POST /documents/{document_id}/refetch-normalize` — воркер выполняет `fetch_document(..., force=True)` (удаляет старые `source_artifact` версии и заново качает), затем при успехе ставится `normalize`. В Streamlit: кнопка «Обновить сырьё + нормализацию (refetch)».
- **Повторить только extract** (новые эвристики МНН): `POST /documents/{document_id}/reextract` или кнопка «Переизвлечь МНН / пары» в Streamlit.

## Итог

- **«Реальные документы» как файлы** — после успешного **fetch** в **S3/MinIO** + метаданные в `**source_artifact`**.
- **Полнотекст в БД без отдельного файла в bucket** — после **normalize** (`text_fragment` и т.д.).
- **Результат компиляции KB** — после **compile_document_version** в таблицах `**knowledge_artifact`** / связях (не в отдельном файловом wiki-слое до реализации Git/fs-слоя из TZ).
- **Поиск по подстроке по артефактам KB** — `GET /kb/artifacts?search=...` (ILIKE по title/summary/slug); полнотекст по `search_vector` — задача `**rebuild_indexes`** + запросы к FTS (расширяемо).

См. также `GET /pipeline/storage-stages` (JSON для UI/скриптов).
### Диагностика refetch (почему «нет изменений»)

- Задача Celery `fetch_document` при **отсутствии валидного html/pdf** завершается с **FAILURE** (раньше была SUCCESS без эффекта). Текст ошибки: `GET /tasks/{task_id}` — поле `error` (опционально `include_result=true` для SUCCESS).
- История шагов в БД: таблица `pipeline_event_log` (миграция **004**), API `GET /documents/{id}/pipeline-events`. В Streamlit: кнопки «Проверить статус fetch» и «Загрузить журнал pipeline».
- После деплоя выполните: `alembic upgrade head` (или эквивалент в CI), чтобы журнал писался в PostgreSQL.

- **Поле `pdf_url` в реестре** иногда указывает на URL, который по факту отдаёт **`text/html` (SPA, ~610 байт), а не `application/pdf`**. Такой ответ **не сохраняется как PDF**; затем пробуем **Playwright** на странице **`/preview-cr/{external_id}`** (клик по «Скачать … PDF», ожидание браузерного download). Проверка: `curl -D - -o /tmp/x ...` — смотреть `content-type` и первые байты (`%PDF-`).
