# Когда появляются данные в хранилище и в БД

Краткая схема для операторов и разработчиков (соответствует текущему коду pipeline).

## PostgreSQL

| Стадия | Что появляется |
| --- | --- |
| **Discovery** (sync full/incremental) | `pipeline_run`, строки **`document_registry`** — каталог: заголовки, URL карточек/HTML/PDF, метаданные рубрикатора. Полного текста документа в БД на этом шаге нет. |
| **Probe** (по цепочке после discovery) | **`document_version`** (в т.ч. `source_type_primary`), при необходимости новые версии. |
| **Fetch** | **`source_artifact`**: ссылка `raw_path` на объект в S3/MinIO, хэш, тип. |
| **Normalize** | **`document_section`**, **`text_fragment`** — нормализованный текст и структура (результат индексирования/парсинга в табличном виде). |
| **Compile KB** (Celery `compile_document_version` / `POST /kb/compile`) | **`entity_registry`** (тип `document` на `document_registry_id`), **`knowledge_artifact`**: `source_digest`, `entity_page`, `glossary_term`, `open_question`, **`master_index`**; **`artifact_source_link`** (provenance на `document_version`). |
| **refresh_backlinks** | **`artifact_backlink`** — рёбра из `[[slug]]` / markdown-ссылок в `content_md`. |
| **rebuild_indexes** (после миграции 003) | обновление **`knowledge_artifact.search_vector`** (FTS, `simple`). |
| **Clinical extraction / scoring** | сущности клинического слоя, evidence, matrix — по мере реализации задач `extract` / `score`. |
| **Output generate** | **`output_release`** — черновик записи аналитического output. |
| **Output file** | обновление **`output_release`** (`file_back_status`, при `accepted` — `released_at`). |

## Объектное хранилище (MinIO/S3, bucket из `CRIN_S3_BUCKET`)

| Стадия | Что появляется |
| --- | --- |
| **Fetch** | Байты **реальных документов**: HTML/PDF по ключам вида `documents/{registry_id}/versions/{version_id}/...` (см. `artifact_key` в `app/core/storage.py`). До выполнения fetch файл в bucket отсутствует. |

## Итог

- **«Реальные документы» как файлы** — после успешного **fetch** в **S3/MinIO** + метаданные в **`source_artifact`**.
- **Полнотекст в БД без отдельного файла в bucket** — после **normalize** (`text_fragment` и т.д.).
- **Результат компиляции KB** — после **compile_document_version** в таблицах **`knowledge_artifact`** / связях (не в отдельном файловом wiki-слое до реализации Git/fs-слоя из TZ).
- **Поиск по подстроке по артефактам KB** — `GET /kb/artifacts?search=...` (ILIKE по title/summary/slug); полнотекст по `search_vector` — задача **`rebuild_indexes`** + запросы к FTS (расширяемо).

См. также `GET /pipeline/storage-stages` (JSON для UI/скриптов).
