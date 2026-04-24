Техническое задание

CR Intelligence Platform — техническая фиксация tranche работ для release-ready MVP

| Версия | v1.5 |
| --- | --- |
| Дата | 21.04.2026 |
| Статус | Рабочая версия |
| Назначение | Техническая реализация и приемка release-hardening tranche поверх quality-capable implementation |

> **Supersedes:** [TZ_CR_Intelligence_Platform_v1_4.md](TZ_CR_Intelligence_Platform_v1_4.md).

> **Alignment note:** knowledge-compilation расширение, KB endpoints и output filing остаются в [TZ_CR_Intelligence_Platform_v1_2_kb.md](TZ_CR_Intelligence_Platform_v1_2_kb.md). Настоящая версия не переопределяет KB architecture; она фиксирует ближайший execution tranche для перевода текущей реализации в release-ready MVP.

# 1. Назначение документа

Настоящее ТЗ определяет технический состав работ, контракты, зависимости, критерии приемки и порядок реализации следующего этапа проекта: собрать уже реализованные surfaces и quality checks в воспроизводимый release contour с явным go/no-go process.

# 2. Текущая техническая стадия

## 2.1 Подтверждено в кодовой базе

- Смонтированы основные API surfaces: pipeline, matrix, outputs, kb, tasks, documents, sync, health.
- Structural и quality smoke реализованы и уже проверяют разные классы инвариантов.
- Downstream после extract включает candidate generation, scoring и matrix build.
- Есть operator/admin surfaces для review, scoring models, outputs, KB и tasks.
- Есть additive documents path для valid raw artifacts текущей версии: API download/preview и UI buttons без изменения старых payloads.
- Первая версия multilingual support должна покрывать Streamlit admin/operator UI (`RU`/`EN`) без изменения API contracts и internal keys.

## 2.2 Подтвержденные ограничения

- Нет единого канонического release pack, который команда трактует как окончательный barrier.
- Не все operator workflows формализованы как части release procedure.
- Интеграционная регрессия на downstream и KB/output path еще недостаточно закреплена как обязательный gate.
- Release summary и residual risk discipline остаются недостаточно формализованными.

# 3. Техническая цель версии

Сделать проект release-ready:

1. формализовать обязательный release pack;
2. связать runtime preflight, smoke и API/integration regression в единый gate;
3. довести минимально достаточный reviewer/scoring governance contour;
4. проверить downstream evidence/matrix и KB/output workflows как части release procedure;
5. оформить controlled release rehearsal и go/no-go summary.

# 4. Scope реализации

## 4.1 In scope

| Направление | Техническое содержание |
| --- | --- |
| Release pack | Canonical набор smoke, targeted API suites и integration checks |
| Runtime preflight | Проверки profile consistency, broker/backend alignment, operator readiness |
| Governance hardening | Минимально необходимый reviewer/scoring/release discipline |
| Downstream verification | Проверка extract -> candidate -> scoring -> matrix на фактических данных |
| KB/output workflow closure | Проверка compile/lint/output/task visibility как части release contour |
| Raw document access | Additive API/UI path для скачивания valid current-version artifacts с фильтрацией SPA-shell/fake-PDF |
| UI multilinguality | Backward-compatible language switch в Streamlit UI с мгновенным rerender и сохранением выбора языка |
| Release procedure | Rehearsal, summary, risk capture, go/no-go checklist |

## 4.2 Out of scope

| Направление | Исключение |
| --- | --- |
| Full product governance | Полный adjudication workflow, advanced roles, SLA |
| Full matrix release productization | Отдельная governed release system для matrix как самостоятельного продукта |
| Broad UI work | Сильное расширение UI beyond admin/operator needs |

# 5. Контракты и семантика release-ready

## 5.1 Базовые статусы

| Статус | Значение |
| --- | --- |
| structural-ready | Runtime profile, lifecycle и observability contract подтверждены |
| quality-ready | Content-layer и downstream quality checks подтверждены |
| release-ready | Structural, quality, operator regression и workflow verification завершены; есть go/no-go summary |
| blocked | Есть незакрытый gate, делающий выпуск недопустимым |

## 5.2 Обязательные release artifacts

Минимально должны существовать и интерпретироваться согласованно:

- structural smoke summary;
- quality smoke summary;
- targeted API regression result;
- downstream integration verification result;
- release summary с residual risks.

# 6. Рабочие пакеты

## 6.1 Task A — Release contract и doc sync

| Поле | Описание |
| --- | --- |
| Приоритет | P0 |
| Зависимости | Нет |
| Оценка | 0.5-1 день |
| Результат | PRD/TZ/VERSIONING/RUNBOOK/DOD используют одну и ту же release-ready семантику |

**Definition of done:** новые версии документов созданы; versioning обновлен; release gates не противоречат runbook и baseline DoD.

## 6.2 Task B — Runtime preflight и release checklist

| Поле | Описание |
| --- | --- |
| Приоритет | P0 |
| Зависимости | Task A |
| Оценка | 0.5-1 день |
| Результат | Перед release decision существует канонический preflight/checklist |

**Технические изменения:**

- Runbook и smoke usage синхронизированы с release checklist.
- Явно определено, что structural и quality smoke проверяют и чего не проверяют.
- Зафиксирован минимальный порядок release verification.

## 6.3 Task C — Regression pack baseline

| Поле | Описание |
| --- | --- |
| Приоритет | P0 |
| Зависимости | Task A, Task B |
| Оценка | 1-2 дня |
| Результат | Собран и стабилизирован минимальный обязательный release pack |

**Технические изменения:**

- Выделен обязательный набор targeted suites для review, matrix model ops, outputs, auxiliary mounts и related slices.
- Зафиксированы downstream integration checks для evidence/matrix, KB/output workflows и valid raw current-version artifacts.
- Результаты regression pack трактуются как gate, а не как справочная диагностика.

## 6.4 Task D — Governance completion

| Поле | Описание |
| --- | --- |
| Приоритет | P1 |
| Зависимости | Task C |
| Оценка | 1-2 дня |
| Результат | Reviewer/scoring/output actions сведены в минимально достаточный release contour |

**Технические изменения:**

- Проверяется целостность review queue/history/actions и scoring model readiness/activation.
- Определяется operator path для release-critical действий.
- Residual manual steps явно документируются, а не остаются неявными.

## 6.5 Task E — Downstream and KB/output verification

| Поле | Описание |
| --- | --- |
| Приоритет | P1 |
| Зависимости | Task C, Task D |
| Оценка | 1-2 дня |
| Результат | Downstream evidence/matrix, KB/output workflows и valid raw current-version artifacts проверены как часть release process |

**Технические изменения:**

- Проверяется связка extract -> candidate -> scoring -> matrix.
- Проверяются KB compile/lint, output generation/file-back и task polling visibility.
- Добавляются additive endpoints и UI controls для скачивания valid raw artifacts текущей версии документа; SPA-shell и fake-PDF скрываются из user-facing списка.
- Выявленные gaps классифицируются как blocker или post-MVP risk.

## 6.6 Task F — Controlled release rehearsal

| Поле | Описание |
| --- | --- |
| Приоритет | P2 |
| Зависимости | Task D, Task E |
| Оценка | 0.5-1 день |
| Результат | Проведен один воспроизводимый rehearsal и оформлен go/no-go summary |

**Технические изменения:**

- Выполняется полный release pack в одном runtime profile.
- Формируется краткий release report с остаточными рисками.
- Фиксируется решение: release-ready или blocked.

# 7. Затрагиваемые компоненты

| Компонент | Изменение |
| --- | --- |
| `scripts/e2e_smoke.py` | Канонический structural/quality release barrier |
| `RUNBOOK_RUNTIME_PROFILE.md` | Preflight, smoke usage и release checklist |
| `app/api/documents.py` | User-facing documents API, raw artifact list/download path |
| `app/schemas/documents.py` | Additive schema for raw artifact access |
| `app/api/pipeline.py` | Review queue/history/actions как часть operator contour |
| `app/services/reviewer.py` | Reviewer governance logic |
| `app/api/matrix.py` | Scoring model lifecycle, pair evidence, matrix checks |
| `app/services/release.py` | Release/readiness semantics для scoring model workflow |
| `app/workers/tasks/extract.py` | Downstream orchestration evidence -> scoring -> matrix |
| `app/api/kb.py` | KB operator workflows |
| `app/api/outputs.py` | Output generation/file-back workflows |
| `app/api/tasks.py` | Task visibility для background workflows |
| `app/ui/app.py` | Admin/operator UI path для release-critical actions, raw artifact download/preview и language switch |
| `app/ui/ui_i18n.py` | Primary lightweight i18n layer, persistence и display translation helpers |
| `app/ui_i18n.py` | Backward-compatible shim for existing imports |
| `tests/test_pipeline_review_api.py` | Review API regression |
| `tests/test_matrix_model_ops_api.py` | Scoring model/operator regression |
| `tests/test_outputs_api.py` | Outputs regression |
| `tests/test_aux_api_mounts.py` | Mounted routes regression barrier |
| `tests/test_document_pipeline_outcomes_api.py` | Documents API regression incl. raw artifact access |
| `tests/test_kb_integration_postgres.py` | KB integration verification |

# 8. Требования к данным и API

## 8.1 Данные

- Release artifacts должны быть интерпретируемы вне worker logs.
- Task visibility должна покрывать по крайней мере output/KB background workflows.
- Downstream checks должны ссылаться на фактически существующие evidence/matrix results, а не на декларативную готовность.
- User-facing raw artifact access должен опираться только на valid current-version artifacts; synthetic rubricator URLs и invalid payloads не должны трактоваться как downloadable source.

## 8.2 API

Минимум должен сохраняться и расширяться следующими свойствами:

1. Operator может различить structural-ready, quality-ready и release-ready.
2. Review/scoring/output/KB/task endpoints должны быть пригодны для release verification без чтения исходников.
3. Documents API может аддитивно отдавать список valid raw artifacts текущей версии и download/preview links без изменения старых document payloads.
4. Smoke summary и API results должны быть совместимы по терминологии и ожиданиям.

# 9. Тестирование и QA

## 9.1 Обязательный минимальный набор

| Тип | Проверка |
| --- | --- |
| Runtime preflight | Profile consistency, broker/backend alignment |
| Smoke structural | Lifecycle, queue routing, stats contract, auxiliary routes |
| Smoke quality | Content-layer, pair evidence, matrix checks |
| API regression | Review, matrix model ops, outputs, auxiliary mounts |
| Integration | KB integration, downstream evidence/matrix verification и valid raw artifact access |

## 9.2 Release gate этой версии

Версия считается принятой, если одновременно выполнены условия:

1. Runtime preflight пройден.
2. Structural smoke проходит.
3. Quality smoke проходит.
4. Обязательные targeted API suites проходят.
5. Downstream и KB/output verification проходят.
6. Есть оформленный go/no-go summary.

# 10. Порядок реализации

1. Task A
2. Task B
3. Task C
4. Task D
5. Task E
6. Task F

# 11. План спринтов

## 11.1 Sprint 1

Включает Task A, Task B, Task C.

**Выход спринта:**

- release-ready contract зафиксирован;
- runtime preflight и checklist оформлены;
- regression pack baseline собран и объявлен обязательным.

## 11.2 Sprint 2

Включает Task D, Task E, Task F.

**Выход спринта:**

- operator governance contour доведен до MVP-уровня;
- downstream и KB/output workflows проверены как часть release process;
- проведен controlled release rehearsal.

# 12. Ограничения и допущения

- Baseline MVP DoD остается каноническим в [DOD_MVP.md](DOD_MVP.md).
- Эта версия ТЗ не заменяет knowledge-compilation roadmap, а уточняет ближайший release-hardening tranche.
- Операционный профиль запуска и изоляция окружения остаются обязательными по [RUNBOOK_RUNTIME_PROFILE.md](RUNBOOK_RUNTIME_PROFILE.md) и [ISOLATION_POLICY.md](ISOLATION_POLICY.md).

# 13. Definition of Done версии

1. Созданы и синхронизированы новые PRD/TZ/versioning документы.
2. Release pack определен и принят как обязательный gate.
3. Reviewer/scoring/KB/output workflows описаны как единый release contour.
4. Проведен хотя бы один controlled release rehearsal или подготовлен точный checklist для него.
5. Команда может формально ответить, является ли текущая сборка release-ready или blocked, без скрытых допущений.