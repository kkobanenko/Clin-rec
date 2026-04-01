from datetime import datetime

from pydantic import BaseModel


class MoleculeCreate(BaseModel):
    inn_ru: str
    inn_en: str | None = None
    atc_code: str | None = None


class MoleculeOut(BaseModel):
    id: int
    inn_ru: str
    inn_en: str | None = None
    atc_code: str | None = None

    model_config = {"from_attributes": True}


class MoleculeSynonymCreate(BaseModel):
    synonym_text: str
    source: str = "manual"


class MoleculeSynonymOut(BaseModel):
    id: int
    molecule_id: int
    synonym_text: str
    source: str

    model_config = {"from_attributes": True}


class ClinicalContextOut(BaseModel):
    id: int
    disease_name: str
    line_of_therapy: str | None = None
    treatment_goal: str | None = None
    population_json: dict | None = None
    context_signature: str

    model_config = {"from_attributes": True}


class PairEvidenceOut(BaseModel):
    id: int
    context_id: int
    molecule_from_id: int
    molecule_to_id: int
    fragment_id: int
    relation_type: str
    uur: str | None = None
    udd: str | None = None
    role_score: float | None = None
    text_score: float | None = None
    population_score: float | None = None
    parity_score: float | None = None
    practical_score: float | None = None
    penalty: float | None = None
    final_fragment_score: float | None = None
    review_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
