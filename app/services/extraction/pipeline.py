"""Extraction pipeline — orchestrates all extractors for a normalized document."""

import logging

from app.core.sync_database import get_sync_session
from app.models.clinical import ClinicalContext
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.text import DocumentSection, TextFragment
from app.services.knowledge_entity_sync import ensure_molecule_entities
from app.services.extraction.context_extractor import ContextExtractor
from app.services.extraction.mnn_extractor import MnnExtractor
from app.services.extraction.relation_extractor import RelationExtractor
from app.services.extraction.uur_udd_extractor import UurUddExtractor

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    def __init__(self):
        self.mnn_extractor = MnnExtractor()
        self.context_extractor = ContextExtractor()
        self.uur_udd_extractor = UurUddExtractor()
        self.relation_extractor = RelationExtractor()

    def extract(self, version_id: int) -> None:
        session = get_sync_session()
        try:
            version = session.get(DocumentVersion, version_id)
            if not version:
                logger.error("DocumentVersion %d not found", version_id)
                return

            doc = session.get(DocumentRegistry, version.registry_id)
            if not doc:
                logger.error("DocumentRegistry %d not found", version.registry_id)
                return

            # Load MNN dictionary
            self.mnn_extractor.load_dictionary()

            # Get all sections and fragments
            sections = (
                session.query(DocumentSection)
                .filter_by(document_version_id=version_id)
                .order_by(DocumentSection.section_order)
                .all()
            )

            section_data = []
            all_mnn_results = []
            all_uur_udd_results = []
            all_relation_results = []

            for section in sections:
                fragments = (
                    session.query(TextFragment)
                    .filter_by(section_id=section.id)
                    .order_by(TextFragment.fragment_order)
                    .all()
                )

                frag_data = []
                for frag in fragments:
                    # MNN extraction
                    mnn_hits = self.mnn_extractor.extract(frag.fragment_text)
                    for hit in mnn_hits:
                        hit["fragment_id"] = frag.id
                    all_mnn_results.extend(mnn_hits)

                    # UUR/UDD extraction
                    uur_udd_hits = self.uur_udd_extractor.extract(frag.fragment_text)
                    for hit in uur_udd_hits:
                        hit["fragment_id"] = frag.id
                    all_uur_udd_results.extend(uur_udd_hits)

                    # Relation signal extraction
                    relation_hits = self.relation_extractor.extract(frag.fragment_text)
                    for hit in relation_hits:
                        hit["fragment_id"] = frag.id
                    all_relation_results.extend(relation_hits)

                    frag_data.append({"text": frag.fragment_text, "id": frag.id})

                section_data.append({
                    "title": section.section_title or "",
                    "fragments": frag_data,
                })

            # Извлечённые МНН → entity_registry (канонические сущности для KB/scoring).
            mol_ids = {h["molecule_id"] for h in all_mnn_results if h.get("molecule_id") is not None}
            ensure_molecule_entities(session, mol_ids)

            # Extract clinical contexts
            contexts = self.context_extractor.extract_from_document(
                title=doc.title,
                sections=section_data,
            )

            # Persist contexts
            for ctx in contexts:
                existing = (
                    session.query(ClinicalContext)
                    .filter_by(context_signature=ctx["context_signature"])
                    .first()
                )
                if not existing:
                    db_ctx = ClinicalContext(
                        disease_name=ctx["disease_name"],
                        line_of_therapy=ctx.get("line_of_therapy"),
                        treatment_goal=ctx.get("treatment_goal"),
                        population_json=ctx.get("population_json"),
                        context_signature=ctx["context_signature"],
                        document_version_id=version_id,
                    )
                    session.add(db_ctx)

            session.commit()

            logger.info(
                "Extraction for version %d: %d MNN hits, %d UUR/UDD hits, %d relation signals, %d contexts",
                version_id,
                len(all_mnn_results),
                len(all_uur_udd_results),
                len(all_relation_results),
                len(contexts),
            )

            # Store extraction results as JSON metadata on the pipeline run
            stats = {
                "mnn_count": len(all_mnn_results),
                "uur_udd_count": len(all_uur_udd_results),
                "relation_count": len(all_relation_results),
                "context_count": len(contexts),
                "mnn_molecules": list({h["molecule_id"] for h in all_mnn_results}),
            }
            logger.info("Extraction stats for version %d: %s", version_id, stats)

        finally:
            session.close()
