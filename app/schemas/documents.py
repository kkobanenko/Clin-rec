from datetime import datetime

from pydantic import BaseModel


class PipelineOutcomeOut(BaseModel):
    stage: str
    status: str
    message: str
    reason_code: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentRegistryOut(BaseModel):
    id: int
    external_id: str | None = None
    title: str
    card_url: str | None = None
    html_url: str | None = None
    pdf_url: str | None = None
    specialty: str | None = None
    age_group: str | None = None
    status: str | None = None
    version_label: str | None = None
    publish_date: str | None = None
    update_date: str | None = None
    discovered_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class DocumentVersionOut(BaseModel):
    id: int
    registry_id: int
    version_hash: str | None = None
    source_type_primary: str | None = None
    source_type_available: str | None = None
    detected_at: datetime
    is_current: bool

    model_config = {"from_attributes": True}


class SourceArtifactOut(BaseModel):
    id: int
    document_version_id: int
    artifact_type: str
    raw_path: str
    content_hash: str
    content_type: str | None = None
    fetched_at: datetime

    model_config = {"from_attributes": True}


class SourceArtifactAccessOut(SourceArtifactOut):
    download_url: str
    preview_url: str


class DocumentDetailOut(BaseModel):
    registry: DocumentRegistryOut
    versions: list[DocumentVersionOut] = []
    artifacts: list[SourceArtifactOut] = []


class SectionOut(BaseModel):
    id: int
    section_path: str | None = None
    section_title: str | None = None
    section_order: int

    model_config = {"from_attributes": True}


class FragmentOut(BaseModel):
    id: int
    section_id: int
    fragment_order: int
    fragment_type: str
    fragment_text: str
    stable_id: str | None = None

    model_config = {"from_attributes": True}


class NormalizedDocumentOut(BaseModel):
    document_id: int
    version_id: int
    sections: list[SectionOut] = []
    pipeline_outcome: PipelineOutcomeOut | None = None


class FragmentListOut(BaseModel):
    document_id: int
    version_id: int
    fragments: list[FragmentOut] = []
    total: int
    pipeline_outcome: PipelineOutcomeOut | None = None


class DocumentArtifactListOut(BaseModel):
    document_id: int
    version_id: int
    artifacts: list[SourceArtifactAccessOut] = []
    total: int


class ArtifactCoverageDocumentOut(BaseModel):
    document_id: int
    current_version_id: int | None = None
    artifact_count: int = 0
    artifact_types: list[str] = []
    downloadable: bool = False
    problems: list[str] = []


class ArtifactCoverageOut(BaseModel):
    total_documents: int
    documents_with_current_version: int
    documents_without_current_version: int
    current_versions_with_artifacts: int
    current_versions_without_artifacts: int
    artifacts_total: int
    artifacts_downloadable: int
    artifacts_failed_validation: int
    documents: list[ArtifactCoverageDocumentOut] = []
