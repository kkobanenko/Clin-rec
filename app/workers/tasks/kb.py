"""Фоновые задачи KB: compile, lint, backlinks, conflicts, outputs (TZ §19)."""

import logging

from app.services.index_stats import collect_index_stats, refresh_knowledge_artifact_fts
from app.services.knowledge_backlinks import refresh_all_backlinks_sync
from app.services.knowledge_compile import KnowledgeCompileService
from app.services.knowledge_conflicts import detect_conflicts_sync
from app.services.knowledge_lint import KnowledgeLintService
from app.services.output_release_service import apply_file_back, create_pending_output
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.kb.compile_document_version", queue="compile_kb")
def compile_document_version(version_id: int) -> dict:
    """Пересборка source_digest и master_index для одной версии документа."""
    return KnowledgeCompileService().compile_version(version_id)


@celery_app.task(name="app.workers.tasks.kb.run_compile_kb", queue="compile_kb")
def run_compile_kb() -> dict:
    """Полная пересборка digest для всех текущих версий и master_index."""
    return KnowledgeCompileService().compile_all_current()


@celery_app.task(name="app.workers.tasks.kb.lint_kb", queue="lint_kb")
def lint_kb() -> dict:
    """Базовые проверки provenance и claims."""
    return KnowledgeLintService().run()


@celery_app.task(name="app.workers.tasks.kb.refresh_backlinks", queue="refresh_backlinks")
def refresh_backlinks() -> dict:
    """Парсинг [[slug]] и markdown-ссылок в knowledge_artifact.content_md → artifact_backlink."""
    return refresh_all_backlinks_sync()


@celery_app.task(name="app.workers.tasks.kb.detect_conflicts", queue="detect_conflicts")
def detect_conflicts() -> dict:
    return detect_conflicts_sync()


@celery_app.task(name="app.workers.tasks.kb.generate_outputs", queue="generate_outputs")
def generate_outputs(
    output_type: str = "memo",
    title: str | None = None,
    scope_json: dict | None = None,
) -> dict:
    """Создаёт запись output_release (черновик); генерация файла — отдельный шаг."""
    output_id = create_pending_output(output_type, title, scope_json)
    logger.info("generate_outputs id=%s type=%s", output_id, output_type)
    return {"status": "ok", "output_id": output_id, "output_type": output_type}


@celery_app.task(name="app.workers.tasks.kb.file_outputs", queue="file_outputs")
def file_outputs(output_id: int, file_back_status: str) -> dict:
    """Output filing: обновление output_release в БД."""
    result = apply_file_back(output_id, file_back_status)
    logger.info("file_outputs result=%s", result)
    return result


@celery_app.task(name="app.workers.tasks.kb.rebuild_indexes", queue="rebuild_indexes")
def rebuild_indexes() -> dict:
    """FTS по knowledge_artifact + снимок счётчиков таблиц (TZ §19)."""
    fts = refresh_knowledge_artifact_fts()
    stats = collect_index_stats()
    stats.update(fts)
    logger.info("rebuild_indexes stats=%s", stats)
    return stats
