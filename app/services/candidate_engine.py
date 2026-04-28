"""Candidate engine — generates directed MNN pairs within clinical contexts."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from itertools import permutations
from typing import Optional

from app.core.sync_database import get_sync_session
from app.models.clinical import ClinicalContext
from app.models.evidence import PairEvidence
from app.models.text import DocumentSection, TextFragment
from app.services.extraction.mnn_extractor import MnnExtractor
from app.services.extraction.relation_extractor import RelationExtractor
from app.services.extraction.uur_udd_extractor import UurUddExtractor

logger = logging.getLogger(__name__)


class FragmentSkipReason(str, Enum):
    """Why a fragment did not contribute any candidate pairs."""

    NO_CONTEXT = "no_context"                # No ClinicalContext rows for this version
    SINGLE_MNN = "single_mnn"                # Only 0-1 MNN hits — cannot form a directed pair
    NO_MNN = "no_mnn"                        # No MNN hits at all
    ALL_PAIRS_EXIST = "all_pairs_exist"      # Every permutation already had a PairEvidence row
    IMAGE_FRAGMENT = "image_fragment"        # Fragment is image — skipped intentionally
    PRODUCED_PAIRS = "produced_pairs"        # Fragment DID yield at least one new pair (not a skip)


@dataclass
class FragmentCandidateDiagnostic:
    """Per-fragment outcome from candidate pair generation."""

    fragment_id: int
    fragment_text_prefix: str                # First 60 chars for log readability
    content_kind: str
    mnn_hits: int
    new_pairs: int
    skipped_pairs: int                       # Pairs skipped because they already existed
    skip_reason: Optional[FragmentSkipReason] = None
    context_id: Optional[int] = None        # Which context this fragment was processed under


@dataclass
class CandidateDiagnosticResult:
    """Aggregate diagnostics for a ``generate_pairs_with_diagnostics`` call."""

    version_id: int
    total_new_pairs: int = 0
    total_skipped_pairs: int = 0
    fragments_with_pairs: int = 0
    fragments_single_mnn: int = 0
    fragments_no_mnn: int = 0
    fragments_image: int = 0
    fragments_all_exist: int = 0
    fragment_diagnostics: list[FragmentCandidateDiagnostic] = field(default_factory=list)

    # ---- computed helpers ----
    @property
    def total_fragments_processed(self) -> int:
        return len(self.fragment_diagnostics)

    @property
    def skip_rate(self) -> float:
        """Fraction of fragments that did NOT yield any new pair (0–1)."""
        total = self.total_fragments_processed
        if total == 0:
            return 0.0
        productive = self.fragments_with_pairs
        return (total - productive) / total

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "total_new_pairs": self.total_new_pairs,
            "total_skipped_pairs": self.total_skipped_pairs,
            "fragments_with_pairs": self.fragments_with_pairs,
            "fragments_single_mnn": self.fragments_single_mnn,
            "fragments_no_mnn": self.fragments_no_mnn,
            "fragments_image": self.fragments_image,
            "fragments_all_exist": self.fragments_all_exist,
            "total_fragments_processed": self.total_fragments_processed,
            "skip_rate": round(self.skip_rate, 4),
            "fragment_diagnostics": [
                {
                    "fragment_id": d.fragment_id,
                    "content_kind": d.content_kind,
                    "mnn_hits": d.mnn_hits,
                    "new_pairs": d.new_pairs,
                    "skipped_pairs": d.skipped_pairs,
                    "skip_reason": d.skip_reason.value if d.skip_reason else None,
                    "context_id": d.context_id,
                }
                for d in self.fragment_diagnostics
            ],
        }


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

    # ------------------------------------------------------------------
    # Diagnostic variant — returns rich per-fragment breakdown
    # ------------------------------------------------------------------

    def generate_pairs_with_diagnostics(
        self,
        version_id: int,
        max_fragment_details: int = 500,
    ) -> CandidateDiagnosticResult:
        """Like ``generate_pairs`` but returns a :class:`CandidateDiagnosticResult`.

        All pairs ARE written to the database (same side-effects as
        ``generate_pairs``).  The diagnostic result provides per-fragment
        reasons for any fragment that did not contribute new pairs, which
        is useful for debugging sparse evidence distributions.
        """
        result = CandidateDiagnosticResult(version_id=version_id)
        session = get_sync_session()

        try:
            self.mnn_extractor.load_dictionary()

            contexts = (
                session.query(ClinicalContext)
                .filter_by(document_version_id=version_id)
                .all()
            )

            if not contexts:
                logger.info(
                    "generate_pairs_with_diagnostics: no contexts for version %d", version_id
                )
                return result

            sections = (
                session.query(DocumentSection)
                .filter_by(document_version_id=version_id)
                .order_by(DocumentSection.section_order)
                .all()
            )

            for context in contexts:
                for section in sections:
                    fragments = (
                        session.query(TextFragment)
                        .filter_by(section_id=section.id)
                        .order_by(TextFragment.fragment_order)
                        .all()
                    )

                    for frag in fragments:
                        diag = self._process_fragment_diagnostic(
                            session=session,
                            frag=frag,
                            context=context,
                            result=result,
                            max_fragment_details=max_fragment_details,
                        )
                        if diag.skip_reason == FragmentSkipReason.PRODUCED_PAIRS:
                            result.fragments_with_pairs += 1
                        elif diag.skip_reason == FragmentSkipReason.NO_MNN:
                            result.fragments_no_mnn += 1
                        elif diag.skip_reason == FragmentSkipReason.SINGLE_MNN:
                            result.fragments_single_mnn += 1
                        elif diag.skip_reason == FragmentSkipReason.IMAGE_FRAGMENT:
                            result.fragments_image += 1
                        elif diag.skip_reason == FragmentSkipReason.ALL_PAIRS_EXIST:
                            result.fragments_all_exist += 1

                        result.total_new_pairs += diag.new_pairs
                        result.total_skipped_pairs += diag.skipped_pairs

                        if len(result.fragment_diagnostics) < max_fragment_details:
                            result.fragment_diagnostics.append(diag)

                session.flush()

            session.commit()
            logger.info(
                "generate_pairs_with_diagnostics: version=%d new=%d skipped=%d fragments=%d",
                version_id,
                result.total_new_pairs,
                result.total_skipped_pairs,
                result.total_fragments_processed,
            )
            return result

        finally:
            session.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_fragment_diagnostic(
        self,
        *,
        session,
        frag: "TextFragment",  # noqa: F821 – forward ref for readability
        context: "ClinicalContext",  # noqa: F821
        result: "CandidateDiagnosticResult",  # noqa: F821
        max_fragment_details: int,
    ) -> FragmentCandidateDiagnostic:
        """Process one fragment and return its diagnostic record.

        Side-effects: may add ``PairEvidence`` rows to *session*.
        """
        content_kind = getattr(frag, "content_kind", "text") or "text"
        text_prefix = (frag.fragment_text or "")[:60].replace("\n", " ")

        base = FragmentCandidateDiagnostic(
            fragment_id=frag.id,
            fragment_text_prefix=text_prefix,
            content_kind=content_kind,
            mnn_hits=0,
            new_pairs=0,
            skipped_pairs=0,
            context_id=context.id,
        )

        # Images are intentionally skipped — no text to extract from
        if content_kind == "image":
            base.skip_reason = FragmentSkipReason.IMAGE_FRAGMENT
            return base

        mnn_hits = self.mnn_extractor.extract(frag.fragment_text or "")
        mol_ids = list({h["molecule_id"] for h in mnn_hits})
        base.mnn_hits = len(mnn_hits)

        if not mol_ids:
            base.skip_reason = FragmentSkipReason.NO_MNN
            return base

        if len(mol_ids) < 2:
            base.skip_reason = FragmentSkipReason.SINGLE_MNN
            return base

        # Extract relation and UUR/UDD signals once per fragment
        relation_signals = self.relation_extractor.extract(frag.fragment_text)
        relation_type, _conf = self.relation_extractor.classify_relation(relation_signals)
        uur_udd = self.uur_udd_extractor.extract(frag.fragment_text)
        uur = uur_udd[0]["uur"] if uur_udd else None
        udd = uur_udd[0]["udd"] if uur_udd else None

        all_existed = True
        for mol_from, mol_to in permutations(mol_ids, 2):
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
                base.skipped_pairs += 1
                continue

            all_existed = False
            evidence = PairEvidence(
                context_id=context.id,
                molecule_from_id=mol_from,
                molecule_to_id=mol_to,
                fragment_id=frag.id,
                relation_type=relation_type,
                uur=uur,
                udd=udd,
                review_status="auto",
                extractor_version="candidate_v1.1",
            )
            session.add(evidence)
            base.new_pairs += 1

        if base.new_pairs > 0:
            base.skip_reason = FragmentSkipReason.PRODUCED_PAIRS
        elif all_existed:
            base.skip_reason = FragmentSkipReason.ALL_PAIRS_EXIST
        else:
            # edge case: skipped_pairs == 0 and new_pairs == 0 shouldn't happen
            base.skip_reason = FragmentSkipReason.ALL_PAIRS_EXIST

        return base
