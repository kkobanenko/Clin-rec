from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentRegistry(Base):
    __tablename__ = "document_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(256), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    card_url: Mapped[str | None] = mapped_column(Text)
    html_url: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    specialty: Mapped[str | None] = mapped_column(String(512))
    age_group: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str | None] = mapped_column(String(128))
    version_label: Mapped[str | None] = mapped_column(String(256))
    publish_date: Mapped[str | None] = mapped_column(String(64))
    update_date: Mapped[str | None] = mapped_column(String(64))
    source_payload_json: Mapped[dict | None] = mapped_column(JSONB)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="registry", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_document_registry_specialty", "specialty"),
        Index("ix_document_registry_status", "status"),
    )


class DocumentVersion(Base):
    __tablename__ = "document_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registry_id: Mapped[int] = mapped_column(ForeignKey("document_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    version_hash: Mapped[str | None] = mapped_column(String(128))
    source_type_primary: Mapped[str | None] = mapped_column(String(32))
    source_type_available: Mapped[str | None] = mapped_column(String(128))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    registry: Mapped["DocumentRegistry"] = relationship(back_populates="versions")
    artifacts: Mapped[list["SourceArtifact"]] = relationship(back_populates="document_version", cascade="all, delete-orphan")
    sections: Mapped[list["DocumentSection"]] = relationship(back_populates="document_version", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_document_version_registry_current", "registry_id", "is_current"),
    )


class SourceArtifact(Base):
    __tablename__ = "source_artifact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_version_id: Mapped[int] = mapped_column(ForeignKey("document_version.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    headers_json: Mapped[dict | None] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document_version: Mapped["DocumentVersion"] = relationship(back_populates="artifacts")
