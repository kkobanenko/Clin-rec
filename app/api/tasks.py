"""Read-only статус Celery task по id (для UI polling)."""

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusOut(BaseModel):
    task_id: str
    state: str
    ready: bool
    error: str | None = None
    result: dict[str, Any] | None = None


@router.get("/{task_id}", response_model=TaskStatusOut)
async def get_task_status(
    task_id: str,
    include_result: bool = Query(
        False,
        description="Если true и задача SUCCESS — вернуть result (dict), если он сериализуем.",
    ),
):
    """Состояние задачи: PENDING, STARTED, SUCCESS, FAILURE, … При FAILURE — поле error."""
    r = AsyncResult(task_id, app=celery_app)
    out = TaskStatusOut(task_id=task_id, state=str(r.state), ready=r.ready())
    if r.ready():
        if r.failed():
            err = r.result
            out.error = str(err) if err is not None else "unknown failure"
        elif r.successful() and include_result and r.result is not None:
            if isinstance(r.result, dict):
                out.result = r.result
    return out
