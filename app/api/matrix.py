import csv
import io

from celery import chain
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.evidence import MatrixCell, PairContextScore, PairEvidence
from app.models.molecule import Molecule
from app.models.scoring import ScoringModelVersion
from app.schemas.clinical import PairEvidenceOut
from app.schemas.matrix import (
    MatrixCellDetailOut,
    MatrixCellOut,
    MatrixRebuildBody,
    MatrixRebuildQueued,
    ScoringModelVersionCreate,
    ScoringModelVersionOut,
)
from app.workers.tasks.score import build_matrix, score_pairs
from app.schemas.pipeline import PaginatedResponse

router = APIRouter(prefix="/matrix", tags=["matrix"])


@router.get("", response_model=PaginatedResponse)
async def list_matrix_cells(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    scope_type: str | None = None,
    scope_id: str | None = None,
    model_version_id: int | None = None,
    molecule_from_id: int | None = None,
):
    query = select(MatrixCell)
    count_query = select(func.count(MatrixCell.id))

    if scope_type:
        query = query.where(MatrixCell.scope_type == scope_type)
        count_query = count_query.where(MatrixCell.scope_type == scope_type)
    if scope_id:
        query = query.where(MatrixCell.scope_id == scope_id)
        count_query = count_query.where(MatrixCell.scope_id == scope_id)
    if model_version_id:
        query = query.where(MatrixCell.model_version_id == model_version_id)
        count_query = count_query.where(MatrixCell.model_version_id == model_version_id)
    if molecule_from_id:
        query = query.where(MatrixCell.molecule_from_id == molecule_from_id)
        count_query = count_query.where(MatrixCell.molecule_from_id == molecule_from_id)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(MatrixCell.substitution_score.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [MatrixCellOut.model_validate(c) for c in result.scalars().all()]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if page_size else 1,
    )


@router.get("/cell", response_model=MatrixCellDetailOut)
async def get_matrix_cell(
    molecule_from_id: int,
    molecule_to_id: int,
    db: AsyncSession = Depends(get_db),
    model_version_id: int | None = None,
    scope_type: str = "global",
):
    query = select(MatrixCell).where(
        MatrixCell.molecule_from_id == molecule_from_id,
        MatrixCell.molecule_to_id == molecule_to_id,
        MatrixCell.scope_type == scope_type,
    )
    if model_version_id:
        query = query.where(MatrixCell.model_version_id == model_version_id)
    query = query.order_by(MatrixCell.created_at.desc()).limit(1)
    cell = (await db.execute(query)).scalar_one()

    mol_from = (await db.execute(select(Molecule).where(Molecule.id == molecule_from_id))).scalar_one()
    mol_to = (await db.execute(select(Molecule).where(Molecule.id == molecule_to_id))).scalar_one()

    evidence_result = await db.execute(
        select(PairEvidence).where(
            PairEvidence.molecule_from_id == molecule_from_id,
            PairEvidence.molecule_to_id == molecule_to_id,
        )
    )
    evidence = [PairEvidenceOut.model_validate(e) for e in evidence_result.scalars().all()]

    return MatrixCellDetailOut(
        cell=MatrixCellOut.model_validate(cell),
        molecule_from_inn=mol_from.inn_ru,
        molecule_to_inn=mol_to.inn_ru,
        evidence=evidence,
    )


@router.get("/export")
async def export_matrix(
    db: AsyncSession = Depends(get_db),
    model_version_id: int | None = None,
    scope_type: str = "global",
    format: str = Query("csv", pattern="^(csv|jsonl)$"),
):
    query = select(MatrixCell).where(MatrixCell.scope_type == scope_type)
    if model_version_id:
        query = query.where(MatrixCell.model_version_id == model_version_id)
    query = query.order_by(MatrixCell.molecule_from_id, MatrixCell.molecule_to_id)
    cells = (await db.execute(query)).scalars().all()

    mol_ids = {c.molecule_from_id for c in cells} | {c.molecule_to_id for c in cells}
    mols = {}
    if mol_ids:
        mol_result = await db.execute(select(Molecule).where(Molecule.id.in_(mol_ids)))
        mols = {m.id: m.inn_ru for m in mol_result.scalars().all()}

    version_ids = {c.model_version_id for c in cells}
    versions = {}
    if version_ids:
        ver_result = await db.execute(select(ScoringModelVersion).where(ScoringModelVersion.id.in_(version_ids)))
        versions = {v.id: v.version_label for v in ver_result.scalars().all()}

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["from_inn", "to_inn", "scope_type", "scope_id", "model_version", "substitution_score", "confidence_score"])
        for c in cells:
            writer.writerow([
                mols.get(c.molecule_from_id, ""),
                mols.get(c.molecule_to_id, ""),
                c.scope_type,
                c.scope_id or "",
                versions.get(c.model_version_id, ""),
                c.substitution_score,
                c.confidence_score,
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=matrix_export.csv"},
        )

    # JSONL
    import json

    lines = []
    for c in cells:
        lines.append(json.dumps({
            "from_inn": mols.get(c.molecule_from_id, ""),
            "to_inn": mols.get(c.molecule_to_id, ""),
            "scope_type": c.scope_type,
            "scope_id": c.scope_id,
            "model_version": versions.get(c.model_version_id, ""),
            "substitution_score": c.substitution_score,
            "confidence_score": c.confidence_score,
        }, ensure_ascii=False))
    content = "\n".join(lines)
    return StreamingResponse(
        iter([content]),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=matrix_export.jsonl"},
    )


@router.post("/rebuild", response_model=MatrixRebuildQueued, status_code=202)
async def queue_matrix_rebuild(body: MatrixRebuildBody):
    """
    Ставит в Celery цепочку: score_pairs(model_version_id) → build_matrix(model_version_id, scope_type).
    Нужна активная модель и наличие PairEvidence (после extract). См. RUNBOOK_RUNTIME_PROFILE.md.
    """
    async_result = chain(
        score_pairs.s(body.model_version_id),
        build_matrix.si(body.model_version_id, body.scope_type),
    ).apply_async()
    return MatrixRebuildQueued(
        task_id=async_result.id,
        message="score_pairs then build_matrix queued on score queue",
    )


@router.get("/models", response_model=list[ScoringModelVersionOut])
async def list_scoring_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScoringModelVersion).order_by(ScoringModelVersion.created_at.desc()))
    return [ScoringModelVersionOut.model_validate(m) for m in result.scalars().all()]


@router.post("/models", response_model=ScoringModelVersionOut)
async def create_scoring_model(data: ScoringModelVersionCreate, db: AsyncSession = Depends(get_db)):
    model = ScoringModelVersion(**data.model_dump())
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return ScoringModelVersionOut.model_validate(model)
