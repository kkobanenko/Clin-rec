"""Candidate engine — generates directed MNN pairs within clinical contexts."""

import logging
from itertools import permutations

from app.core.sync_database import get_sync_session
from app.models.clinical import ClinicalContext
from app.models.evidence import PairEvidence
from app.models.text import DocumentSection, TextFragment
from app.services.extraction.mnn_extractor import MnnExtractor
from app.services.extraction.relation_extractor import RelationExtractor
from app.services.extraction.uur_udd_extractor import UurUddExtractor

logger = logging.getLogger(__name__)


class CandidateEngine:
    def __init__(self):
        self.mnn_extractor = MnnExtractor()
        self.relation_extractor = RelationExtractor()
        self.uur_udd_extractor = UurUddExtractor()

    def generate_pairs(self, version_id: int) -> int:
        """Generate directed candidate pairs for a document version.

        Returns number of pair_evidence records created.
        """
        session = get_sync_session()
        try:
            self.mnn_extractor.load_dictionary()

            # Get contexts for this document version
            contexts = (
                session.query(ClinicalContext)
                .filter_by(document_version_id=version_id)
                .all()
            )
            if not contexts:
                logger.info("No contexts for version %d, skipping candidate generation", version_id)
                return 0

            # Get all sections and fragments
            sections = (
                session.query(DocumentSection)
                .filter_by(document_version_id=version_id)
                .order_by(DocumentSection.section_order)
                .all()
            )

            total_pairs = 0

            for context in contexts:
                for section in sections:
                    fragments = (
                        session.query(TextFragment)
                        .filter_by(section_id=section.id)
                        .order_by(TextFragment.fragment_order)
                        .all()
                    )

                    for frag in fragments:
                        # Find MNN mentions in this fragment
                        mnn_hits = self.mnn_extractor.extract(frag.fragment_text)
                        mol_ids = list({h["molecule_id"] for h in mnn_hits})

                        if len(mol_ids) < 2:
                            continue

                        # Extract relation signals
                        relation_signals = self.relation_extractor.extract(frag.fragment_text)
                        relation_type, relation_confidence = self.relation_extractor.classify_relation(relation_signals)

                        # Extract UUR/UDD
                        uur_udd = self.uur_udd_extractor.extract(frag.fragment_text)
                        uur = uur_udd[0]["uur"] if uur_udd else None
                        udd = uur_udd[0]["udd"] if uur_udd else None

                        # Generate directed pairs (all permutations)
                        for mol_from, mol_to in permutations(mol_ids, 2):
                            # Check for existing evidence
                            existing = (
                                session.query(PairEvidence)
                                .filter_by(
                                    context_id=context.id,
                                    molecule_from_id=mol_from,
                                    molecule_to_id=mol_to,
                                    fragment_id=frag.id,
                                )
                                .first()
                            )
                            if existing:
                                continue

                            evidence = PairEvidence(
                                context_id=context.id,
                                molecule_from_id=mol_from,
                                molecule_to_id=mol_to,
                                fragment_id=frag.id,
                                relation_type=relation_type,
                                uur=uur,
                                udd=udd,
                                review_status="auto",
                                extractor_version=f"candidate_v1.0",
                            )
                            session.add(evidence)
                            total_pairs += 1

                session.flush()

            session.commit()
            logger.info("Generated %d candidate pairs for version %d", total_pairs, version_id)
            return total_pairs

        finally:
            session.close()
