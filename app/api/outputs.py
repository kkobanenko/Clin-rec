"""API аналитических outputs и output filing (TZ §17)."""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.knowledge import OutputRelease
from app.schemas.knowledge import (
    OutputFileBackBody,
    OutputFileRequest,
    OutputGenerateRequest,
    OutputReleaseOut,
)
from app.schemas.pipeline import PaginatedResponse
from app.workers.tasks.kb import file_outputs as file_outputs_task
from app.workers.tasks.kb import generate_outputs as generate_outputs_task

router = APIRouter(prefix="/outputs", tags=["outputs"])


@router.post("/generate", status_code=202)
async def generate_output(body: OutputGenerateRequest):
    """Постановка в очередь: worker создаёт строку output_release (черновик)."""
    async_result = generate_outputs_task.delay(
        output_type=body.output_type,
        title=body.title,
        scope_json=body.scope_json,
    )
    return {
        "task_id": async_result.id,
        "status": "queued",
        "output_type": body.output_type,
        "message": "generate_outputs queued — по готовности см. GET /outputs",
    }


@router.post("/file", status_code=202)
async def file_output(body: OutputFileRequest):
    """Output filing workflow: обновление статуса (обработка в worker)."""
    async_result = file_outputs_task.delay(body.output_id, body.file_back_status)
    return {"task_id": async_result.id, "status": "queued", "output_id": body.output_id}


@router.post("/memo", status_code=202)
async def generate_memo_alias(body: OutputGenerateRequest):
    """TZ §17: алиас POST /outputs/generate с output_type=memo."""
    async_result = generate_outputs_task.delay(
        output_type="memo",
        title=body.title,
        scope_json=body.scope_json,
    )
    return {
        "task_id": async_result.id,
        "status": "queued",
        "output_type": "memo",
        "message": "memo generation queued — см. GET /outputs",
    }


@router.post("/file-back/{output_id}", status_code=202)
async def file_back_alias(output_id: int, body: OutputFileBackBody):
    """TZ §17: алиас к POST /outputs/file с output_id в пути."""
    async_result = file_outputs_task.delay(output_id, body.file_back_status)
    return {"task_id": async_result.id, "status": "queued", "output_id": output_id}


@router.get("", response_model=PaginatedResponse)
async def list_outputs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    output_type: str | None = None,
    file_back_status: str | None = None,
    review_status: str | None = None,
    generator_version: str | None = None,
    released_only: bool = False,
    has_file_pointer: bool = False,
    artifact_id: int | None = None,
    search: str | None = Query(None, description="Подстрока в title или file_pointer (ILIKE)"),
):
    q = select(OutputRelease)
    count_q = select(func.count(OutputRelease.id))
    if output_type:
        q = q.where(OutputRelease.output_type == output_type)
        count_q = count_q.where(OutputRelease.output_type == output_type)
    if file_back_status:
        q = q.where(OutputRelease.file_back_status == file_back_status)
        count_q = count_q.where(OutputRelease.file_back_status == file_back_status)
    if review_status:
        q = q.where(OutputRelease.review_status == review_status)
        count_q = count_q.where(OutputRelease.review_status == review_status)
    if generator_version:
        q = q.where(OutputRelease.generator_version == generator_version)
        count_q = count_q.where(OutputRelease.generator_version == generator_version)
    if released_only:
        q = q.where(OutputRelease.released_at.is_not(None))
        count_q = count_q.where(OutputRelease.released_at.is_not(None))
    if has_file_pointer:
        q = q.where(OutputRelease.file_pointer.is_not(None))
        count_q = count_q.where(OutputRelease.file_pointer.is_not(None))
    if artifact_id is not None:
        q = q.where(OutputRelease.artifact_id == artifact_id)
        count_q = count_q.where(OutputRelease.artifact_id == artifact_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filt = or_(
            OutputRelease.title.ilike(term),
            OutputRelease.file_pointer.ilike(term),
            cast(OutputRelease.scope_json, Text).ilike(term),
        )
        q = q.where(filt)
        count_q = count_q.where(filt)
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(OutputRelease.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = [OutputReleaseOut.model_validate(r) for r in rows]
    pages = (total + page_size - 1) // page_size if page_size else 1
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{output_id}", response_model=OutputReleaseOut)
async def get_output(output_id: int, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(OutputRelease).where(OutputRelease.id == output_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Output not found")
    return OutputReleaseOut.model_validate(row)
