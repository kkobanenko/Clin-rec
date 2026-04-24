PRD v1.6

CR Intelligence Platform

| Версия | v1.6 |
| --- | --- |
| Дата | 24.04.2026 |
| Статус | Рабочая версия, актуализирована после release-ready validation |
| Назначение | Продуктовая фиксация достигнутого release-ready MVP и следующего tranche phase-2 operator hardening |

> **Supersedes:** [PRD_CR_Intelligence_Platform_v1_5.md](PRD_CR_Intelligence_Platform_v1_5.md).

> **Alignment note:** knowledge-compilation контур, compiled KB и downstream KB/output-концепция сохраняются и описаны в [PRD_CR_Intelligence_Platform_v1_3_kb.md](PRD_CR_Intelligence_Platform_v1_3_kb.md). Настоящая версия не заменяет knowledge roadmap, а фиксирует два состояния одновременно: release-ready MVP уже подтвержден, а ближайший продуктовый tranche смещён в сторону phase-2 operator hardening без снятия release discipline.

> Документ описывает текущее продуктовое состояние: CR Intelligence Platform уже находится в состоянии release-ready MVP по compose-backed validation, а ближайшая цель — уменьшать operator friction и расширять observability, не размывая сформированный go/no-go release process.

# 1. Видение версии

CR Intelligence Platform должна обеспечивать не только quality-capable pipeline, но и release-ready MVP: оператор может воспроизводимо запустить pipeline, проверить structural и quality smoke, интерпретировать reviewer/scoring state, получить диагностируемые downstream результаты и принять решение о выпуске без скрытых допущений.

Ключевая цепочка этой версии:

`runtime profile -> pipeline run -> quality validation -> downstream evidence/matrix checks -> KB/output workflow -> go/no-go release decision`

# 2. Текущее состояние продукта

## 2.1 Что уже достигнуто

- Runtime pipeline и queue routing работают в согласованном приложении и worker-контуре.
- Основные operator surfaces уже реализованы: pipeline, matrix, outputs, KB, tasks, review/scoring endpoints.
- Admin UI покрывает ключевые operator сценарии.
- Admin UI должен оставаться обратносовместимым и поддерживать мультиязычность display-layer как operator requirement первой очереди.
- Для документов доступен user-facing path к valid raw artifacts текущей версии: download primary, preview secondary.
- Structural и quality smoke уже существуют и отделены друг от друга.
- После extract уже доступны candidate generation, scoring и matrix build path.
- Composite release-ready pack уже подтвержден: compose-backed runtime, structural smoke, quality smoke, targeted API regression и KB integration зафиксированы как green в актуальном release summary.
- Admin UI уже поддерживает persisted `RU`/`EN` language switch и несколько additive operator follow-up surfaces: recent UI tasks, pipeline run detail picker, pipeline stage filter, matrix list/detail filters, quick-pick review controls для queue/history/submit flows и compact Tasks-page controls для quick-pick/filter/search/sort по recent tasks.

## 2.2 Где находится главный разрыв

- Проект уже не находится в зоне главного риска по release discipline: базовый release contract и composite evidence зафиксированы.
- Основной разрыв сместился в operator productivity и day-2 usability: быстрый follow-up для async workflows, cross-surface linkage и компактная observability все еще расширяются итеративно.
- Часть phase-2 backlog теперь относится не к blocker-gap, а к post-release hardening: linkage-view, gap suggestions, richer health dashboard и более глубокая productization operator surfaces.
- Release evidence и документация теперь должны обновляться синхронно с каждым заметным operator-surface tranche, чтобы не образовывался новый разрыв между текущей реализацией и каноническими документами.

# 3. Проблема версии

Release-ready проблема базового уровня закрыта, но продукт по-прежнему не полностью operator-efficient. Команда уже может выпускать MVP на зафиксированном runtime profile, однако ежедневная работа оператора все еще требует локальных follow-up улучшений: проще находить свежие async tasks, быстрее проваливаться в run details, сокращать ручной контекстный поиск между pipeline, tasks, outputs и KB surfaces.

# 4. Цель версии

## 4.1 Главная цель

Удержать уже достигнутый release-ready MVP и продолжить phase-2 operator hardening, в котором каждый следующий tranche уменьшает operator friction, улучшает observability и сохраняет совместимость с действующим release contract.

## 4.2 Измеримый результат версии

| Поле | Описание |
| --- | --- |
| Release contract | Зафиксирован минимальный набор gates для решения go/no-go по MVP release. |
| Regression pack | Structural smoke, quality smoke, targeted API regression и downstream integration checks собраны в обязательный набор. |
| Operator governance | Reviewer/scoring/output actions трактуются как управляемый release workflow, а не набор разрозненных endpoint-ов. |
| Downstream readiness | Evidence/matrix/KB/output path проверяется как фактический downstream результат, а не как декларативная готовность. |
| Release observability | Причины stop/go и состояние ключевых стадий доступны без чтения исходного кода и ручной трассировки worker logs. |
| Operator efficiency | Асинхронные workflow и pipeline follow-up доступны через additive UI controls без ручного поиска id и повторного контекстного переключения. |

# 5. Non-goals версии

- Полный governed release матрицы заменяемости как отдельного продукта.
- Полноценный reviewer adjudication product workflow сверх минимально необходимого governance.
- Масштабный redesign UI или расширение внешнего пользовательского контура.
- Полная автоматизация knowledge-compilation lifecycle beyond MVP release needs.

# 6. Пользователи и ценность на этой стадии

| Роль | Боль текущей стадии | Что дает эта версия |
| --- | --- | --- |
| Operator / data engineer | Есть рабочие контуры, но нет жесткого release barrier | Явный preflight, smoke и regression contract перед выпуском |
| QA / reviewer | Сложно отделить quality-capable implementation от release-ready состояния | Единый go/no-go набор и прозрачные acceptance gates |
| Product owner | Ширина реализации не превращается автоматически в управляемый MVP release | Формализованная стадия release-ready и границы post-MVP |
| Analyst | Нужен предсказуемый путь от run к output/KB verification и исходному сырью документа | Понятный operator workflow, диагностируемые downstream results и доступ к valid raw artifacts текущей версии |

# 7. Product scope этой версии

## 7.1 In scope

| Направление | Что входит |
| --- | --- |
| Release contract | Формализация release-ready критериев, go/no-go и обязательного regression pack |
| Runtime preflight | Проверки runtime-profile consistency, broker/backend alignment и operator readiness |
| Regression hardening | Structural smoke, quality smoke, targeted API regression, downstream integration checks |
| Governance completion | Минимально достаточный reviewer/scoring/release discipline для MVP |
| KB/output workflow closure | Связка KB/output endpoints с фактическим release workflow |
| Raw document access | Download-first, preview-secondary доступ к valid raw artifacts текущей версии без показа synthetic или invalid source URLs |
| Release rehearsal | Контролируемый rehearsal и документируемое решение о готовности версии |

## 7.2 Out of scope

| Направление | Что не входит |
| --- | --- |
| Full matrix governance | Отдельный governed matrix release process как самостоятельный product layer |
| Full reviewer productization | Расширенный adjudication workflow, SLA и сложные reviewer roles |
| External distribution | Выход output/KB workflows за пределы внутреннего контура |

# 8. Приоритетные продуктовые требования

1. Команда должна различать quality-capable implementation и release-ready MVP.

2. Release-ready статус должен требовать формального прохождения обязательного regression pack, а не только отдельных ручных проверок.

3. Structural smoke и quality smoke должны использоваться как разные operator gates с ясной областью применения.

4. Reviewer/scoring/output/KB surfaces должны трактоваться как части единого release workflow.

5. Downstream evidence/matrix/KB/output results должны подтверждаться фактическими данными и task visibility.

6. Operator должен иметь возможность скачать valid raw artifacts текущей версии документа через additive UI/API path, не полагаясь на misleading external rubricator URLs.

7. Каждое решение stop/go должно быть объяснимо через API, smoke summary и documented criteria.

8. Admin UI должен поддерживать мультиязычность display-layer как минимум для `RU` и `EN`, с мгновенным переключением языка в интерфейсе и без изменения internal keys, API payloads и существующей логики operator workflows.

# 9. Release contract версии

## 9.1 Базовые принципы

- Baseline DoD из [DOD_MVP.md](DOD_MVP.md) остается нижней границей приемки.
- Structural green не равен release-ready.
- Quality green не равен full productization.
- Release-ready требует формального объединения runtime, quality, regression и governance checks.

## 9.2 Минимальные release gates

| Gate | Описание |
| --- | --- |
| Gate 1 — Runtime readiness | API/worker работают в одном runtime profile, broker/result backend согласованы. |
| Gate 2 — Structural smoke | Lifecycle, routing, observability contract и auxiliary routes подтверждены. |
| Gate 3 — Quality smoke | Для валидного сценария подтверждены content-layer и downstream pair/matrix checks. |
| Gate 4 — API/operator regression | Ключевые operator endpoints на pipeline/review/matrix/outputs/kb/tasks проходят targeted regression. |
| Gate 5 — Downstream workflow verification | Evidence, matrix, KB/output workflows и valid raw document access проверены на фактических данных и task visibility. |
| Gate 6 — Release review | Есть явное go/no-go решение с зафиксированными причинами и оставшимися рисками. |

# 10. План продвижения

## 10.1 P0

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P0 | Release evidence/doc sync | PRD/TZ/VERSIONING/backlog остаются синхронными с текущим validated head и новыми operator-surface tranche. |
| P0 | Async workflow follow-up | Task/run visibility в UI расширяется additive controls без изменения API compatibility. |
| P0 | Narrow regression discipline | Каждый additive operator change закрывается focused validation и не размывает canonical release pack. |

## 10.2 P1

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P1 | Cross-surface linkage | Operator быстрее переходит между pipeline, tasks, outputs, KB и review без ручного поиска идентификаторов. |
| P1 | Release observability polish | Release-gate snapshot, task status и run details становятся доступнее через компактные admin surfaces. |
| P1 | Governance polish | Reviewer/scoring/output/KB surfaces продолжают выравниваться как единый operator contour без full productization. |

## 10.3 P2

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P2 | Productized health dashboard | Более богатый operator health/release cockpit без изменения release semantics. |
| P2 | Streamlit chrome polish | Перевод framework-provided chrome и более цельный multilingual UX остаются post-MVP polish. |
| P2 | Broader operator productization | Linkage-view, gap suggestions и расширенный admin UX остаются следующей, а не блокирующей фазой. |

# 11. Критерии готовности к MVP release

MVP release считается допустимым, когда одновременно выполнены условия:

1. Runtime profile и queue connectivity подтверждены без смешения контуров.

2. Structural smoke проходит.

3. Quality smoke проходит.

4. Targeted API regression на operator surfaces проходит.

5. Downstream integration checks для evidence/matrix, KB/output workflows и valid raw current-version artifacts проходят.

6. Остающиеся риски зафиксированы и явно отнесены к post-MVP scope, а не к скрытым блокерам текущего release.
7. Новые operator-surface улучшения не ломают действующий release-ready contract и подтверждаются focused validation.

# 12. Риски версии

| Риск | Описание | Мера снижения |
| --- | --- | --- |
| Регрессия release-ready статуса | Небольшие operator изменения могут незаметно нарушить validated contour | Узкий regression-first цикл и периодические full-pack rerun для release-facing tranche |
| Разрыв между docs и head | Код продолжит двигаться быстрее, чем канонические PRD/TZ/backlog записи | Синхронизировать docs/versioning при каждом заметном tranche |
| Scope creep | Команда начнет full productization вместо additive operator hardening | Жестко держать small-slice delivery и post-MVP boundaries |
| Непрозрачный operator friction | Формально все green, но day-2 сценарии остаются неудобными | Приоритизировать async follow-up, linkage и compact observability |

# 13. Операционные ограничения

- Runtime profile, queue routing и smoke semantics остаются обязательными по [RUNBOOK_RUNTIME_PROFILE.md](RUNBOOK_RUNTIME_PROFILE.md).
- Канонический baseline DoD остается в [DOD_MVP.md](DOD_MVP.md).
- Все операции с контейнерами и портами подчиняются [ISOLATION_POLICY.md](ISOLATION_POLICY.md).
- Knowledge-compilation roadmap и KB/output capability roadmap сохраняются по [PRD_CR_Intelligence_Platform_v1_3_kb.md](PRD_CR_Intelligence_Platform_v1_3_kb.md).

# 14. Acceptance criteria версии

1. В документации зафиксирован release-ready MVP contract поверх baseline DoD.

2. Structural smoke, quality smoke и regression pack объявлены обязательными gates.

3. Reviewer/scoring/KB/output workflows описаны как единый operator release contour.

4. Scope post-MVP productization явно отделен от immediate release goals.

5. Версия служит формальной точкой перехода от quality-capable implementation к release-ready MVP.
6. Актуализированный документ фиксирует, что текущая стадия проекта — release-ready MVP с активным phase-2 operator hardening tranche.