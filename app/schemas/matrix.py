from datetime import datetime

from pydantic import BaseModel, Field


class MatrixCellOut(BaseModel):
    id: int
    model_version_id: int
    scope_type: str
    scope_id: str | None = None
    molecule_from_id: int
    molecule_to_id: int
    substitution_score: float | None = None
    confidence_score: float | None = None
    contexts_count: int
    supporting_evidence_count: int
    explanation_short: str | None = None
    explanation_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MatrixCellDetailOut(BaseModel):
    cell: MatrixCellOut
    molecule_from_inn: str
    molecule_to_inn: str
    evidence: list = []


class MatrixExportRow(BaseModel):
    from_inn: str
    to_inn: str
    scope_type: str
    scope_id: str | None = None
    model_version: str
    substitution_score: float | None = None
    confidence_score: float | None = None


class PairContextScoreOut(BaseModel):
    id: int
    model_version_id: int
    context_id: int
    molecule_from_id: int
    molecule_to_id: int
    substitution_score: float | None = None
    confidence_score: float | None = None
    evidence_count: int
    explanation_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoringModelVersionOut(BaseModel):
    id: int
    version_label: str
    weights_json: dict
    code_commit_hash: str | None = None
    description: str | None = None
    is_active: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoringModelVersionCreate(BaseModel):
    version_label: str
    weights_json: dict
    code_commit_hash: str | None = None
    description: str | None = None


class MatrixRebuildBody(BaseModel):
    """POST /matrix/rebuild: очередь score_pairs → build_matrix."""

    model_version_id: int = Field(..., ge=1)
    scope_type: str = "global"


class MatrixRebuildQueued(BaseModel):
    task_id: str
    status: str = "queued"
    message: str
