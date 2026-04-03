import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.evidence import PairEvidence
from app.models.pipeline import PipelineRun
from app.models.reviewer import ReviewAction
from app.schemas.pipeline import PaginatedResponse, PipelineRunOut, ReviewActionCreate, ReviewActionOut

logger = logging.getLogger(__name__)

# TZ §7.12: маппинг action → review_status для PairEvidence.
_ACTION_TO_STATUS = {
    "approve": "approved",
    "reject": "rejected",
    "override": "overridden",
}

router = APIRouter(tags=["pipeline"])


@router.get("/runs", response_model=PaginatedResponse)
async def list_runs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: str | None = None,
):
    query = select(PipelineRun)
    count_query = select(func.count(PipelineRun.id))
    if stage:
        query = query.where(PipelineRun.stage == stage)
        count_query = count_query.where(PipelineRun.stage == stage)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(PipelineRun.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [PipelineRunOut.model_validate(r) for r in result.scalars().all()]

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=(total + page_size - 1) // page_size if page_size else 1)


@router.get("/runs/{run_id}", response_model=PipelineRunOut)
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
    return PipelineRunOut.model_validate(result.scalar_one())


@router.post("/review", response_model=ReviewActionOut)
async def create_review_action(data: ReviewActionCreate, db: AsyncSession = Depends(get_db)):
    """
    Создание review action + обновление review_status на целевой записи.
    При target_type='pair_evidence' меняет PairEvidence.review_status (TZ §7.12).
    """
    old_value_json = data.new_value_json
    # Обновить статус PairEvidence, если действие касается evidence.
    if data.target_type == "pair_evidence":
        new_status = _ACTION_TO_STATUS.get(data.action)
        if new_status:
            pe_row = (
                await db.execute(select(PairEvidence).where(PairEvidence.id == data.target_id))
            ).scalar_one_or_none()
            if pe_row:
                old_value_json = {"review_status": pe_row.review_status}
                await db.execute(
                    update(PairEvidence)
                    .where(PairEvidence.id == data.target_id)
                    .values(review_status=new_status)
                )
                logger.info(
                    "PairEvidence %d review_status: %s -> %s (by %s)",
                    data.target_id, pe_row.review_status, new_status, data.author,
                )
    action = ReviewAction(
        target_type=data.target_type,
        target_id=data.target_id,
        action=data.action,
        old_value_json=old_value_json,
        new_value_json=data.new_value_json,
        reason=data.reason,
        author=data.author,
    )
    db.add(action)
    await db.flush()
    await db.refresh(action)
    return ReviewActionOut.model_validate(action)


@router.get("/reviews", response_model=list[ReviewActionOut])
async def list_reviews(
    db: AsyncSession = Depends(get_db),
    target_type: str | None = None,
    target_id: int | None = None,
):
    query = select(ReviewAction)
    if target_type:
        query = query.where(ReviewAction.target_type == target_type)
    if target_id:
        query = query.where(ReviewAction.target_id == target_id)
    query = query.order_by(ReviewAction.created_at.desc())
    result = await db.execute(query)
    return [ReviewActionOut.model_validate(r) for r in result.scalars().all()]
