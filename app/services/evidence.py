"""Evidence service — manages pair evidence records and provides query helpers."""

import logging

from sqlalchemy import and_, select

from app.core.sync_database import get_sync_session
from app.models.evidence import PairEvidence

logger = logging.getLogger(__name__)


class EvidenceService:
    def get_evidence_for_pair(
        self,
        molecule_from_id: int,
        molecule_to_id: int,
        context_id: int | None = None,
    ) -> list[PairEvidence]:
        """Get all evidence records for a directed pair."""
        session = get_sync_session()
        try:
            query = session.query(PairEvidence).filter(
                PairEvidence.molecule_from_id == molecule_from_id,
                PairEvidence.molecule_to_id == molecule_to_id,
            )
            if context_id:
                query = query.filter(PairEvidence.context_id == context_id)

            return query.all()
        finally:
            session.close()

    def get_evidence_for_context(self, context_id: int) -> list[PairEvidence]:
        """Get all evidence records for a context."""
        session = get_sync_session()
        try:
            return (
                session.query(PairEvidence)
                .filter_by(context_id=context_id)
                .order_by(PairEvidence.molecule_from_id, PairEvidence.molecule_to_id)
                .all()
            )
        finally:
            session.close()

    def get_unique_pairs(self, context_id: int | None = None) -> list[tuple[int, int]]:
        """Get unique (from, to) pairs, optionally filtered by context."""
        session = get_sync_session()
        try:
            query = session.query(
                PairEvidence.molecule_from_id,
                PairEvidence.molecule_to_id,
            ).distinct()
            if context_id:
                query = query.filter(PairEvidence.context_id == context_id)
            return [(r[0], r[1]) for r in query.all()]
        finally:
            session.close()

    def count_evidence(self, molecule_from_id: int, molecule_to_id: int) -> int:
        """Count evidence records for a directed pair."""
        session = get_sync_session()
        try:
            return (
                session.query(PairEvidence)
                .filter_by(molecule_from_id=molecule_from_id, molecule_to_id=molecule_to_id)
                .count()
            )
        finally:
            session.close()
