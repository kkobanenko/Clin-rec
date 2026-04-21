from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.evidence import PairEvidence
from app.models.pipeline import PipelineRun
from app.models.reviewer import ReviewAction
from app.schemas.clinical import PairEvidenceOut
from app.schemas.pipeline import (
    BulkReviewApproveIn,
    BulkReviewApproveOut,
    PaginatedResponse,
    PipelineRunOut,
    ReviewActionCreate,
    ReviewActionOut,
    ReviewStatsOut,
)
from app.services.reviewer import ReviewerService

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
    del db
    if data.target_type != "pair_evidence":
        raise HTTPException(status_code=400, detail="Only pair_evidence review actions are supported")

    service = ReviewerService()
    action: ReviewAction | None
    if data.action == "approve":
        action = service.approve(data.target_id, author=data.author, reason=data.reason)
    elif data.action == "reject":
        if not data.reason:
            raise HTTPException(status_code=400, detail="Reject action requires reason")
        action = service.reject(data.target_id, author=data.author, reason=data.reason)
    elif data.action == "override":
        new_score = None
        if data.new_value_json:
            new_score = data.new_value_json.get("final_fragment_score")
        if new_score is None:
            raise HTTPException(status_code=400, detail="Override action requires new_value_json.final_fragment_score")
        action = service.override_score(data.target_id, author=data.author, new_score=float(new_score), reason=data.reason or "manual override")
    else:
        raise HTTPException(status_code=400, detail="Unsupported review action")

    if action is None:
        raise HTTPException(status_code=404, detail="Evidence record not found")
    return ReviewActionOut.model_validate(action)


@router.get("/review/queue", response_model=PaginatedResponse)
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    status: str = Query("auto"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total = (
        await db.execute(
            select(func.count(PairEvidence.id)).where(PairEvidence.review_status == status)
        )
    ).scalar_one()
    items = ReviewerService().get_review_queue(status=status, limit=page_size, offset=(page - 1) * page_size)
    return PaginatedResponse(
        items=[PairEvidenceOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if page_size else 1,
    )


@router.get("/review/stats", response_model=ReviewStatsOut)
async def get_review_stats():
    counts = ReviewerService().get_review_stats()
    return ReviewStatsOut(counts=counts, total=sum(counts.values()))


@router.post("/review/bulk-approve", response_model=BulkReviewApproveOut)
async def bulk_approve_reviews(data: BulkReviewApproveIn):
    approved_count = ReviewerService().bulk_approve(data.evidence_ids, author=data.author)
    return BulkReviewApproveOut(approved_count=approved_count)


@router.get("/review/history", response_model=PaginatedResponse)
async def get_review_history(
    db: AsyncSession = Depends(get_db),
    target_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    count_query = select(func.count(ReviewAction.id))
    if target_type:
        count_query = count_query.where(ReviewAction.target_type == target_type)
    total = (await db.execute(count_query)).scalar_one()
    items = ReviewerService().get_review_history(
        target_type=target_type,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return PaginatedResponse(
        items=[ReviewActionOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if page_size else 1,
    )


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
