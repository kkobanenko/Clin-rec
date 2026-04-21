PRD v1.5

CR Intelligence Platform

| Версия | v1.5 |
| --- | --- |
| Дата | 21.04.2026 |
| Статус | Рабочая версия |
| Назначение | Продуктовая фиксация плана перехода от orchestration-ready к quality-ready pipeline |

> **Supersedes:** [PRD_CR_Intelligence_Platform_v1_2.md](PRD_CR_Intelligence_Platform_v1_2.md).

> **Alignment note:** knowledge-compilation контур и downstream KB/output-концепция сохраняются и описаны в [PRD_CR_Intelligence_Platform_v1_3_kb.md](PRD_CR_Intelligence_Platform_v1_3_kb.md). Настоящая версия фиксирует продуктовый план продвижения текущей реализации к качественно верифицируемому pipeline.

> Документ описывает ближайшую продуктовую цель: перевести CR Intelligence Platform из состояния, в котором pipeline корректно проходит жизненный цикл и заполняет наблюдаемость, в состояние, где pipeline стабильно извлекает полезный контент, прозрачно сигнализирует причины деградации и готов к пользовательской оценке на реальных документах.

# 1. Видение версии

CR Intelligence Platform должна обеспечить не только технический проход по этапам discovery, fetch и normalize, но и устойчивый quality-ready результат: для найденных клинических рекомендаций система должна либо извлечь пригодный для анализа текстовый слой, либо завершить run с объяснимой причиной отказа или деградации.

Ключевая цепочка этой версии:

`discovery -> probe -> fetch -> normalize -> content quality gate -> extraction readiness -> downstream candidate readiness`

# 2. Текущее состояние продукта

## 2.1 Что уже достигнуто

- Pipeline lifecycle работает: discovery-run создается, проходит через queue/workers и завершается терминальным статусом.
- Наблюдаемость базового уровня есть: `stats_json`, counters и API-маршруты позволяют проверить структурную целостность запуска.
- Source fallback уже частично реализован: для normalize есть HTML-first логика с fallback на PDF.
- Базовая защита от ложных PDF уже существует: fetch и source-validation различают хотя бы часть невалидных артефактов.

## 2.2 Где находится главный разрыв

- Текущий pipeline может завершаться статусом `completed`, но при этом не давать непустой content-layer.
- Structural smoke подтверждает жизненный цикл и контракт наблюдаемости, но еще не гарантирует качественный результат извлечения.
- Логика source validation и stage outcomes не полностью унифицирована между probe, fetch и normalize.
- Downstream readiness после extraction недостаточно жестко увязана с quality-gate контента.

# 3. Проблема версии

Пока run может считаться успешным без непустых `sections` и `fragments`, команда не имеет надежного сигнала о том, что документ действительно пригоден для последующей clinical extraction и экспертной оценки. Это создает риск ложноположительной приемки: инфраструктура выглядит стабильной, но продуктовый результат еще не подтвержден.

# 4. Цель версии

## 4.1 Главная цель

Зафиксировать и реализовать переход к quality-ready pipeline, в котором успешный run означает не только корректный lifecycle, но и подтвержденное наличие пригодного текстового результата хотя бы для контролируемого валидного документа.

## 4.2 Измеримый результат версии

| Поле | Описание |
| --- | --- |
| Quality contract | Зафиксированы минимальные критерии успешного content extraction: `sections`, `fragments`, объем текста и семантика статусов `success/degraded/failed`. |
| Source validation | Probe и fetch используют согласованную политику валидации HTML/PDF и диагностируют причины отклонения. |
| Stage observability | Пустой результат normalize перестает быть "тихим успехом" и становится наблюдаемым outcome с reason-code. |
| Quality smoke | Помимо lifecycle и `stats_json`, smoke контролирует не-пустой content-layer на валидном сценарии. |
| User evaluation readiness | После прохождения quality-gate допустимо проводить пользовательскую оценку реального документа через pipeline. |

# 5. Non-goals версии

- Полная продуктовая готовность reviewer workflow.
- Масштабная оптимизация производительности и throughput.
- Полное завершение matrix productization.
- UI redesign и расширение внешнего пользовательского контура.

# 6. Пользователи и ценность на этой стадии

| Роль | Боль текущей стадии | Что дает эта версия |
| --- | --- | --- |
| Data engineer | Run завершается, но неясно, действительно ли документ пригоден | Явные reason-codes, quality smoke и предсказуемая диагностика |
| NLP/ML engineer | Пустой или деградированный normalized corpus неотличим от успешного кейса | Гарантированно более чистый вход для extraction и regression testing |
| Фарма-аналитик | Нельзя доверять результату пользовательской прогоны без ручной трассировки | Понятный критерий, когда документ уже можно оценивать вручную |
| QA / reviewer | Трудно отделить инфраструктурный успех от продуктового результата | Формализованные acceptance gates перед ручной проверкой |

# 7. Product scope этой версии

## 7.1 In scope

| Направление | Что входит |
| --- | --- |
| Quality contract | Формализация критериев успешного content extraction и политики деградации |
| Source validation hardening | Единая валидация HTML/PDF, SPA-shell rejection, HEAD -> GET fallback |
| Pipeline outcome semantics | Явные terminal outcomes и reason-codes для probe/fetch/normalize |
| Quality smoke | Разделение structural и quality smoke, quality gate для content-layer |
| Integration QA | Автотесты на полную цепочку `source -> fetch -> normalize -> content/fragments` |
| Downstream readiness | Подготовка к автоматическому переходу от extraction к candidate generation |

## 7.2 Out of scope

| Направление | Что не входит |
| --- | --- |
| Full matrix release | Финальный governed release матрицы заменяемости |
| Reviewer governance | Полноценный reviewer queue и adjudication workflow |
| External distribution | Публикация корпуса и выходов за пределы внутреннего контура |

# 8. Приоритетные продуктовые требования

1. Система должна различать структурный успех run и качественный успех content extraction.

2. Run с `discovered > 0` и пустым content-layer не должен считаться безусловно успешным без явной классификации `degraded` или `failed`.

3. Для probe и fetch должна существовать единая политика определения валидного HTML/PDF-источника.

4. Normalize должен выдавать не только результат, но и диагностируемый outcome при нулевом извлечении после всех допустимых fallback-попыток.

5. Quality smoke должен проверять не только lifecycle, но и наличие полезного content-layer на контролируемом сценарии.

6. Downstream переход к extraction/candidate readiness не должен запускаться как эквивалент полноценного успеха, если content quality gate не выполнен.

# 9. Quality contract версии

## 9.1 Базовые принципы

- Structural success и quality success разделяются.
- Пустой content-layer при найденных документах требует явной классификации.
- Каждый отказ или деградация должны быть трассируемы до этапа и причины.

## 9.2 Минимальные quality gates

| Gate | Описание |
| --- | --- |
| Gate 1 — Source validity | Артефакт не является SPA shell, fake PDF или неполной HTML-витриной, если ожидается полный текст. |
| Gate 2 — Normalize outcome | После HTML/PDF попыток для валидного документа формируются непустые `sections` и `fragments`, либо фиксируется объяснимый terminal outcome. |
| Gate 3 — Smoke quality | При `discovered > 0` хотя бы один контролируемый документ проходит content quality gate. |
| Gate 4 — Extraction readiness | В downstream не передается документ, не прошедший content quality gate, как эквивалент полноценного успеха. |

# 10. План продвижения

## 10.1 P0

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P0 | Quality contract и acceptance semantics | Команда единообразно трактует пустой content при `discovered > 0`. |
| P0 | Unified source validation | Probe и fetch используют один источник истины для HTML/PDF validation и reason-codes. |
| P0 | Observable stage outcomes | Normalize и связанные task wrappers не маскируют пустой extraction под успех. |

## 10.2 P1

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P1 | Quality smoke | Smoke не пропускает ложноположительные run-ы без контента. |
| P1 | Integration tests | Критичная цепочка качества покрыта автотестами end-to-end уровня. |
| P1 | Dev test runtime | Минимальный regression pack воспроизводим в рабочем окружении. |

## 10.3 P2

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P2 | Downstream candidate readiness | После extract данные пригодны для matrix/evidence-level проверки. |
| P2 | Matrix/evidence consistency | Downstream endpoints отражают фактически сгенерированные candidate/evidence данные. |

# 11. Критерии готовности к пользовательской оценке

Пользовательская прогонка реального документа через pipeline считается допустимой, когда одновременно выполнены условия:

1. Quality smoke проходит не только по lifecycle и `stats_json`, но и по content quality.

2. Для хотя бы одного реального документа `sections` и `fragments` непустые и согласованы между API и storage.

3. Неуспешные кейсы дают reason-codes и stage events, пригодные для диагностики без чтения исходного кода.

4. Минимальный regression pack запускается воспроизводимо в согласованном runtime profile.

# 12. Риски версии

| Риск | Описание | Мера снижения |
| --- | --- | --- |
| Ложный structural green | Smoke проходит, хотя document content пуст | Ввести отдельный quality smoke и terminal outcomes |
| Нестабильность source behavior | Источник может отдавать HTML shell вместо полного текста | Общая validation-логика, reason-codes, fallback probe |
| Расхождение сервисной логики | Probe/fetch/normalize принимают разные решения | Один validation contract и единая семантика outcomes |
| Смещение scope | Команда уйдет в full matrix work до закрытия content quality | Жестко отделить P0/P1 от P2 |

# 13. Операционные ограничения

- Базовый runtime profile и queue routing остаются обязательными по [RUNBOOK_RUNTIME_PROFILE.md](RUNBOOK_RUNTIME_PROFILE.md) и [DOD_MVP.md](DOD_MVP.md).
- Все операции с контейнерами и портами по-прежнему подчиняются [ISOLATION_POLICY.md](ISOLATION_POLICY.md).
- Канонический MVP DoD остается в [DOD_MVP.md](DOD_MVP.md); эта версия PRD уточняет advancement gates сверх baseline DoD, не заменяя его.

# 14. Acceptance criteria версии

1. В документации зафиксирован quality contract для content extraction и семантика статусов `success/degraded/failed`.

2. Source validation унифицирована на уровне продукта и отражена в технических требованиях.

3. Quality smoke становится обязательным критерием перед ручной оценкой реального документа.

4. План работ декомпозирован на P0/P1/P2 и привязан к выходным результатам.

5. Версия служит формальной точкой перехода от baseline orchestration к quality-ready implementation.