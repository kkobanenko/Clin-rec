"""Справочная информация о стадиях данных (хранилище + БД)."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.clinical import ClinicalContext
from app.models.document import DocumentVersion, SourceArtifact
from app.models.evidence import MatrixCell, PairEvidence
from app.models.pipeline_event import PipelineEventLog
from app.models.text import DocumentSection, TextFragment

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/storage-stages")
async def storage_stages():
    """
    Когда появляются каталог, raw в S3, нормализованный текст, compiled KB и outputs.
    Дублирует содержание docs/STORAGE_STAGES.md в машиночитаемом виде.
    """
    return {
        "postgresql": [
            {
                "stage": "discovery",
                "tables": ["pipeline_run", "document_registry"],
                "note": "Каталог и URL; полного текста документа в БД ещё нет.",
            },
            {
                "stage": "probe",
                "tables": ["document_version"],
                "note": "Версии документов, классификация primary source.",
            },
            {
                "stage": "fetch",
                "tables": ["source_artifact"],
                "note": "Метаданные raw: raw_path указывает на объект в S3/MinIO.",
            },
            {
                "stage": "normalize",
                "tables": ["document_section", "text_fragment"],
                "note": "Нормализованный корпус в таблицах (индексированный текст).",
            },
            {
                "stage": "compile_kb",
                "tables": ["knowledge_artifact", "artifact_source_link"],
                "note": "Source digest, master index; provenance на document_version.",
            },
            {
                "stage": "extract_score",
                "tables": ["clinical_context", "pair_evidence", "matrix_cell", "..."],
                "note": "По мере включения задач extract/score.",
            },
            {
                "stage": "outputs",
                "tables": ["output_release"],
                "note": "Черновики и релизы аналитических артефактов.",
            },
        ],
        "object_storage_s3": [
            {
                "stage": "fetch",
                "note": "Здесь появляются байты HTML/PDF (реальные файлы документов).",
                "key_example": "documents/{registry_id}/versions/{version_id}/html.html",
            },
        ],
        "documentation_markdown": "docs/STORAGE_STAGES.md",
    }


@router.get("/corpus-stats", summary="Corpus statistics across all current versions")
async def corpus_stats(db: AsyncSession = Depends(get_db)):
    """Return live corpus statistics for monitoring and release evidence.

    Breaks down counts by artifact type, fragment content_kind,
    and pipeline stage completion.
    """
    # Current versions count
    current_version_count = (
        await db.execute(
            select(func.count(DocumentVersion.id)).where(DocumentVersion.is_current.is_(True))
        )
    ).scalar_one()

    # Artifact type breakdown
    art_result = await db.execute(
        select(SourceArtifact.artifact_type, func.count(SourceArtifact.id))
        .join(DocumentVersion, SourceArtifact.document_version_id == DocumentVersion.id)
        .where(DocumentVersion.is_current.is_(True))
        .group_by(SourceArtifact.artifact_type)
    )
    artifact_type_counts = {row[0]: row[1] for row in art_result.all()}

    # Section count
    section_count = (
        await db.execute(
            select(func.count(DocumentSection.id))
            .join(DocumentVersion, DocumentSection.document_version_id == DocumentVersion.id)
            .where(DocumentVersion.is_current.is_(True))
        )
    ).scalar_one()

    # Fragment content_kind breakdown
    ck_result = await db.execute(
        select(
            TextFragment.content_kind,
            func.count(TextFragment.id),
        )
        .join(DocumentSection, TextFragment.section_id == DocumentSection.id)
        .join(DocumentVersion, DocumentSection.document_version_id == DocumentVersion.id)
        .where(DocumentVersion.is_current.is_(True))
        .group_by(TextFragment.content_kind)
    )
    content_kind_counts = {(row[0] or "null"): row[1] for row in ck_result.all()}

    # Fragment source_artifact_type breakdown (traceability)
    sat_result = await db.execute(
        select(
            TextFragment.source_artifact_type,
            func.count(TextFragment.id),
        )
        .join(DocumentSection, TextFragment.section_id == DocumentSection.id)
        .join(DocumentVersion, DocumentSection.document_version_id == DocumentVersion.id)
        .where(DocumentVersion.is_current.is_(True))
        .group_by(TextFragment.source_artifact_type)
    )
    source_artifact_type_counts = {(row[0] or "null"): row[1] for row in sat_result.all()}

    # Pipeline stage completion (latest event per version per stage)
    stage_result = await db.execute(
        select(PipelineEventLog.stage, PipelineEventLog.status, func.count(PipelineEventLog.id))
        .where(PipelineEventLog.document_version_id.isnot(None))
        .group_by(PipelineEventLog.stage, PipelineEventLog.status)
    )
    pipeline_stage_counts: dict[str, dict[str, int]] = {}
    for stage, status, cnt in stage_result.all():
        pipeline_stage_counts.setdefault(stage, {})[status] = cnt

    # Evidence and matrix
    pair_evidence_total = (await db.execute(select(func.count(PairEvidence.id)))).scalar_one()
    matrix_cell_total = (await db.execute(select(func.count(MatrixCell.id)))).scalar_one()
    clinical_context_total = (await db.execute(select(func.count(ClinicalContext.id)))).scalar_one()

    return {
        "current_versions": current_version_count,
        "artifact_type_counts": artifact_type_counts,
        "section_count": section_count,
        "content_kind_counts": content_kind_counts,
        "source_artifact_type_counts": source_artifact_type_counts,
        "pipeline_stage_counts": pipeline_stage_counts,
        "pair_evidence_total": pair_evidence_total,
        "matrix_cell_total": matrix_cell_total,
        "clinical_context_total": clinical_context_total,
    }

