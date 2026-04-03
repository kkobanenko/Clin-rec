"""Read-only статус Celery task по id (для UI polling)."""

from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel

from app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusOut(BaseModel):
    task_id: str
    state: str
    ready: bool


@router.get("/{task_id}", response_model=TaskStatusOut)
async def get_task_status(task_id: str):
    """Состояние задачи: PENDING, STARTED, SUCCESS, FAILURE, … Без тела результата."""
    r = AsyncResult(task_id, app=celery_app)
    return TaskStatusOut(task_id=task_id, state=str(r.state), ready=r.ready())
