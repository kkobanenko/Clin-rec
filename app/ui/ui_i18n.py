"""Lightweight UI i18n helpers for Streamlit admin surfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

LANGUAGE_OPTIONS = ("ru", "en")
DEFAULT_LANGUAGE = "ru"
LANGUAGE_STORAGE_PATH = Path("var/ui_preferences.json")

_CURRENT_LANGUAGE = DEFAULT_LANGUAGE
_PATCHED = False

TRANSLATIONS: dict[str, dict[str, str]] = {
    "Language": {"ru": "Язык", "en": "Language"},
    "Navigation": {"ru": "Навигация", "en": "Navigation"},
    "CR Intelligence Platform": {"ru": "CR Intelligence Platform", "en": "CR Intelligence Platform"},
    "Dashboard": {"ru": "Панель", "en": "Dashboard"},
    "Documents": {"ru": "Документы", "en": "Documents"},
    "Matrix Cells": {"ru": "Ячейки матрицы", "en": "Matrix Cells"},
    "Pipeline Runs": {"ru": "Прогоны пайплайна", "en": "Pipeline Runs"},
    "KB Artifacts": {"ru": "KB артефакты", "en": "KB Artifacts"},
    "Pipeline": {"ru": "Пайплайн", "en": "Pipeline"},
    "Matrix": {"ru": "Матрица", "en": "Matrix"},
    "Reviews": {"ru": "Ревью", "en": "Reviews"},
    "Scoring Models": {"ru": "Скоринговые модели", "en": "Scoring Models"},
    "Knowledge Base": {"ru": "База знаний", "en": "Knowledge Base"},
    "Tasks": {"ru": "Задачи", "en": "Tasks"},
    "Recent UI Tasks": {"ru": "Недавние UI-задачи", "en": "Recent UI Tasks"},
    "Tracked Task": {"ru": "Отслеживаемая задача", "en": "Tracked Task"},
    "Load Selected Task": {"ru": "Загрузить выбранную задачу", "en": "Load Selected Task"},
    "No tracked tasks in this session": {"ru": "В этой сессии ещё нет отслеживаемых задач", "en": "No tracked tasks in this session"},
    "Outputs": {"ru": "Выходы", "en": "Outputs"},
    "KB Artifact": {"ru": "KB артефакт", "en": "KB Artifact"},
    "Output": {"ru": "Выход", "en": "Output"},
    "Entity #{id}": {"ru": "Сущность #{id}", "en": "Entity #{id}"},
    "Untitled entity": {"ru": "Сущность без названия", "en": "Untitled entity"},
    "Untitled": {"ru": "Без названия", "en": "Untitled"},
    "Unknown": {"ru": "Неизвестно", "en": "Unknown"},
    "Current Task": {"ru": "Текущая задача", "en": "Current Task"},
    "Manual Task ID": {"ru": "Ввести ID задачи вручную", "en": "Manual Task ID"},
    "Task Origin Filter": {"ru": "Фильтр источника задачи", "en": "Task Origin Filter"},
    "Task Label Search": {"ru": "Поиск по метке задачи", "en": "Task Label Search"},
    "Task Sort Order": {"ru": "Порядок задач", "en": "Task Sort Order"},
    "Newest First": {"ru": "Сначала новые", "en": "Newest First"},
    "Oldest First": {"ru": "Сначала старые", "en": "Oldest First"},
    "All Origins": {"ru": "Все источники", "en": "All Origins"},
    "Current Artifact": {"ru": "Артефакт из текущего списка", "en": "Current Artifact"},
    "Manual Artifact ID": {"ru": "Ввести ID артефакта вручную", "en": "Manual Artifact ID"},
    "Artifact ID": {"ru": "ID артефакта", "en": "Artifact ID"},
    "Output ID": {"ru": "ID выхода", "en": "Output ID"},
    "Type": {"ru": "Тип", "en": "Type"},
    "Status": {"ru": "Статус", "en": "Status"},
    "Review": {"ru": "Ревью", "en": "Review"},
    "Claims": {"ru": "Утверждения", "en": "Claims"},
    "Sources": {"ru": "Источники", "en": "Sources"},
    "Manifest": {"ru": "Манифест", "en": "Manifest"},
    "Source Links": {"ru": "Связи с источниками", "en": "Source Links"},
    "Artifact #{id} {artifact_type} ({content_type})": {
        "ru": "Артефакт #{id} {artifact_type} ({content_type})",
        "en": "Artifact #{id} {artifact_type} ({content_type})",
    },
    "#{id} | {relation_type} | {score}": {
        "ru": "#{id} | {relation_type} | {score}",
        "en": "#{id} | {relation_type} | {score}",
    },
    "#{id} {label}": {"ru": "#{id} {label}", "en": "#{id} {label}"},
    "#{id} | {output_type} | {title}": {
        "ru": "#{id} | {output_type} | {title}",
        "en": "#{id} | {output_type} | {title}",
    },
    "#{id} | {artifact_type} | {title}": {
        "ru": "#{id} | {artifact_type} | {title}",
        "en": "#{id} | {artifact_type} | {title}",
    },
    "#{id} | {entity_type} | {name}": {
        "ru": "#{id} | {entity_type} | {name}",
        "en": "#{id} | {entity_type} | {name}",
    },
    "{task_id} | {label} | {origin}": {
        "ru": "{task_id} | {label} | {origin}",
        "en": "{task_id} | {label} | {origin}",
    },
    "#{id} | {stage} | {run_type} | {status}": {
        "ru": "#{id} | {stage} | {run_type} | {status}",
        "en": "#{id} | {stage} | {run_type} | {status}",
    },
    "application/octet-stream": {"ru": "application/octet-stream", "en": "application/octet-stream"},
    "Frontmatter": {"ru": "Фронтматтер", "en": "Frontmatter"},
    "Markdown Body": {"ru": "Markdown-тело", "en": "Markdown Body"},
    "Raw Payload": {"ru": "Сырой payload", "en": "Raw Payload"},
    "File-Back": {"ru": "Файлинг", "en": "File-Back"},
    "Artifact": {"ru": "Артефакт", "en": "Artifact"},
    "Scope": {"ru": "Контур", "en": "Scope"},
    "Aliases": {"ru": "Алиасы", "en": "Aliases"},
    "External Refs": {"ru": "Внешние ссылки", "en": "External Refs"},
    "System Health": {"ru": "Состояние системы", "en": "System Health"},
    "All systems operational": {"ru": "Все системы работают штатно", "en": "All systems operational"},
    "Status: {status}": {"ru": "Статус: {status}", "en": "Status: {status}"},
    "DB: {error}": {"ru": "БД: {error}", "en": "DB: {error}"},
    "Release Gate Snapshot": {"ru": "Сводка контрольных проверок релиза", "en": "Release Gate Snapshot"},
    "Latest Pipeline Runs": {"ru": "Последние прогоны пайплайна", "en": "Latest Pipeline Runs"},
    "No pipeline runs available": {"ru": "Прогоны пайплайна не найдены", "en": "No pipeline runs available"},
    "Latest Outputs": {"ru": "Последние выходы", "en": "Latest Outputs"},
    "Release-Critical Operator Surfaces": {"ru": "Критичные операторские поверхности релиза", "en": "Release-Critical Operator Surfaces"},
    "Active scoring model: #{id} {label}": {"ru": "Активная модель: #{id} {label}", "en": "Active scoring model: #{id} {label}"},
    "No active scoring model": {"ru": "Нет активной скоринговой модели", "en": "No active scoring model"},
    "KB master index available: artifact #{id} ({fmt})": {"ru": "Master index KB доступен: артефакт #{id} ({fmt})", "en": "KB master index available: artifact #{id} ({fmt})"},
    "KB master index unavailable": {"ru": "Master index KB недоступен", "en": "KB master index unavailable"},
    "Quick operator checks": {"ru": "Быстрые проверки оператора", "en": "Quick operator checks"},
    "Document Registry": {"ru": "Реестр документов", "en": "Document Registry"},
    "Search": {"ru": "Поиск", "en": "Search"},
    "Specialty filter": {"ru": "Фильтр по специальности", "en": "Specialty filter"},
    "No documents found": {"ru": "Документы не найдены", "en": "No documents found"},
    "Document Detail": {"ru": "Детали документа", "en": "Document Detail"},
    "Current Document": {"ru": "Документ из текущего списка", "en": "Current Document"},
    "Manual Document ID": {"ru": "Ввести ID документа вручную", "en": "Manual Document ID"},
    "Document ID": {"ru": "ID документа", "en": "Document ID"},
    "Document Status Filter": {"ru": "Фильтр статуса документа", "en": "Document Status Filter"},
    "Document Sort Order": {"ru": "Порядок документов", "en": "Document Sort Order"},
    "All Statuses": {"ru": "Все статусы", "en": "All Statuses"},
    "Load Document": {"ru": "Загрузить документ", "en": "Load Document"},
    "Raw Source Artifacts": {"ru": "Сырые исходные артефакты", "en": "Raw Source Artifacts"},
    "Download": {"ru": "Скачать", "en": "Download"},
    "Preview": {"ru": "Предпросмотр", "en": "Preview"},
    "No valid raw artifacts available for current version": {"ru": "Нет валидных сырых артефактов для текущей версии", "en": "No valid raw artifacts available for current version"},
    "Section Search": {"ru": "Поиск по разделам", "en": "Section Search"},
    "Section": {"ru": "Раздел", "en": "Section"},
    "Pipeline Management": {"ru": "Управление пайплайном", "en": "Pipeline Management"},
    "Run Full Sync": {"ru": "Запустить полный sync", "en": "Run Full Sync"},
    "Run Incremental Sync": {"ru": "Запустить инкрементальный sync", "en": "Run Incremental Sync"},
    "Pipeline run started: ID {run_id}": {"ru": "Прогон пайплайна запущен: ID {run_id}", "en": "Pipeline run started: ID {run_id}"},
    "Stage Filter": {"ru": "Фильтр по стадии", "en": "Stage Filter"},
    "Pipeline Status Filter": {"ru": "Фильтр статуса прогона", "en": "Pipeline Status Filter"},
    "Recent Pipeline Runs": {"ru": "Последние прогоны пайплайна", "en": "Recent Pipeline Runs"},
    "Run Detail": {"ru": "Детали прогона", "en": "Run Detail"},
    "Recent Run": {"ru": "Недавний прогон", "en": "Recent Run"},
    "Load Selected Run": {"ru": "Загрузить выбранный прогон", "en": "Load Selected Run"},
    "No pipeline runs yet": {"ru": "Прогонов пайплайна пока нет", "en": "No pipeline runs yet"},
    "All": {"ru": "Все", "en": "All"},
    "Substitution Matrix": {"ru": "Матрица заменяемости", "en": "Substitution Matrix"},
    "Page size": {"ru": "Размер страницы", "en": "Page size"},
    "Scope ID Filter": {"ru": "Фильтр по scope ID", "en": "Scope ID Filter"},
    "Model Version ID Filter": {"ru": "Фильтр по ID версии модели", "en": "Model Version ID Filter"},
    "Molecule From Filter": {"ru": "Фильтр по исходной молекуле", "en": "Molecule From Filter"},
    "0 means no model filter": {"ru": "0 означает отсутствие фильтра по модели", "en": "0 means no model filter"},
    "0 means no molecule filter": {"ru": "0 означает отсутствие фильтра по молекуле", "en": "0 means no molecule filter"},
    "No matrix cells found": {"ru": "Ячейки матрицы не найдены", "en": "No matrix cells found"},
    "Export Matrix": {"ru": "Экспорт матрицы", "en": "Export Matrix"},
    "Format": {"ru": "Формат", "en": "Format"},
    "Use API endpoint: GET /matrix/export?format={fmt}": {"ru": "Используйте API endpoint: GET /matrix/export?format={fmt}", "en": "Use API endpoint: GET /matrix/export?format={fmt}"},
    "Cell Detail": {"ru": "Детали ячейки", "en": "Cell Detail"},
    "Cell Scope": {"ru": "Контур ячейки", "en": "Cell Scope"},
    "Cell Model Version ID": {"ru": "ID версии модели для ячейки", "en": "Cell Model Version ID"},
    "0 means latest available model": {"ru": "0 означает последнюю доступную модель", "en": "0 means latest available model"},
    "Molecule From ID": {"ru": "ID исходной молекулы", "en": "Molecule From ID"},
    "Molecule To ID": {"ru": "ID целевой молекулы", "en": "Molecule To ID"},
    "Load Cell Detail": {"ru": "Загрузить детали ячейки", "en": "Load Cell Detail"},
    "Reviewer Queue": {"ru": "Очередь ревью", "en": "Reviewer Queue"},
    "Auto": {"ru": "Авто", "en": "Auto"},
    "Approved": {"ru": "Подтверждено", "en": "Approved"},
    "Rejected": {"ru": "Отклонено", "en": "Rejected"},
    "Queue": {"ru": "Очередь", "en": "Queue"},
    "Queue Document Version ID": {"ru": "ID версии документа для очереди", "en": "Queue Document Version ID"},
    "0 means no document filter": {"ru": "0 означает отсутствие фильтра по документу", "en": "0 means no document filter"},
    "No evidence awaiting review": {"ru": "Нет элементов доказательств, ожидающих ревью", "en": "No evidence awaiting review"},
    "Recent Review Actions": {"ru": "Последние действия ревью", "en": "Recent Review Actions"},
    "History Target From Queue": {"ru": "Цель истории из текущей очереди", "en": "History Target From Queue"},
    "Manual History Target": {"ru": "Ввести цель истории вручную", "en": "Manual History Target"},
    "History Target Type": {"ru": "Тип цели истории", "en": "History Target Type"},
    "History Target ID": {"ru": "ID цели истории", "en": "History Target ID"},
    "0 means no target filter": {"ru": "0 означает отсутствие фильтра по цели", "en": "0 means no target filter"},
    "No review actions yet": {"ru": "Действий ревью пока нет", "en": "No review actions yet"},
    "Bulk Approve": {"ru": "Массовое подтверждение", "en": "Bulk Approve"},
    "Evidence IDs (comma-separated)": {"ru": "ID доказательств (через запятую)", "en": "Evidence IDs (comma-separated)"},
    "Queued Evidence IDs": {"ru": "ID доказательств из очереди", "en": "Queued Evidence IDs"},
    "Optional quick-pick from current review queue": {"ru": "Быстрый выбор из текущей очереди ревью (необязательно)", "en": "Optional quick-pick from current review queue"},
    "Queued Evidence Target": {"ru": "Цель из текущей очереди доказательств", "en": "Queued Evidence Target"},
    "Manual Target ID": {"ru": "Ввести ID цели вручную", "en": "Manual Target ID"},
    "Bulk Approve Author": {"ru": "Автор массового подтверждения", "en": "Bulk Approve Author"},
    "Use the filtered queue above to identify evidence IDs for bulk approval.": {"ru": "Используйте отфильтрованную очередь выше, чтобы выбрать ID доказательств для массового подтверждения.", "en": "Use the filtered queue above to identify evidence IDs for bulk approval."},
    "Enter at least one evidence ID": {"ru": "Введите хотя бы один ID доказательства", "en": "Enter at least one evidence ID"},
    "Approved {count} evidence items": {"ru": "Подтверждено элементов доказательств: {count}", "en": "Approved {count} evidence items"},
    "Submit Review": {"ru": "Отправить решение ревью", "en": "Submit Review"},
    "Target Type": {"ru": "Тип цели", "en": "Target Type"},
    "Target ID": {"ru": "ID цели", "en": "Target ID"},
    "Action": {"ru": "Действие", "en": "Action"},
    "Reason": {"ru": "Причина", "en": "Reason"},
    "Author": {"ru": "Автор", "en": "Author"},
    "Override Score": {"ru": "Override score", "en": "Override Score"},
    "Submit": {"ru": "Отправить", "en": "Submit"},
    "Review submitted": {"ru": "Ревью отправлено", "en": "Review submitted"},
    "Selected Model": {"ru": "Выбранная модель", "en": "Selected Model"},
    "Ready": {"ru": "Готово", "en": "Ready"},
    "Cells": {"ru": "Ячейки", "en": "Cells"},
    "Pair Scores": {"ru": "Pair scores", "en": "Pair Scores"},
    "Model Actions": {"ru": "Действия модели", "en": "Model Actions"},
    "Refresh Scope Type": {"ru": "Тип refresh scope", "en": "Refresh Scope Type"},
    "Refresh Scope ID": {"ru": "ID refresh scope", "en": "Refresh Scope ID"},
    "Refresh Model": {"ru": "Обновить модель", "en": "Refresh Model"},
    "Refreshed: {pair_scores} pair scores, {matrix_cells} matrix cells": {"ru": "Обновлено: {pair_scores} pair scores, {matrix_cells} matrix cells", "en": "Refreshed: {pair_scores} pair scores, {matrix_cells} matrix cells"},
    "Activation Author": {"ru": "Автор активации", "en": "Activation Author"},
    "Force Activate": {"ru": "Принудительная активация", "en": "Force Activate"},
    "Activate Model": {"ru": "Активировать модель", "en": "Activate Model"},
    "Activated model {label}": {"ru": "Модель активирована: {label}", "en": "Activated model {label}"},
    "Model Diff": {"ru": "Diff моделей", "en": "Model Diff"},
    "Old Version": {"ru": "Старая версия", "en": "Old Version"},
    "New Version": {"ru": "Новая версия", "en": "New Version"},
    "Load Diff": {"ru": "Загрузить diff", "en": "Load Diff"},
    "Added": {"ru": "Добавлено", "en": "Added"},
    "Removed": {"ru": "Удалено", "en": "Removed"},
    "Changed": {"ru": "Изменено", "en": "Changed"},
    "Create Scoring Model Version": {"ru": "Создать версию скоринговой модели", "en": "Create Scoring Model Version"},
    "Version Label": {"ru": "Метка версии", "en": "Version Label"},
    "Weights JSON": {"ru": "Weights JSON", "en": "Weights JSON"},
    "Create": {"ru": "Создать", "en": "Create"},
    "Invalid JSON": {"ru": "Невалидный JSON", "en": "Invalid JSON"},
    "Model created: ID {id}": {"ru": "Модель создана: ID {id}", "en": "Model created: ID {id}"},
    "No scoring models defined": {"ru": "Скоринговые модели не заданы", "en": "No scoring models defined"},
    "Output Type Filter": {"ru": "Фильтр по типу выхода", "en": "Output Type Filter"},
    "File-Back Filter": {"ru": "Фильтр по файлингу", "en": "File-Back Filter"},
    "Review Status Filter": {"ru": "Фильтр по статусу ревью", "en": "Review Status Filter"},
    "Generator Version Filter": {"ru": "Фильтр по версии генератора", "en": "Generator Version Filter"},
    "Artifact ID Filter": {"ru": "Фильтр по ID артефакта", "en": "Artifact ID Filter"},
    "0 means no artifact filter": {"ru": "0 означает отсутствие фильтра по артефакту", "en": "0 means no artifact filter"},
    "Output Search": {"ru": "Поиск по выходам", "en": "Output Search"},
    "Released Outputs Only": {"ru": "Только выпущенные выходы", "en": "Released Outputs Only"},
    "Outputs With Files Only": {"ru": "Только выходы с файлами", "en": "Outputs With Files Only"},
    "No outputs available": {"ru": "Выходы не найдены", "en": "No outputs available"},
    "Output Detail": {"ru": "Детали выхода", "en": "Output Detail"},
    "Current Output": {"ru": "Выход из текущего списка", "en": "Current Output"},
    "Manual Output ID": {"ru": "Ввести ID выхода вручную", "en": "Manual Output ID"},
    "Detail Output ID": {"ru": "ID выхода для деталей", "en": "Detail Output ID"},
    "Load Output Detail": {"ru": "Загрузить детали выхода", "en": "Load Output Detail"},
    "Linked KB artifact: #{id}": {"ru": "Связанный KB артефакт: #{id}", "en": "Linked KB artifact: #{id}"},
    "Load Linked Artifact": {"ru": "Загрузить связанный артефакт", "en": "Load Linked Artifact"},
    "Generate Output": {"ru": "Сгенерировать выход", "en": "Generate Output"},
    "Output Type": {"ru": "Тип выхода", "en": "Output Type"},
    "Title": {"ru": "Заголовок", "en": "Title"},
    "Queue Generation": {"ru": "Поставить генерацию в очередь", "en": "Queue Generation"},
    "Generation queued: {task_id}": {"ru": "Генерация поставлена в очередь: {task_id}", "en": "Generation queued: {task_id}"},
    "File Back Output": {"ru": "Файлинг выхода", "en": "File Back Output"},
    "Current File-Back Output": {"ru": "Выход для файлинга из текущего списка", "en": "Current File-Back Output"},
    "Manual File-Back Output ID": {"ru": "Ввести ID файлинга вручную", "en": "Manual File-Back Output ID"},
    "File Back Status": {"ru": "Статус файлинга", "en": "File Back Status"},
    "Queue File Back": {"ru": "Поставить файлинг в очередь", "en": "Queue File Back"},
    "File-back queued: {task_id}": {"ru": "Файлинг поставлен в очередь: {task_id}", "en": "File-back queued: {task_id}"},
    "Compile KB": {"ru": "Собрать KB", "en": "Compile KB"},
    "Lint KB": {"ru": "Проверить KB", "en": "Lint KB"},
    "KB compile queued: {task_id}": {"ru": "Сборка KB поставлена в очередь: {task_id}", "en": "KB compile queued: {task_id}"},
    "KB lint queued: {task_id}": {"ru": "Lint KB поставлен в очередь: {task_id}", "en": "KB lint queued: {task_id}"},
    "Master Index": {"ru": "Master index", "en": "Master Index"},
    "artifact #{id} {slug}": {"ru": "артефакт #{id} {slug}", "en": "artifact #{id} {slug}"},
    "No master index artifact yet": {"ru": "Артефакта master index пока нет", "en": "No master index artifact yet"},
    "Master Manifest": {"ru": "Манифест master index", "en": "Master Manifest"},
    "Artifacts": {"ru": "Артефакты", "en": "Artifacts"},
    "Artifact Type Filter": {"ru": "Фильтр по типу артефакта", "en": "Artifact Type Filter"},
    "Artifact Status Filter": {"ru": "Фильтр по статусу артефакта", "en": "Artifact Status Filter"},
    "Artifact Review Filter": {"ru": "Фильтр по ревью артефакта", "en": "Artifact Review Filter"},
    "Artifact Generator Filter": {"ru": "Фильтр по генератору артефакта", "en": "Artifact Generator Filter"},
    "Artifact Search": {"ru": "Поиск по артефактам", "en": "Artifact Search"},
    "No KB artifacts available": {"ru": "KB артефакты не найдены", "en": "No KB artifacts available"},
    "Artifact Detail": {"ru": "Детали артефакта", "en": "Artifact Detail"},
    "Load Artifact": {"ru": "Загрузить артефакт", "en": "Load Artifact"},
    "Entities": {"ru": "Сущности", "en": "Entities"},
    "Entity Type Filter": {"ru": "Фильтр по типу сущности", "en": "Entity Type Filter"},
    "Entity Status Filter": {"ru": "Фильтр по статусу сущности", "en": "Entity Status Filter"},
    "Entity Search": {"ru": "Поиск по сущностям", "en": "Entity Search"},
    "No KB entities available": {"ru": "KB сущности не найдены", "en": "No KB entities available"},
    "Entity Detail": {"ru": "Детали сущности", "en": "Entity Detail"},
    "Current Entity": {"ru": "Сущность из текущего списка", "en": "Current Entity"},
    "Manual Entity ID": {"ru": "Ввести ID сущности вручную", "en": "Manual Entity ID"},
    "Entity ID": {"ru": "ID сущности", "en": "Entity ID"},
    "Load Entity": {"ru": "Загрузить сущность", "en": "Load Entity"},
    "Conflicts": {"ru": "Конфликты", "en": "Conflicts"},
    "Conflict Artifact ID Filter": {"ru": "Фильтр конфликтов по ID артефакта", "en": "Conflict Artifact ID Filter"},
    "Conflict Review Filter": {"ru": "Фильтр конфликтов по ревью", "en": "Conflict Review Filter"},
    "No KB conflicts detected": {"ru": "Конфликты KB не обнаружены", "en": "No KB conflicts detected"},
    "Claim Artifact ID Filter": {"ru": "Фильтр claim по ID артефакта", "en": "Claim Artifact ID Filter"},
    "Claim Type Filter": {"ru": "Фильтр по типу claim", "en": "Claim Type Filter"},
    "Claim Review Filter": {"ru": "Фильтр по ревью claim", "en": "Claim Review Filter"},
    "Claims Page Size": {"ru": "Размер страницы claims", "en": "Claims Page Size"},
    "Claim Search": {"ru": "Поиск по claims", "en": "Claim Search"},
    "Conflicted Claims Only": {"ru": "Только конфликтные claims", "en": "Conflicted Claims Only"},
    "No KB claims available": {"ru": "KB claims не найдены", "en": "No KB claims available"},
    "Task ID": {"ru": "ID задачи", "en": "Task ID"},
    "Include Result": {"ru": "Включить результат", "en": "Include Result"},
    "Load Task Status": {"ru": "Загрузить статус задачи", "en": "Load Task Status"},
    "Enter a task ID": {"ru": "Введите ID задачи", "en": "Enter a task ID"},
    "API error: {error}": {"ru": "Ошибка API: {error}", "en": "API error: {error}"},
    "generator={value}": {"ru": "генератор={value}", "en": "generator={value}"},
    "released_at={released_at} | generator={generator}": {"ru": "released_at={released_at} | генератор={generator}", "en": "released_at={released_at} | generator={generator}"},
    "global": {"ru": "глобальный", "en": "global"},
    "disease": {"ru": "заболевание", "en": "disease"},
    "csv": {"ru": "csv", "en": "csv"},
    "jsonl": {"ru": "jsonl", "en": "jsonl"},
    "memo": {"ru": "мемо", "en": "memo"},
    "accepted": {"ru": "принято", "en": "accepted"},
    "rejected": {"ru": "отклонено", "en": "rejected"},
    "needs_review": {"ru": "нужно ревью", "en": "needs_review"},
    "approved": {"ru": "подтверждено", "en": "approved"},
    "draft": {"ru": "черновик", "en": "draft"},
    "auto": {"ru": "авто", "en": "auto"},
    "active": {"ru": "активный", "en": "active"},
    "archived": {"ru": "архивный", "en": "archived"},
    "pending": {"ru": "в ожидании", "en": "pending"},
    "none": {"ru": "нет", "en": "none"},
    "n/a": {"ru": "н/д", "en": "n/a"},
    "source_digest": {"ru": "source_digest", "en": "source_digest"},
    "entity_page": {"ru": "entity_page", "en": "entity_page"},
    "glossary_term": {"ru": "glossary_term", "en": "glossary_term"},
    "open_question": {"ru": "open_question", "en": "open_question"},
    "master_index": {"ru": "master_index", "en": "master_index"},
    "document": {"ru": "документ", "en": "document"},
    "molecule": {"ru": "молекула", "en": "molecule"},
    "fact": {"ru": "факт", "en": "fact"},
    "inference": {"ru": "вывод", "en": "inference"},
    "hypothesis": {"ru": "гипотеза", "en": "hypothesis"},
    "pair_evidence": {"ru": "pair_evidence", "en": "pair_evidence"},
    "approve": {"ru": "подтвердить", "en": "approve"},
    "reject": {"ru": "отклонить", "en": "reject"},
    "override": {"ru": "override", "en": "override"},
    "yes": {"ru": "да", "en": "yes"},
    "no": {"ru": "нет", "en": "no"},
    "id": {"ru": "ID", "en": "id"},
    "status": {"ru": "статус", "en": "status"},
    "probe": {"ru": "probe", "en": "probe"},
    "discovery": {"ru": "discovery", "en": "discovery"},
    "fetch": {"ru": "fetch", "en": "fetch"},
    "normalize": {"ru": "normalize", "en": "normalize"},
    "extract": {"ru": "extract", "en": "extract"},
    "full": {"ru": "полный", "en": "full"},
    "incremental": {"ru": "инкрементальный", "en": "incremental"},
    "success": {"ru": "успешно", "en": "success"},
    "global": {"ru": "global", "en": "global"},
    "disease": {"ru": "disease", "en": "disease"},
    "discovered": {"ru": "обнаружено", "en": "discovered"},
    "fetched": {"ru": "загружено", "en": "fetched"},
    "finished_at": {"ru": "завершено", "en": "finished_at"},
    "type": {"ru": "тип", "en": "type"},
    "title": {"ru": "заголовок", "en": "title"},
    "specialty": {"ru": "специальность", "en": "specialty"},
    "external_id": {"ru": "external_id", "en": "external_id"},
    "context_id": {"ru": "context_id", "en": "context_id"},
    "from": {"ru": "от", "en": "from"},
    "to": {"ru": "к", "en": "to"},
    "relation": {"ru": "связь", "en": "relation"},
    "score": {"ru": "скор", "en": "score"},
    "model_version_id": {"ru": "ID версии модели", "en": "model_version_id"},
    "version_label": {"ru": "метка версии", "en": "version_label"},
    "is_active": {"ru": "активна", "en": "is_active"},
    "cell_count": {"ru": "число ячеек", "en": "cell_count"},
    "pcs_count": {"ru": "число pair scores", "en": "pcs_count"},
    "low_confidence_ratio": {"ru": "доля low confidence", "en": "low_confidence_ratio"},
    "artifact_id": {"ru": "ID артефакта", "en": "artifact_id"},
    "released_at": {"ru": "released_at", "en": "released_at"},
    "slug": {"ru": "slug", "en": "slug"},
    "canonical_name": {"ru": "каноническое имя", "en": "canonical_name"},
    "alias_count": {"ru": "число алиасов", "en": "alias_count"},
    "external_ref_count": {"ru": "число внешних ссылок", "en": "external_ref_count"},
    "conflict_group_id": {"ru": "ID группы конфликта", "en": "conflict_group_id"},
    "claim_count": {"ru": "число claims", "en": "claim_count"},
    "artifact_ids": {"ru": "ID артефактов", "en": "artifact_ids"},
    "claim_ids": {"ru": "ID claims", "en": "claim_ids"},
    "claim_previews": {"ru": "превью claims", "en": "claim_previews"},
    "conflicted": {"ru": "конфликтный", "en": "conflicted"},
    "confidence": {"ru": "уверенность", "en": "confidence"},
    "text": {"ru": "текст", "en": "text"},
    "target_type": {"ru": "тип target", "en": "target_type"},
    "target_id": {"ru": "ID target", "en": "target_id"},
    "created_at": {"ru": "создано", "en": "created_at"},
    "review_status": {"ru": "статус ревью", "en": "review_status"},
    "file_back_status": {"ru": "статус файлинга", "en": "file_back_status"},
    "generator_version": {"ru": "версия генератора", "en": "generator_version"},
    "task_id": {"ru": "ID задачи", "en": "task_id"},
    "label": {"ru": "метка", "en": "label"},
    "origin": {"ru": "источник", "en": "origin"},
    "queued_at": {"ru": "поставлено в очередь", "en": "queued_at"},
    "sync_full": {"ru": "полный sync", "en": "sync_full"},
    "sync_incremental": {"ru": "инкрементальный sync", "en": "sync_incremental"},
    "output_generate": {"ru": "генерация выхода", "en": "output_generate"},
    "output_file_back": {"ru": "файлинг выхода", "en": "output_file_back"},
    "kb_compile": {"ru": "сборка KB", "en": "kb_compile"},
    "kb_lint": {"ru": "lint KB", "en": "kb_lint"},
    "pipeline": {"ru": "пайплайн", "en": "pipeline"},
    "outputs": {"ru": "выходы", "en": "outputs"},
    "knowledge_base": {"ru": "база знаний", "en": "knowledge_base"},
}


def set_current_language(language: str) -> str:
    global _CURRENT_LANGUAGE
    if language not in LANGUAGE_OPTIONS:
        language = DEFAULT_LANGUAGE
    _CURRENT_LANGUAGE = language
    return _CURRENT_LANGUAGE


def get_current_language() -> str:
    return _CURRENT_LANGUAGE


def tr(key: str, **kwargs: Any) -> str:
    translations = TRANSLATIONS.get(key)
    if translations is None:
        template = key
    else:
        template = translations.get(_CURRENT_LANGUAGE) or translations.get(DEFAULT_LANGUAGE) or key
    if kwargs:
        return template.format(**kwargs)
    return template


def translate_markup_text(text: str) -> str:
    if text.startswith("**") and text.endswith("**") and len(text) > 4:
        return f"**{tr(text[2:-2])}**"
    return tr(text)


def language_label(language: str) -> str:
    labels = {
        "ru": {"ru": "Русский", "en": "Russian"},
        "en": {"ru": "Английский", "en": "English"},
    }
    return labels.get(language, labels[DEFAULT_LANGUAGE]).get(_CURRENT_LANGUAGE, language)


def load_language_preference() -> str:
    try:
        if not LANGUAGE_STORAGE_PATH.exists():
            return DEFAULT_LANGUAGE
        payload = json.loads(LANGUAGE_STORAGE_PATH.read_text(encoding="utf-8"))
        language = payload.get("language", DEFAULT_LANGUAGE)
        if language in LANGUAGE_OPTIONS:
            return language
    except (OSError, json.JSONDecodeError):
        pass
    return DEFAULT_LANGUAGE


def save_language_preference(language: str) -> None:
    if language not in LANGUAGE_OPTIONS:
        return
    LANGUAGE_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LANGUAGE_STORAGE_PATH.write_text(
        json.dumps({"language": language}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def init_language_state() -> str:
    if st.session_state.get("ui_language") not in LANGUAGE_OPTIONS:
        st.session_state["ui_language"] = load_language_preference()
    return set_current_language(st.session_state["ui_language"])


def persist_language(language: str) -> str:
    language = set_current_language(language)
    st.session_state["ui_language"] = language
    save_language_preference(language)
    return language


def _translate_cell_value(value: Any) -> Any:
    if isinstance(value, bool):
        return tr("yes") if value else tr("no")
    if isinstance(value, str):
        return tr(value)
    return value


def translate_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    translated = dataframe.rename(columns=lambda column: tr(str(column)))
    return translated.map(_translate_cell_value)


def _translate_help(kwargs: dict[str, Any]) -> None:
    if isinstance(kwargs.get("help"), str):
        kwargs["help"] = tr(kwargs["help"])


def _patch_method(name: str, transform: Callable[[list[Any], dict[str, Any]], tuple[list[Any], dict[str, Any]]]) -> None:
    original = getattr(DeltaGenerator, name, None)
    if original is None or getattr(original, "_cr_i18n_wrapped", False):
        return

    def wrapped(self: DeltaGenerator, *args: Any, **kwargs: Any):
        mutable_args = list(args)
        mutable_args, kwargs = transform(mutable_args, kwargs)
        return original(self, *mutable_args, **kwargs)

    wrapped._cr_i18n_wrapped = True  # type: ignore[attr-defined]
    setattr(DeltaGenerator, name, wrapped)


def _patch_streamlit_function(
    name: str,
    transform: Callable[[list[Any], dict[str, Any]], tuple[list[Any], dict[str, Any]]],
) -> None:
    original = getattr(st, name, None)
    if original is None or getattr(original, "_cr_i18n_wrapped", False):
        return

    def wrapped(*args: Any, **kwargs: Any):
        mutable_args = list(args)
        mutable_args, kwargs = transform(mutable_args, kwargs)
        return original(*mutable_args, **kwargs)

    wrapped._cr_i18n_wrapped = True  # type: ignore[attr-defined]
    setattr(st, name, wrapped)


def _transform_label(args: list[Any], kwargs: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    if args and isinstance(args[0], str):
        args[0] = translate_markup_text(args[0])
    _translate_help(kwargs)
    return args, kwargs


def _transform_metric(args: list[Any], kwargs: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    if args and isinstance(args[0], str):
        args[0] = tr(args[0])
    if len(args) > 1 and isinstance(args[1], str):
        args[1] = tr(args[1])
    if isinstance(kwargs.get("label"), str):
        kwargs["label"] = tr(kwargs["label"])
    if isinstance(kwargs.get("value"), str):
        kwargs["value"] = tr(kwargs["value"])
    return args, kwargs


def _transform_select(args: list[Any], kwargs: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    args, kwargs = _transform_label(args, kwargs)
    if "format_func" not in kwargs:
        kwargs["format_func"] = lambda option: tr(option) if isinstance(option, str) else option
    return args, kwargs


def _transform_dataframe(args: list[Any], kwargs: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    if args and isinstance(args[0], pd.DataFrame):
        args[0] = translate_dataframe(args[0])
    elif isinstance(kwargs.get("data"), pd.DataFrame):
        kwargs["data"] = translate_dataframe(kwargs["data"])
    return args, kwargs


def install_streamlit_i18n() -> None:
    global _PATCHED
    if _PATCHED:
        return

    label_methods = (
        "title",
        "header",
        "subheader",
        "markdown",
        "caption",
        "info",
        "warning",
        "success",
        "error",
        "button",
        "checkbox",
        "text_input",
        "text_area",
        "number_input",
        "link_button",
        "expander",
        "form_submit_button",
    )
    for name in label_methods:
        _patch_method(name, _transform_label)
        _patch_streamlit_function(name, _transform_label)

    for name in ("selectbox", "radio"):
        _patch_method(name, _transform_select)
        _patch_streamlit_function(name, _transform_select)

    _patch_method("metric", _transform_metric)
    _patch_streamlit_function("metric", _transform_metric)
    _patch_method("dataframe", _transform_dataframe)
    _patch_streamlit_function("dataframe", _transform_dataframe)
    _PATCHED = True