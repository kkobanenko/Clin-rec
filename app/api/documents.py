from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from collections import defaultdict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.storage import download_artifact
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.models.pipeline_event import PipelineEventLog
from app.schemas.diagnostics import CorpusCoverageOut, VersionEvidenceStateOut
from app.schemas.documents import DocumentArtifactListOut
from app.models.text import DocumentSection, TextFragment
from app.services.artifact_validation import validate_artifact_payload
from app.services.evidence_diagnostics import EvidenceDiagnosticsService
from app.schemas.documents import (
    DocumentDetailOut,
    SourceArtifactAccessOut,
    DocumentRegistryOut,
    DocumentVersionOut,
    FragmentListOut,
    FragmentOut,
    NormalizedDocumentOut,
    PipelineOutcomeOut,
    SectionOut,
    SectionWithFragmentsOut,
    SourceArtifactOut,
)
from app.schemas.pipeline import PaginatedResponse

router = APIRouter(prefix="/documents", tags=["documents"])

TERMINAL_PIPELINE_STATUSES = ["success", "degraded", "failed", "failure"]
CONTENT_PRESENT_PIPELINE_STATUSES = ["success"]


def _build_public_registry_out(doc: DocumentRegistry) -> DocumentRegistryOut:
    """Hide synthetic fallback URLs from user-facing API output without changing DB state."""
    registry = DocumentRegistryOut.model_validate(doc)
    payload = getattr(doc, "source_payload_json", None) or {}
    if not isinstance(payload, dict) or not payload.get("dom_row"):
        return registry

    external_id = getattr(doc, "external_id", None)
    if not external_id:
        return registry

    base_url = settings.rubricator_base_url.rstrip("/")
    synthetic_card_url = f"{base_url}/{settings.rubricator_view_path.strip('/')}/{external_id}"
    synthetic_pdf_url = f"{base_url}/{settings.rubricator_pdf_path.strip('/')}/{external_id}"

    updates = {}
    if registry.card_url == synthetic_card_url:
        updates["card_url"] = None
    if registry.html_url == synthetic_card_url:
        updates["html_url"] = None
    if registry.pdf_url == synthetic_pdf_url:
        updates["pdf_url"] = None

    return registry.model_copy(update=updates) if updates else registry


async def _get_current_version(db: AsyncSession, document_id: int) -> DocumentVersion:
    version_result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.registry_id == document_id, DocumentVersion.is_current.is_(True))
        .order_by(DocumentVersion.detected_at.desc())
        .limit(1)
    )
    version = version_result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=404, detail="Current document version not found")
    return version


def _artifact_access_out(document_id: int, artifact: SourceArtifact) -> SourceArtifactAccessOut:
    base_path = f"/documents/{document_id}/artifacts/{artifact.id}/download"
    return SourceArtifactAccessOut(
        id=artifact.id,
        document_version_id=artifact.document_version_id,
        artifact_type=artifact.artifact_type,
        raw_path=artifact.raw_path,
        content_hash=artifact.content_hash,
        content_type=artifact.content_type,
        fetched_at=artifact.fetched_at,
        download_url=base_path,
        preview_url=f"{base_path}?disposition=inline",
    )


def _artifact_filename(artifact: SourceArtifact) -> str:
    extension = "bin"
    if artifact.artifact_type == "html":
        extension = "html"
    elif artifact.artifact_type == "pdf":
        extension = "pdf"
    return f"document_artifact_{artifact.id}.{extension}"


async def _get_current_valid_artifacts(db: AsyncSession, document_id: int) -> tuple[DocumentVersion, list[SourceArtifact]]:
    version = await _get_current_version(db, document_id)
    artifact_result = await db.execute(
        select(SourceArtifact)
        .where(SourceArtifact.document_version_id == version.id)
        .order_by(SourceArtifact.fetched_at.desc(), SourceArtifact.id.desc())
    )
    artifacts = artifact_result.scalars().all()

    valid_artifacts: list[SourceArtifact] = []
    for artifact in artifacts:
        raw_data = download_artifact(artifact.raw_path)
        validation = validate_artifact_payload(artifact.artifact_type, artifact.content_type, raw_data)
        if validation.is_valid:
            valid_artifacts.append(artifact)

    return version, valid_artifacts


async def _get_latest_pipeline_outcome(
    db: AsyncSession,
    version_id: int,
    *,
    prefer_success: bool = False,
) -> PipelineOutcomeOut | None:
    if prefer_success:
        success_result = await db.execute(
            select(PipelineEventLog)
            .where(
                PipelineEventLog.document_version_id == version_id,
                PipelineEventLog.stage.in_(["normalize", "fetch", "probe", "extract"]),
                PipelineEventLog.status.in_(CONTENT_PRESENT_PIPELINE_STATUSES),
            )
            .order_by(PipelineEventLog.created_at.desc(), PipelineEventLog.id.desc())
            .limit(1)
        )
        event = success_result.scalar_one_or_none()
        if event is not None:
            detail_json = event.detail_json or {}
            return PipelineOutcomeOut(
                stage=event.stage,
                status=event.status,
                message=event.message,
                reason_code=detail_json.get("reason_code"),
                created_at=event.created_at,
            )

    terminal_result = await db.execute(
        select(PipelineEventLog)
        .where(
            PipelineEventLog.document_version_id == version_id,
            PipelineEventLog.stage.in_(["normalize", "fetch", "probe", "extract"]),
            PipelineEventLog.status.in_(TERMINAL_PIPELINE_STATUSES),
        )
        .order_by(PipelineEventLog.created_at.desc(), PipelineEventLog.id.desc())
        .limit(1)
    )
    event = terminal_result.scalar_one_or_none()
    if event is None:
        fallback_result = await db.execute(
            select(PipelineEventLog)
            .where(
                PipelineEventLog.document_version_id == version_id,
                PipelineEventLog.stage.in_(["normalize", "fetch", "probe", "extract"]),
            )
            .order_by(PipelineEventLog.created_at.desc(), PipelineEventLog.id.desc())
            .limit(1)
        )
        event = fallback_result.scalar_one_or_none()
    if event is None:
        return None
    detail_json = event.detail_json or {}
    return PipelineOutcomeOut(
        stage=event.stage,
        status=event.status,
        message=event.message,
        reason_code=detail_json.get("reason_code"),
        created_at=event.created_at,
    )


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
    items = [_build_public_registry_out(r) for r in result.scalars().all()]

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
        artifacts = [SourceArtifactOut.model_validate(a) for a in art_result.scalars().all()]

    return DocumentDetailOut(
        registry=_build_public_registry_out(doc),
        versions=[DocumentVersionOut.model_validate(v) for v in doc.versions],
        artifacts=artifacts,
    )


@router.get("/{document_id}/artifacts", response_model=DocumentArtifactListOut)
async def list_document_artifacts(document_id: int, db: AsyncSession = Depends(get_db)):
    version, artifacts = await _get_current_valid_artifacts(db, document_id)
    return DocumentArtifactListOut(
        document_id=document_id,
        version_id=version.id,
        artifacts=[_artifact_access_out(document_id, artifact) for artifact in artifacts],
        total=len(artifacts),
    )


@router.get("/{document_id}/artifacts/{artifact_id}/download")
async def download_document_artifact(
    document_id: int,
    artifact_id: int,
    disposition: str = Query("attachment", pattern="^(attachment|inline)$"),
    db: AsyncSession = Depends(get_db),
):
    version, artifacts = await _get_current_valid_artifacts(db, document_id)
    artifact = next((item for item in artifacts if item.id == artifact_id), None)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    raw_data = download_artifact(artifact.raw_path)
    filename = _artifact_filename(artifact)
    media_type = artifact.content_type or "application/octet-stream"
    headers = {"Content-Disposition": f'{disposition}; filename="{filename}"'}
    return StreamingResponse(iter([raw_data]), media_type=media_type, headers=headers)


@router.get("/{document_id}/content", response_model=NormalizedDocumentOut)
async def get_document_content(document_id: int, db: AsyncSession = Depends(get_db)):
    version = await _get_current_version(db, document_id)

    sections_result = await db.execute(
        select(DocumentSection)
        .where(DocumentSection.document_version_id == version.id)
        .order_by(DocumentSection.section_order)
    )
    section_rows = sections_result.scalars().all()
    section_ids = [section.id for section in section_rows]
    fragments_by_section: dict[int, list[FragmentOut]] = defaultdict(list)
    if section_ids:
        fragments_result = await db.execute(
            select(TextFragment)
            .where(TextFragment.section_id.in_(section_ids))
            .order_by(TextFragment.section_id, TextFragment.fragment_order)
        )
        for fragment in fragments_result.scalars().all():
            fragments_by_section[fragment.section_id].append(FragmentOut.model_validate(fragment))

    sections = [
        SectionWithFragmentsOut(
            **SectionOut.model_validate(section).model_dump(),
            fragments=fragments_by_section.get(section.id, []),
        )
        for section in section_rows
    ]
    pipeline_outcome = await _get_latest_pipeline_outcome(
        db,
        version.id,
        prefer_success=bool(section_rows),
    )

    return NormalizedDocumentOut(
        document_id=document_id,
        version_id=version.id,
        sections=sections,
        pipeline_outcome=pipeline_outcome,
    )


@router.get("/{document_id}/fragments", response_model=FragmentListOut)
async def get_document_fragments(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    section_id: int | None = None,
):
    version = await _get_current_version(db, document_id)

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
    pipeline_outcome = await _get_latest_pipeline_outcome(db, version.id, prefer_success=bool(fragments))

    return FragmentListOut(
        document_id=document_id,
        version_id=version.id,
        fragments=fragments,
        total=len(fragments),
        pipeline_outcome=pipeline_outcome,
    )


@router.get(
    "/{document_id}/versions/{version_id}/evidence-state",
    response_model=VersionEvidenceStateOut,
    summary="Evidence density diagnostics for a specific document version",
)
async def get_version_evidence_state(
    document_id: int,
    version_id: int,
    include_fragments: bool = Query(True, description="Include per-fragment diagnostics"),
    max_fragments: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Return fragment-level evidence density state classification for a document version.

    Each fragment is classified as one of:
    - evidence_rows_present
    - healthy_empty_state
    - degraded_routing
    - extraction_missing
    - scoring_missing
    - no_mnn
    """
    # Verify document and version exist
    doc_result = await db.execute(
        select(DocumentRegistry).where(DocumentRegistry.id == document_id)
    )
    doc = doc_result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    ver_result = await db.execute(
        select(DocumentVersion).where(
            DocumentVersion.id == version_id,
            DocumentVersion.registry_id == document_id,
        )
    )
    ver = ver_result.scalar_one_or_none()
    if ver is None:
        raise HTTPException(status_code=404, detail="Version not found for this document")

    svc = EvidenceDiagnosticsService()
    return svc.diagnose_version(
        version_id=version_id,
        include_fragment_details=include_fragments,
        max_fragment_details=max_fragments,
    )


@router.get(
    "/corpus/evidence-coverage",
    response_model=CorpusCoverageOut,
    summary="Corpus-level evidence density across all current versions",
)
async def get_corpus_evidence_coverage(
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated evidence density across all current document versions.

    Useful for release evidence documents and operational health dashboards.
    """
    svc = EvidenceDiagnosticsService()
    return svc.corpus_coverage()
