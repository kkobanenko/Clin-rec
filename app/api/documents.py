import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db
from app.core.storage import download_artifact
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.models.text import DocumentSection, TextFragment
from app.schemas.documents import (
    DocumentDetailOut,
    DocumentRegistryOut,
    DocumentVersionOut,
    FragmentListOut,
    FragmentOut,
    NormalizedDocumentOut,
    SectionOut,
    SourceArtifactOut,
)
from app.schemas.pipeline import PaginatedResponse
from app.workers.tasks.extract import extract_document
from app.workers.tasks.fetch import fetch_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=PaginatedResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    specialty: str | None = None,
    status: str | None = None,
    search: str | None = None,
):
    query = select(DocumentRegistry)
    count_query = select(func.count(DocumentRegistry.id))

    if specialty:
        query = query.where(DocumentRegistry.specialty == specialty)
        count_query = count_query.where(DocumentRegistry.specialty == specialty)
    if status:
        query = query.where(DocumentRegistry.status == status)
        count_query = count_query.where(DocumentRegistry.status == status)
    if search:
        query = query.where(DocumentRegistry.title.ilike(f"%{search}%"))
        count_query = count_query.where(DocumentRegistry.title.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(DocumentRegistry.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [DocumentRegistryOut.model_validate(r) for r in result.scalars().all()]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if page_size else 1,
    )


@router.get("/{document_id}", response_model=DocumentDetailOut)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DocumentRegistry).where(DocumentRegistry.id == document_id).options(selectinload(DocumentRegistry.versions))
    )
    doc = result.scalar_one()

    version_ids = [v.id for v in doc.versions]
    artifacts = []
    if version_ids:
        art_result = await db.execute(select(SourceArtifact).where(SourceArtifact.document_version_id.in_(version_ids)))
        raw_artifacts = list(art_result.scalars().all())
        # Для каждого (version, artifact_type) оставляем самый свежий артефакт.
        latest_by_kind: dict[tuple[int, str], SourceArtifact] = {}
        for art in raw_artifacts:
            key = (art.document_version_id, art.artifact_type)
            current = latest_by_kind.get(key)
            if current is None:
                latest_by_kind[key] = art
                continue
            current_ts = current.fetched_at or current.id
            new_ts = art.fetched_at or art.id
            if new_ts >= current_ts:
                latest_by_kind[key] = art
        artifacts = [SourceArtifactOut.model_validate(a) for a in latest_by_kind.values()]

    return DocumentDetailOut(
        registry=DocumentRegistryOut.model_validate(doc),
        versions=[DocumentVersionOut.model_validate(v) for v in doc.versions],
        artifacts=artifacts,
    )


@router.get("/{document_id}/content", response_model=NormalizedDocumentOut)
async def get_document_content(document_id: int, db: AsyncSession = Depends(get_db)):
    version_result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.registry_id == document_id, DocumentVersion.is_current.is_(True))
        .order_by(DocumentVersion.detected_at.desc())
        .limit(1)
    )
    version = version_result.scalar_one()

    sections_result = await db.execute(
        select(DocumentSection)
        .where(DocumentSection.document_version_id == version.id)
        .order_by(DocumentSection.section_order)
    )
    sections = [SectionOut.model_validate(s) for s in sections_result.scalars().all()]

    return NormalizedDocumentOut(document_id=document_id, version_id=version.id, sections=sections)


@router.get("/{document_id}/fragments", response_model=FragmentListOut)
async def get_document_fragments(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    section_id: int | None = None,
):
    version_result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.registry_id == document_id, DocumentVersion.is_current.is_(True))
        .order_by(DocumentVersion.detected_at.desc())
        .limit(1)
    )
    version = version_result.scalar_one()

    sections_result = await db.execute(
        select(DocumentSection.id).where(DocumentSection.document_version_id == version.id)
    )
    section_ids = [s for (s,) in sections_result.all()]

    if section_id and section_id in section_ids:
        section_ids = [section_id]

    fragments_query = (
        select(TextFragment)
        .where(TextFragment.section_id.in_(section_ids))
        .order_by(TextFragment.section_id, TextFragment.fragment_order)
    )
    frag_result = await db.execute(fragments_query)
    fragments = [FragmentOut.model_validate(f) for f in frag_result.scalars().all()]

    return FragmentListOut(
        document_id=document_id,
        version_id=version.id,
        fragments=fragments,
        total=len(fragments),
    )


@router.get("/{document_id}/artifacts/{artifact_id}/download")
async def download_source_artifact(document_id: int, artifact_id: int, db: AsyncSession = Depends(get_db)):
    """
    Скачать байты сырья из object storage (MinIO/S3) по записи source_artifact.
    Удобно для UI и проверки без обхода внешнего SPA-сайта.
    """
    result = await db.execute(
        select(SourceArtifact)
        .join(DocumentVersion, SourceArtifact.document_version_id == DocumentVersion.id)
        .where(
            DocumentVersion.registry_id == document_id,
            SourceArtifact.id == artifact_id,
        )
    )
    art = result.scalar_one_or_none()
    if art is None:
        raise HTTPException(status_code=404, detail="Artifact not found for this document")

    data = await asyncio.to_thread(download_artifact, art.raw_path)
    media = art.content_type or "application/octet-stream"
    ext = "html" if art.artifact_type == "html" else ("pdf" if art.artifact_type == "pdf" else "bin")
    filename = f"doc{document_id}_{art.artifact_type}_{artifact_id}.{ext}"
    return StreamingResponse(
        iter([data]),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{document_id}/reextract", status_code=202)
async def queue_reextract_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """Повторный прогон clinical extraction + pair_evidence для текущей версии (после обновления эвристик МНН)."""
    vr = await db.execute(
        select(DocumentVersion.id).where(
            DocumentVersion.registry_id == document_id,
            DocumentVersion.is_current.is_(True),
        )
    )
    version_id = vr.scalar_one_or_none()
    if version_id is None:
        raise HTTPException(status_code=404, detail="No current document version")
    async_result = extract_document.delay(version_id)
    return {
        "task_id": async_result.id,
        "version_id": version_id,
        "message": "extract_document queued",
    }


@router.post("/{document_id}/refetch-normalize", status_code=202)
async def queue_refetch_normalize_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """Повторный прогон fetch -> normalize для текущей версии документа."""
    vr = await db.execute(
        select(DocumentVersion.id).where(
            DocumentVersion.registry_id == document_id,
            DocumentVersion.is_current.is_(True),
        )
    )
    version_id = vr.scalar_one_or_none()
    if version_id is None:
        raise HTTPException(status_code=404, detail="No current document version")

    async_result = fetch_document.delay(version_id)
    return {
        "task_id": async_result.id,
        "version_id": version_id,
        "message": "fetch_document queued (normalize will run automatically on success)",
    }
