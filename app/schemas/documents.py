from datetime import datetime

from pydantic import BaseModel, computed_field

from app.core.config import settings


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

    @computed_field
    @property
    def storage_uri(self) -> str:
        """URI объекта в bucket MinIO/S3 (см. CRIN_S3_BUCKET, CRIN_S3_ENDPOINT_URL)."""
        return f"s3://{settings.s3_bucket}/{self.raw_path}"

    model_config = {"from_attributes": True}


class DocumentDetailOut(BaseModel):
    registry: DocumentRegistryOut
    versions: list[DocumentVersionOut] = []
    artifacts: list[SourceArtifactOut] = []
    # Пояснение для операторов: внешний сайт — SPA; первичный текст у нас после fetch.
    external_source_note: str = (
        "Ссылки card_url/html_url/pdf_url ведут на официальный рубрикатор (одностраничное SPA): "
        "в браузере контент подгружается JavaScript-ом. Скачанные копии документов хранятся в "
        "объектном хранилище; см. storage_uri у каждого source_artifact и нормализованный текст в API /content."
    )


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


class FragmentListOut(BaseModel):
    document_id: int
    version_id: int
    fragments: list[FragmentOut] = []
    total: int
