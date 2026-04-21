from datetime import datetime

from pydantic import BaseModel


class SyncRequest(BaseModel):
    pass


class SyncResponse(BaseModel):
    run_id: int
    status: str
    message: str


class PipelineRunOut(BaseModel):
    id: int
    stage: str
    run_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    discovered_count: int
    fetched_count: int
    parsed_count: int
    failed_count: int
    stats_json: dict | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class ReviewActionCreate(BaseModel):
    target_type: str
    target_id: int
    action: str
    new_value_json: dict | None = None
    reason: str | None = None
    author: str


class ReviewActionOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    action: str
    old_value_json: dict | None = None
    new_value_json: dict | None = None
    reason: str | None = None
    author: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewStatsOut(BaseModel):
    counts: dict[str, int]
    total: int


class ReviewHistoryQueryOut(BaseModel):
    target_type: str | None = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
