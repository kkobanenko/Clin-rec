# Project Analysis — 2026-04-28 v4

## 1. Current Stage

```text
Evidence-rich internal pilot operations in progress (v2.7 candidate observability tranche).
```

Платформа находится в стадии эксплуатационного internal pilot с усилением наблюдаемости extraction/candidate quality. Базовые v2.6 функции (evidence diagnostics, corpus quality, content-kind scoring) остаются валидными и расширены новым операторским слоем.

## 2. Что сделано в текущем автономном цикле

### 2.1 Candidate Diagnostics Aggregate Report (NEW)

Добавлен новый сервис `app/services/candidate_diagnostics_report.py`:

- агрегирует успешные события `extract` из `pipeline_event_log`;
- нормализует метрики `candidate_skip_rate`, `candidate_pairs_count`, `candidate_fragments_no_mnn`, `candidate_fragments_single_mnn`, `candidate_fragments_image`;
- считает агрегаты: средний/максимальный skip-rate, количество high-skip версий, общие counters;
- возвращает report в JSON и Markdown-friendly виде.

### 2.2 Outputs API расширен (additive)

В `app/api/outputs.py` добавлены endpoints:

- `GET /outputs/candidate-diagnostics`
- `GET /outputs/candidate-diagnostics/markdown`

Оба endpoints аддитивны и не ломают действующие контракты API.

### 2.3 Operator UI расширен

В `app/ui/app.py` (`Outputs` page) добавлен новый диагностический блок:

- выбор окна версий, порога high-skip, top-N проблемных версий;
- summary-метрики по candidate diagnostics;
- таблица top-versions по skip-rate;
- загрузка markdown-отчёта для operator handoff.

### 2.4 Тестовое покрытие

Добавлены/обновлены тесты:

- `tests/test_candidate_diagnostics_report.py` (новый модуль)
- `tests/test_outputs_api.py` (новые endpoint tests)

Результат запуска:

- `24 passed` (таргетированный прогон новых и связанных тестов).

## 3. Оценка зрелости реализации

### Уже реализовано и стабильно

- JSON-first ingestion/normalization и runtime pipeline;
- evidence density diagnostics + release evidence reports;
- corpus quality reports;
- content-kind-aware scoring;
- candidate generation diagnostics на уровне worker event log;
- операторские поверхности review/scoring/kb/output/task.

### Что улучшено сейчас

- Candidate diagnostics поднята с уровня сырого event log до операторского агрегированного отчёта (API + UI).

### Открытые риски

- отсутствует автоматическая alert-доставка при деградации (внешние каналы уведомлений);
- нет автоматического gatekeeper-а, блокирующего release при high-skip burst;
- требуется регулярная runtime-проверка на реальном compose stack (не только unit-level).

## 4. Итог по стадии

```text
Текущая стадия: internal pilot operational hardening (candidate observability upgraded).
Следующая стадия: internal pilot released with automated quality gate enforcement.
```
