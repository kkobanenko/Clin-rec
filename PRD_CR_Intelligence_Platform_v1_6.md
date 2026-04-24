PRD v1.6

CR Intelligence Platform

| Версия | v1.6 |
| --- | --- |
| Дата | 21.04.2026 |
| Статус | Рабочая версия |
| Назначение | Продуктовая фиксация плана перехода от quality-capable implementation к release-ready MVP |

> **Supersedes:** [PRD_CR_Intelligence_Platform_v1_5.md](PRD_CR_Intelligence_Platform_v1_5.md).

> **Alignment note:** knowledge-compilation контур, compiled KB и downstream KB/output-концепция сохраняются и описаны в [PRD_CR_Intelligence_Platform_v1_3_kb.md](PRD_CR_Intelligence_Platform_v1_3_kb.md). Настоящая версия не заменяет knowledge roadmap, а фиксирует ближайший продуктовый tranche: перевести уже собранную платформу в release-ready MVP с управляемыми acceptance gates и release discipline.

> Документ описывает ближайшую продуктовую цель: перевести CR Intelligence Platform из состояния late integration / pre-release hardening в состояние, где runtime validation, operator workflows, downstream checks и KB/output workflows образуют управляемый release process с явным go/no-go решением.

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

## 2.2 Где находится главный разрыв

- Проект уже не страдает от нехватки surface area; главный риск теперь в release discipline.
- Не все acceptance gates формализованы как обязательный release barrier.
- Regression pack еще недостаточно оформлен как канонический go/no-go набор.
- Reviewer/scoring governance и KB/output workflow существуют, но еще не сведены в единый release contour.

# 3. Проблема версии

Пока система выглядит функционально широкой, но не полностью release-governed. Команда может видеть работающий runtime и доступные operator surfaces, но без четкой процедуры release verification сохраняется риск ложного green: поверхности существуют, однако решение о готовности MVP к выпуску остается частично неформализованным.

# 4. Цель версии

## 4.1 Главная цель

Зафиксировать и реализовать переход к release-ready MVP, в котором успешный статус проекта означает не только наличие рабочих API и quality-capable pipeline, но и формализованный набор acceptance gates, regression checks, operator governance и release decision criteria.

## 4.2 Измеримый результат версии

| Поле | Описание |
| --- | --- |
| Release contract | Зафиксирован минимальный набор gates для решения go/no-go по MVP release. |
| Regression pack | Structural smoke, quality smoke, targeted API regression и downstream integration checks собраны в обязательный набор. |
| Operator governance | Reviewer/scoring/output actions трактуются как управляемый release workflow, а не набор разрозненных endpoint-ов. |
| Downstream readiness | Evidence/matrix/KB/output path проверяется как фактический downstream результат, а не как декларативная готовность. |
| Release observability | Причины stop/go и состояние ключевых стадий доступны без чтения исходного кода и ручной трассировки worker logs. |

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
| P0 | Release contract и scope freeze | Команда одинаково трактует, что значит release-ready MVP. |
| P0 | Runtime preflight и acceptance barriers | Structural/quality gates и profile checks обязательны перед release decision. |
| P0 | Regression pack baseline | Собран канонический набор smoke и API regression для go/no-go. |

## 10.2 P1

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P1 | Downstream integration hardening | Evidence/matrix path и KB/output workflows подтверждены на фактических данных. |
| P1 | Governance completion | Reviewer/scoring/release actions сведены в управляемый operator contour. |
| P1 | Release observability | Причины stop/go и статус workflow прозрачны через API и documented procedures. |

## 10.3 P2

| Приоритет | Направление | Ожидаемый результат |
| --- | --- | --- |
| P2 | Release rehearsal | Проведен controlled release rehearsal в одном runtime profile. |
| P2 | MVP exit decision | Сформирован formal summary: что входит в release, что остается post-MVP. |

# 11. Критерии готовности к MVP release

MVP release считается допустимым, когда одновременно выполнены условия:

1. Runtime profile и queue connectivity подтверждены без смешения контуров.

2. Structural smoke проходит.

3. Quality smoke проходит.

4. Targeted API regression на operator surfaces проходит.

5. Downstream integration checks для evidence/matrix, KB/output workflows и valid raw current-version artifacts проходят.

6. Остающиеся риски зафиксированы и явно отнесены к post-MVP scope, а не к скрытым блокерам текущего release.

# 12. Риски версии

| Риск | Описание | Мера снижения |
| --- | --- | --- |
| Ложный release green | Наличие широкого surface ошибочно трактуется как готовность к выпуску | Формальный release contract и go/no-go review |
| Разрыв между smoke и реальным workflow | Smoke зеленый, но operator path не собран в единый контур | Проверять KB/output/tasks/review/matrix как единый regression pack |
| Scope creep | Команда начнет full productization до закрытия release hardening | Жестко отделить immediate release scope от post-MVP |
| Непрозрачный residual risk | Неочевидно, что еще осталось незавершенным | Ввести formal release summary и risk register |

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