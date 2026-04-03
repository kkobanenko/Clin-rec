"""Справочная информация о стадиях данных (хранилище + БД)."""

from fastapi import APIRouter

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
