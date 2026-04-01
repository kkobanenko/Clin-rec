from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PairEvidence(Base):
    __tablename__ = "pair_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    context_id: Mapped[int] = mapped_column(ForeignKey("clinical_context.id"), nullable=False, index=True)
    molecule_from_id: Mapped[int] = mapped_column(ForeignKey("molecule.id"), nullable=False, index=True)
    molecule_to_id: Mapped[int] = mapped_column(ForeignKey("molecule.id"), nullable=False, index=True)
    fragment_id: Mapped[int] = mapped_column(ForeignKey("text_fragment.id"), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    uur: Mapped[str | None] = mapped_column(String(8))
    udd: Mapped[str | None] = mapped_column(String(8))

    # Component scores
    role_score: Mapped[float | None] = mapped_column(Float)
    text_score: Mapped[float | None] = mapped_column(Float)
    population_score: Mapped[float | None] = mapped_column(Float)
    parity_score: Mapped[float | None] = mapped_column(Float)
    practical_score: Mapped[float | None] = mapped_column(Float)
    penalty: Mapped[float | None] = mapped_column(Float)
    final_fragment_score: Mapped[float | None] = mapped_column(Float)

    review_status: Mapped[str] = mapped_column(String(32), default="auto")
    extractor_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PairContextScore(Base):
    __tablename__ = "pair_context_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("scoring_model_version.id"), nullable=False, index=True)
    context_id: Mapped[int] = mapped_column(ForeignKey("clinical_context.id"), nullable=False, index=True)
    molecule_from_id: Mapped[int] = mapped_column(ForeignKey("molecule.id"), nullable=False)
    molecule_to_id: Mapped[int] = mapped_column(ForeignKey("molecule.id"), nullable=False)
    substitution_score: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    explanation_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MatrixCell(Base):
    __tablename__ = "matrix_cell"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("scoring_model_version.id"), nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(32), default="global")
    scope_id: Mapped[str | None] = mapped_column(String(256))
    molecule_from_id: Mapped[int] = mapped_column(ForeignKey("molecule.id"), nullable=False, index=True)
    molecule_to_id: Mapped[int] = mapped_column(ForeignKey("molecule.id"), nullable=False, index=True)
    substitution_score: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    contexts_count: Mapped[int] = mapped_column(Integer, default=0)
    supporting_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    explanation_short: Mapped[str | None] = mapped_column(Text)
    explanation_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
