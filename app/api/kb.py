"""HTTP API compiled knowledge base (TZ §17)."""

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db
from app.models.knowledge import EntityRegistry, KnowledgeArtifact, KnowledgeClaim
from app.schemas.knowledge import (
    ConflictGroupOut,
    EntityRegistryOut,
    KbTaskQueued,
    KnowledgeArtifactDetailOut,
    KnowledgeArtifactOut,
    KnowledgeClaimOut,
)
from app.schemas.pipeline import PaginatedResponse
from app.workers.tasks.kb import lint_kb as lint_kb_task
from app.workers.tasks.kb import run_compile_kb

router = APIRouter(prefix="/kb", tags=["knowledge_base"])


@router.get("/indexes/master")
async def master_index(db: AsyncSession = Depends(get_db)):
    """Корневой индекс KB: запись master_index или заглушка."""
    result = await db.execute(
        select(KnowledgeArtifact).where(KnowledgeArtifact.artifact_type == "master_index").limit(1)
    )
    row = result.scalar_one_or_none()
    if row:
        return {
            "format": "kb_master_index",
            "artifact_id": row.id,
            "canonical_slug": row.canonical_slug,
            "title": row.title,
            "manifest_json": row.manifest_json,
            "content_md": row.content_md,
        }
    return {
        "format": "kb_master_index",
        "artifact_id": None,
        "message": "No master_index artifact yet; run /kb/compile after loading corpus.",
        "sections": [],
    }


@router.get("/artifacts", response_model=PaginatedResponse)
async def list_artifacts(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    artifact_type: str | None = None,
    status: str | None = None,
    review_status: str | None = None,
    generator_version: str | None = None,
    search: str | None = Query(None, description="Подстрока в title, summary или canonical_slug (ILIKE)"),
):
    q = select(KnowledgeArtifact)
    count_q = select(func.count(KnowledgeArtifact.id))
    if artifact_type:
        q = q.where(KnowledgeArtifact.artifact_type == artifact_type)
        count_q = count_q.where(KnowledgeArtifact.artifact_type == artifact_type)
    if status:
        q = q.where(KnowledgeArtifact.status == status)
        count_q = count_q.where(KnowledgeArtifact.status == status)
    if review_status:
        q = q.where(KnowledgeArtifact.review_status == review_status)
        count_q = count_q.where(KnowledgeArtifact.review_status == review_status)
    if generator_version:
        q = q.where(KnowledgeArtifact.generator_version == generator_version)
        count_q = count_q.where(KnowledgeArtifact.generator_version == generator_version)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filt = or_(
            KnowledgeArtifact.title.ilike(term),
            KnowledgeArtifact.summary.ilike(term),
            KnowledgeArtifact.canonical_slug.ilike(term),
            KnowledgeArtifact.content_md.ilike(term),
        )
        q = q.where(filt)
        count_q = count_q.where(filt)
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(KnowledgeArtifact.id).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = [KnowledgeArtifactOut.model_validate(r) for r in rows]
    pages = (total + page_size - 1) // page_size if page_size else 1
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/artifacts/{artifact_id}", response_model=KnowledgeArtifactDetailOut)
async def get_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeArtifact)
        .options(selectinload(KnowledgeArtifact.source_links), selectinload(KnowledgeArtifact.claims))
        .where(KnowledgeArtifact.id == artifact_id)
    )
    art = result.scalar_one_or_none()
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return KnowledgeArtifactDetailOut.model_validate(art)


@router.get("/entities", response_model=PaginatedResponse)
async def list_entities(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity_type: str | None = None,
    status: str | None = None,
    search: str | None = Query(None, description="Подстрока в canonical_name (ILIKE)"),
):
    """Список сущностей entity_registry (в т.ч. molecule после extract)."""
    q = select(EntityRegistry)
    count_q = select(func.count(EntityRegistry.id))
    if entity_type:
        q = q.where(EntityRegistry.entity_type == entity_type)
        count_q = count_q.where(EntityRegistry.entity_type == entity_type)
    if status:
        q = q.where(EntityRegistry.status == status)
        count_q = count_q.where(EntityRegistry.status == status)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filt = or_(
            EntityRegistry.canonical_name.ilike(term),
            cast(EntityRegistry.aliases_json, Text).ilike(term),
            cast(EntityRegistry.external_refs_json, Text).ilike(term),
        )
        q = q.where(filt)
        count_q = count_q.where(filt)
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(EntityRegistry.id).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = [EntityRegistryOut.model_validate(r) for r in rows]
    pages = (total + page_size - 1) // page_size if page_size else 1
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/entities/{entity_id}", response_model=EntityRegistryOut)
async def get_entity(entity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EntityRegistry).where(EntityRegistry.id == entity_id))
    ent = result.scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
    return EntityRegistryOut.model_validate(ent)


@router.get("/claims", response_model=PaginatedResponse)
async def list_claims(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    artifact_id: int | None = None,
    claim_type: str | None = None,
    review_status: str | None = None,
    conflicted_only: bool = False,
    search: str | None = Query(None, description="Подстрока в claim_text (ILIKE)"),
):
    q = select(KnowledgeClaim)
    count_q = select(func.count(KnowledgeClaim.id))
    if artifact_id is not None:
        q = q.where(KnowledgeClaim.artifact_id == artifact_id)
        count_q = count_q.where(KnowledgeClaim.artifact_id == artifact_id)
    if claim_type:
        q = q.where(KnowledgeClaim.claim_type == claim_type)
        count_q = count_q.where(KnowledgeClaim.claim_type == claim_type)
    if review_status:
        q = q.where(KnowledgeClaim.review_status == review_status)
        count_q = count_q.where(KnowledgeClaim.review_status == review_status)
    if conflicted_only:
        q = q.where(KnowledgeClaim.is_conflicted.is_(True))
        count_q = count_q.where(KnowledgeClaim.is_conflicted.is_(True))
    if search and search.strip():
        term = f"%{search.strip()}%"
        filt = KnowledgeClaim.claim_text.ilike(term)
        q = q.where(filt)
        count_q = count_q.where(filt)
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(KnowledgeClaim.id).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = [KnowledgeClaimOut.model_validate(r) for r in rows]
    pages = (total + page_size - 1) // page_size if page_size else 1
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/conflicts", response_model=list[ConflictGroupOut])
async def list_conflicts(
    db: AsyncSession = Depends(get_db),
    artifact_id: int | None = None,
):
    result = await db.execute(
        select(KnowledgeClaim).where(
            KnowledgeClaim.conflict_group_id.isnot(None),
            *( [KnowledgeClaim.artifact_id == artifact_id] if artifact_id is not None else [] ),
        )
    )
    rows = result.scalars().all()
    by_group: dict[int, list[int]] = defaultdict(list)
    artifacts_by_group: dict[int, set[int]] = defaultdict(set)
    previews_by_group: dict[int, list[str]] = defaultdict(list)
    for c in rows:
        if c.conflict_group_id is not None:
            by_group[c.conflict_group_id].append(c.id)
            artifacts_by_group[c.conflict_group_id].add(c.artifact_id)
            if len(previews_by_group[c.conflict_group_id]) < 3:
                text = (c.claim_text or "").strip()
                if len(text) > 120:
                    text = f"{text[:117]}..."
                previews_by_group[c.conflict_group_id].append(text)
    return [
        ConflictGroupOut(
            conflict_group_id=gid,
            claim_ids=ids,
            artifact_ids=sorted(artifacts_by_group.get(gid, set())),
            claim_count=len(ids),
            claim_previews=previews_by_group.get(gid, []),
        )
        for gid, ids in sorted(by_group.items())
    ]


@router.post("/compile", response_model=KbTaskQueued, status_code=202)
async def compile_kb():
    async_result = run_compile_kb.delay()
    return KbTaskQueued(task_id=async_result.id, message="compile_kb queued")


@router.post("/lint", response_model=KbTaskQueued, status_code=202)
async def lint_kb():
    async_result = lint_kb_task.delay()
    return KbTaskQueued(task_id=async_result.id, message="lint_kb queued")
