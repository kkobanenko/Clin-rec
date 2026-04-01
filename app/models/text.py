from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentSection(Base):
    __tablename__ = "document_section"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_version_id: Mapped[int] = mapped_column(ForeignKey("document_version.id", ondelete="CASCADE"), nullable=False, index=True)
    section_path: Mapped[str | None] = mapped_column(String(512))
    section_title: Mapped[str | None] = mapped_column(Text)
    section_order: Mapped[int] = mapped_column(Integer, default=0)
    normalizer_version: Mapped[str | None] = mapped_column(String(64))

    document_version = relationship("DocumentVersion", back_populates="sections")
    fragments: Mapped[list["TextFragment"]] = relationship(back_populates="section", cascade="all, delete-orphan")


class TextFragment(Base):
    __tablename__ = "text_fragment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("document_section.id", ondelete="CASCADE"), nullable=False, index=True)
    fragment_order: Mapped[int] = mapped_column(Integer, default=0)
    fragment_type: Mapped[str] = mapped_column(String(32), default="paragraph")
    fragment_text: Mapped[str] = mapped_column(Text, nullable=False)
    stable_id: Mapped[str | None] = mapped_column(String(128), unique=True)

    section: Mapped["DocumentSection"] = relationship(back_populates="fragments")
