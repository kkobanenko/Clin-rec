"""Модели compiled knowledge base: артефакты, claims, связи с источниками (см. TZ §7)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeArtifact(Base):
    """Страница или запись в compiled KB (digest, entity page, …)."""

    __tablename__ = "knowledge_artifact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_slug: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    content_md: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(32))
    review_status: Mapped[str | None] = mapped_column(String(32))
    generator_version: Mapped[str | None] = mapped_column(String(64))
    storage_path: Mapped[str | None] = mapped_column(Text)
    manifest_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source_links: Mapped[list["ArtifactSourceLink"]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan"
    )
    claims: Mapped[list["KnowledgeClaim"]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_knowledge_artifact_type_status", "artifact_type", "status"),)


class ArtifactSourceLink(Base):
    """Provenance: связь артефакта с объектами source vault / corpus."""

    __tablename__ = "artifact_source_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    support_type: Mapped[str] = mapped_column(String(32), nullable=False, default="primary")
    notes: Mapped[str | None] = mapped_column(Text)

    artifact: Mapped["KnowledgeArtifact"] = relationship(back_populates="source_links")


class KnowledgeClaim(Base):
    """Атомарное утверждение с типом fact / inference / hypothesis."""

    __tablename__ = "knowledge_claim"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claim_type: Mapped[str] = mapped_column(String(32), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(32))
    review_status: Mapped[str | None] = mapped_column(String(32))
    conflict_group_id: Mapped[int | None] = mapped_column(Integer, index=True)
    is_conflicted: Mapped[bool] = mapped_column(Boolean, default=False)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    artifact: Mapped["KnowledgeArtifact"] = relationship(back_populates="claims")


class EntityRegistry(Base):
    """Канонические сущности для страниц и ссылок."""

    __tablename__ = "entity_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    aliases_json: Mapped[dict | None] = mapped_column(JSONB)
    external_refs_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str | None] = mapped_column(String(32))

    __table_args__ = (Index("ix_entity_registry_type_name", "entity_type", "canonical_name"),)


class ArtifactBacklink(Base):
    """Граф ссылок между артефактами KB."""

    __tablename__ = "artifact_backlink"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_artifact_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_artifact_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False, index=True
    )
    link_type: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (
        Index("ix_artifact_backlink_from_to", "from_artifact_id", "to_artifact_id"),
    )


class OutputRelease(Base):
    """Зафиксированный аналитический output (memo, slides, matrix snapshot, …)."""

    __tablename__ = "output_release"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    output_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_artifact.id", ondelete="SET NULL"), index=True
    )
    file_pointer: Mapped[str | None] = mapped_column(Text)
    scope_json: Mapped[dict | None] = mapped_column(JSONB)
    generator_version: Mapped[str | None] = mapped_column(String(64))
    review_status: Mapped[str | None] = mapped_column(String(32))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_back_status: Mapped[str | None] = mapped_column(String(32))
