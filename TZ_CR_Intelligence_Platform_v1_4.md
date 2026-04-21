Техническое задание

CR Intelligence Platform — техническая фиксация плана перехода к quality-ready pipeline

| Версия | v1.4 |
| --- | --- |
| Дата | 21.04.2026 |
| Статус | Рабочая версия |
| Назначение | Техническая реализация и приемка плана продвижения P0/P1/P2 |

> **Supersedes:** [TZ_CR_Intelligence_Platform_v1_1.md](TZ_CR_Intelligence_Platform_v1_1.md).

> **Alignment note:** knowledge-compilation расширение, KB endpoints и output filing остаются в [TZ_CR_Intelligence_Platform_v1_2_kb.md](TZ_CR_Intelligence_Platform_v1_2_kb.md). Настоящая версия фиксирует технические работы, необходимые для перевода текущего ingestion pipeline в quality-ready состояние.

# 1. Назначение документа

Настоящее ТЗ определяет технический состав работ, контракты, зависимости, критерии приемки и порядок реализации для следующего этапа проекта: устранить разрыв между структурно успешным pipeline и качественно успешным content extraction.

# 2. Текущая техническая стадия

## 2.1 Подтверждено в кодовой базе

- Discovery, queue routing и базовый run lifecycle работают в согласованном runtime profile.
- Есть контур `probe -> fetch -> normalize`, включая частичный HTML/PDF fallback.
- Есть структурный smoke и минимальный observability contract для `completed` run.

## 2.2 Подтвержденные ограничения

- `completed` run еще не гарантирует непустой content-layer.
- Валидация HTML/PDF частично дублируется и может расходиться между сервисами.
- Normalize может завершиться пустым результатом без достаточно жесткого terminal outcome.
- Автотесты еще не покрывают end-to-end качество цепочки `source -> content` как release gate.

# 3. Техническая цель версии

Сделать pipeline quality-ready:

1. источник должен валидироваться единообразно;
2. пустой или деградированный normalize-результат должен быть явно наблюдаем;
3. quality smoke должен быть обязательным gate;
4. downstream стадия не должна принимать пустой content за полноценный успех.

# 4. Scope реализации

## 4.1 In scope

| Направление | Техническое содержание |
| --- | --- |
| Quality contract | Контракт quality outcome и статусов для content-layer |
| Source validation | Shared validation module, SPA-shell rejection, PDF signature/content-type rules, HEAD -> GET fallback |
| Stage semantics | Terminal outcomes и reason-codes для `probe`, `fetch`, `normalize` |
| Event logging | Подключение stage-level pipeline events в task wrappers |
| Smoke | Разделение structural и quality smoke, новые обязательные проверки |
| Integration QA | Тесты на сквозную цепочку `source -> fetch -> normalize -> content/fragments` |
| Downstream readiness | Подготовка перехода `extract -> candidate generation` без ложноположительных success-paths |

## 4.2 Out of scope

| Направление | Исключение |
| --- | --- |
| UI | Существенные изменения интерфейса и reviewer workflow |
| Productization | Полноценный matrix release и release governance |
| Broad optimization | Большая работа по throughput/performance вне задач качества |

# 5. Контракты и семантика статусов

## 5.1 Классы исходов

| Статус | Значение |
| --- | --- |
| success | Документ прошел source validation и дал непустой результат normalize, пригодный к downstream обработке |
| degraded | Lifecycle завершен, но качество контента или source completeness не соответствует quality gate; требуется диагностика или retry strategy |
| failed | Источник или обработка не позволяют получить пригодный контент; дальнейшая обработка как успешного документа запрещена |

## 5.2 Обязательные reason-codes

Минимально должны поддерживаться reason-codes классов:

- `source_invalid_html_shell`
- `source_invalid_pdf_signature`
- `source_probe_inconclusive`
- `normalize_empty_after_html`
- `normalize_empty_after_pdf_fallback`
- `quality_gate_failed_empty_content`

Набор может расширяться, но не должен сужаться без обновления документации и тестов.

# 6. Рабочие пакеты

## 6.1 Task A — Quality contract и doc sync

| Поле | Описание |
| --- | --- |
| Приоритет | P0 |
| Зависимости | Нет |
| Оценка | 0.5-1 день |
| Результат | Зафиксированы thresholds и правила классификации `success/degraded/failed` |

**Definition of done:** обновлены PRD/TZ/runbook semantics; команда использует один и тот же acceptance contract.

## 6.2 Task B — Unified source validation

| Поле | Описание |
| --- | --- |
| Приоритет | P0 |
| Зависимости | Task A |
| Оценка | 1-2 дня |
| Результат | Probe и fetch используют shared validation contract |

**Технические изменения:**

- `FetchService` использует общий validation module вместо локально расходящейся логики.
- `ProbeService` сохраняет HEAD fast path, но умеет переходить на lightweight GET при неоднозначном HEAD.
- Каждое решение probe/fetch пишет reason-code.

## 6.3 Task C — Observable stage outcomes

| Поле | Описание |
| --- | --- |
| Приоритет | P0 |
| Зависимости | Task A; может идти параллельно с Task B после фиксации статусов |
| Оценка | 1-2 дня |
| Результат | Пустой normalize перестает выглядеть как "тихий успех" |

**Технические изменения:**

- `NormalizeService` фиксирует terminal outcome при пустом результате после HTML/PDF попыток.
- Task wrappers `probe`, `fetch`, `normalize`, `extract` публикуют stage events `start/success/failure` с `detail_json`.
- API run/stage statuses отражают outcome и причину деградации.

## 6.4 Task D — Quality smoke

| Поле | Описание |
| --- | --- |
| Приоритет | P1 |
| Зависимости | Task B, Task C |
| Оценка | 0.5-1 день |
| Результат | Quality smoke не пропускает пустой content-layer |

**Технические изменения:**

- В `scripts/e2e_smoke.py` появляется режим `structural` и режим `quality`.
- В `quality` режиме при `discovered > 0` минимум один документ обязан иметь непустые `sections` и `fragments`.

## 6.5 Task E — Integration tests на source-to-content chain

| Поле | Описание |
| --- | --- |
| Приоритет | P1 |
| Зависимости | Task B, Task C, Task D |
| Оценка | 1-2 дня |
| Результат | Качество цепочки контролируется не только unit-тестами helper-уровня |

**Технические изменения:**

- Добавляются тесты для валидного HTML/PDF сценария.
- Добавляются тесты для SPA shell, fake PDF и probe fallback behavior.
- Добавляется проверка, что успешный normalize приводит к непустым `content/fragments`.

## 6.6 Task F — Test runtime stabilization

| Поле | Описание |
| --- | --- |
| Приоритет | P1 |
| Зависимости | Task D, Task E |
| Оценка | 0.5-1 день |
| Результат | Минимальный regression pack стабильно воспроизводим в активном окружении |

## 6.7 Task G — Downstream candidate readiness

| Поле | Описание |
| --- | --- |
| Приоритет | P2 |
| Зависимости | Task E |
| Оценка | 1-2 дня |
| Результат | После extract появляется детерминированный переход к candidate generation |

## 6.8 Task H — Matrix/evidence verification

| Поле | Описание |
| --- | --- |
| Приоритет | P2 |
| Зависимости | Task G |
| Оценка | 0.5-1 день |
| Результат | Downstream endpoints опираются на фактически сгенерированные данные |

# 7. Затрагиваемые компоненты

| Компонент | Изменение |
| --- | --- |
| `app/services/artifact_validation.py` | Каноническая логика валидации артефактов и source quality |
| `app/services/fetch.py` | Переход на shared validation и reason-codes |
| `app/services/probe.py` | HEAD -> GET fallback и диагностические причины |
| `app/services/normalize.py` | Terminal outcome для empty extraction |
| `app/services/pipeline_event_log.py` | Стандартизация stage-level event logging |
| `app/workers/tasks/probe.py` | Wiring stage events и outcome propagation |
| `app/workers/tasks/fetch.py` | Wiring stage events и outcome propagation |
| `app/workers/tasks/normalize.py` | Wiring stage events и outcome propagation |
| `app/workers/tasks/extract.py` | Wiring stage events и downstream gatekeeping |
| `scripts/e2e_smoke.py` | Structural vs quality smoke |
| `tests/test_source_validation.py` | Сквозные проверки source validation |
| `tests/test_normalize.py` | Empty-result semantics и fallback checks |
| `tests/test_pipeline_stages.py` | Отражение outcome в API/stage status |

# 8. Требования к данным и API

## 8.1 Данные

- Stage outcome и reason-code должны быть доступны в event/log representation.
- Пустой normalize-результат должен быть различим от кейса, когда normalize не запускался.
- Документы, не прошедшие quality gate, не должны маркироваться как downstream-ready без явного статуса деградации.

## 8.2 API

Минимум должен сохраняться и расширяться следующими свойствами:

1. Run/stage endpoints возвращают outcome и reason-code для деградированных и failed кейсов.
2. `/documents/{id}/content` и `/documents/{id}/fragments` остаются согласованными с document-version и stage status.
3. Клиент может отличить structural green от quality green без чтения внутренних логов worker-а.

# 9. Тестирование и QA

## 9.1 Обязательный минимальный набор

| Тип | Проверка |
| --- | --- |
| Unit | `artifact_validation`, `source_validation`, `normalize fallback` |
| Integration | `source -> fetch -> normalize -> content/fragments` |
| API | Stage status и run outcome consistency |
| Smoke structural | Lifecycle, queue routing, `stats_json` contract |
| Smoke quality | Непустой content-layer на валидном сценарии |

## 9.2 Release gate этой версии

Версия считается принятой, если одновременно выполнены условия:

1. Structural smoke проходит.
2. Quality smoke проходит.
3. Интеграционные тесты source-to-content chain проходят.
4. Пустые или невалидные источники завершаются с reason-code, а не silent success.

# 10. Порядок реализации

1. Task A
2. Task B и Task C
3. Task D
4. Task E
5. Task F
6. Task G
7. Task H

# 11. План спринтов

## 11.1 Sprint 1

Включает Task A, Task B, Task C, Task D, Task E.

**Выход спринта:**

- quality contract зафиксирован;
- source validation унифицирована;
- normalize и stage outcomes наблюдаемы;
- quality smoke ловит ложноположительные run-ы;
- source-to-content chain покрыта integration-тестами.

## 11.2 Sprint 2

Включает Task F, Task G, Task H.

**Выход спринта:**

- regression pack стабильно запускается в рабочем окружении;
- candidate generation привязан к quality-approved content;
- downstream matrix/evidence path проверен на фактических данных.

# 12. Ограничения и допущения

- Baseline MVP DoD остается каноническим в [DOD_MVP.md](DOD_MVP.md).
- Эта версия ТЗ не заменяет knowledge-compilation roadmap, а уточняет ближайший технический tranche качества pipeline.
- Операционный профиль запуска и изоляция окружения остаются обязательными по [RUNBOOK_RUNTIME_PROFILE.md](RUNBOOK_RUNTIME_PROFILE.md) и [ISOLATION_POLICY.md](ISOLATION_POLICY.md).

# 13. Definition of Done версии

1. P0 блок завершен и отражен в коде, тестах и документации.
2. Quality smoke отделен от structural smoke и используется как обязательный gate перед пользовательской оценкой.
3. Для деградированных и failed документов система возвращает reason-code и наблюдаемый stage outcome.
4. Минимальный regression pack воспроизводим в согласованном runtime profile.
5. Команда может прогнать реальный документ через pipeline и интерпретировать результат без скрытых допущений.