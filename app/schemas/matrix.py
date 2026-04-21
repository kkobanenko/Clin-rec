from datetime import datetime

from pydantic import BaseModel


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


class ScoringModelReadinessOut(BaseModel):
    ready: bool
    has_matrix_cells: bool | None = None
    sufficient_evidence: bool | None = None
    low_confidence_acceptable: bool | None = None
    cell_count: int | None = None
    pcs_count: int | None = None
    low_confidence_ratio: float | None = None
    error: str | None = None


class ScoringModelActivateIn(BaseModel):
    author: str
    force: bool = False


class ScoringModelActivationOut(BaseModel):
    model_version_id: int
    version_label: str
    released_by: str
    forced: bool = False
    readiness: ScoringModelReadinessOut


class ScoringModelRefreshIn(BaseModel):
    scope_type: str = "global"
    scope_id: str | None = None


class ScoringModelRefreshOut(BaseModel):
    model_version_id: int
    scope_type: str
    scope_id: str | None = None
    pair_context_scores: int
    matrix_cells: int
