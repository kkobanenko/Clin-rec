from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClinicalContext(Base):
    __tablename__ = "clinical_context"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    disease_name: Mapped[str] = mapped_column(Text, nullable=False)
    line_of_therapy: Mapped[str | None] = mapped_column(String(128))
    treatment_goal: Mapped[str | None] = mapped_column(Text)
    population_json: Mapped[dict | None] = mapped_column(JSONB)
    context_signature: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)

    document_version_id: Mapped[int | None] = mapped_column(Integer, index=True)
    fragment_id: Mapped[int | None] = mapped_column(Integer, index=True)
