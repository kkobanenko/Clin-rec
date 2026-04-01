from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Molecule(Base):
    __tablename__ = "molecule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inn_ru: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    inn_en: Mapped[str | None] = mapped_column(Text)
    atc_code: Mapped[str | None] = mapped_column(String(16))

    synonyms: Mapped[list["MoleculeSynonym"]] = relationship(back_populates="molecule", cascade="all, delete-orphan")


class MoleculeSynonym(Base):
    __tablename__ = "molecule_synonym"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    molecule_id: Mapped[int] = mapped_column(ForeignKey("molecule.id", ondelete="CASCADE"), nullable=False, index=True)
    synonym_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="manual")

    molecule: Mapped["Molecule"] = relationship(back_populates="synonyms")
