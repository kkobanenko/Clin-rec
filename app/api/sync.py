from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.pipeline import PipelineRun
from app.schemas.pipeline import SyncResponse
from app.workers.tasks.discovery import run_full_sync, run_incremental_sync

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/full", response_model=SyncResponse, status_code=202)
async def full_sync(db: AsyncSession = Depends(get_db)):
    run = PipelineRun(stage="discovery", run_type="full", status="pending")
    db.add(run)
    await db.flush()
    run_id = run.id
    await db.commit()
    async_result = run_full_sync.delay(run_id)
    return SyncResponse(
        run_id=run_id,
        task_id=async_result.id,
        status="pending",
        message="Full sync queued",
    )


@router.post("/incremental", response_model=SyncResponse, status_code=202)
async def incremental_sync(db: AsyncSession = Depends(get_db)):
    run = PipelineRun(stage="discovery", run_type="incremental", status="pending")
    db.add(run)
    await db.flush()
    run_id = run.id
    await db.commit()
    async_result = run_incremental_sync.delay(run_id)
    return SyncResponse(
        run_id=run_id,
        task_id=async_result.id,
        status="pending",
        message="Incremental sync queued",
    )
