"""Схемы API для compiled KB и output_release."""

from datetime import datetime

from pydantic import BaseModel, Field


class ArtifactSourceLinkOut(BaseModel):
    id: int
    source_kind: str
    source_id: int
    support_type: str
    notes: str | None = None

    model_config = {"from_attributes": True}


class KnowledgeClaimOut(BaseModel):
    id: int
    artifact_id: int
    claim_type: str
    claim_text: str
    confidence: str | None = None
    review_status: str | None = None
    conflict_group_id: int | None = None
    is_conflicted: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeArtifactOut(BaseModel):
    id: int
    artifact_type: str
    title: str
    canonical_slug: str
    status: str
    summary: str | None = None
    confidence: str | None = None
    review_status: str | None = None
    generator_version: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeArtifactDetailOut(KnowledgeArtifactOut):
    content_md: str | None = None
    manifest_json: dict | None = None
    storage_path: str | None = None
    source_links: list[ArtifactSourceLinkOut] = Field(default_factory=list)
    claims: list[KnowledgeClaimOut] = Field(default_factory=list)


class EntityRegistryOut(BaseModel):
    id: int
    entity_type: str
    canonical_name: str
    aliases_json: dict | None = None
    external_refs_json: dict | None = None
    status: str | None = None

    model_config = {"from_attributes": True}


class ConflictGroupOut(BaseModel):
    conflict_group_id: int
    claim_ids: list[int]


class KbTaskQueued(BaseModel):
    task_id: str
    status: str = "queued"
    message: str = "Task submitted to Celery"


class OutputGenerateRequest(BaseModel):
    output_type: str = "memo"
    title: str | None = None
    prompt: str | None = None
    scope_json: dict | None = None


class OutputFileRequest(BaseModel):
    output_id: int
    file_back_status: str  # accepted | rejected | needs_review


class OutputReleaseOut(BaseModel):
    id: int
    output_type: str
    title: str
    artifact_id: int | None = None
    file_pointer: str | None = None
    scope_json: dict | None = None
    generator_version: str | None = None
    review_status: str | None = None
    released_at: datetime | None = None
    file_back_status: str | None = None

    model_config = {"from_attributes": True}
