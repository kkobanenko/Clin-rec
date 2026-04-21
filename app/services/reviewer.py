"""Reviewer service — manages review queue, approve/reject/override actions."""

import logging
from datetime import datetime

from sqlalchemy import func

from app.core.sync_database import get_sync_session
from app.models.evidence import PairEvidence, PairContextScore
from app.models.reviewer import ReviewAction

logger = logging.getLogger(__name__)


class ReviewerService:
    def get_review_queue(
        self, status: str = "auto", limit: int = 50, offset: int = 0
    ) -> list[PairEvidence]:
        """Get evidence records awaiting review."""
        session = get_sync_session()
        try:
            query = (
                session.query(PairEvidence)
                .filter_by(review_status=status)
                .order_by(PairEvidence.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return query.all()
        finally:
            session.close()

    def approve(self, evidence_id: int, author: str, reason: str | None = None) -> ReviewAction | None:
        """Approve an evidence record."""
        return self._apply_action(evidence_id, "approve", author, reason)

    def reject(self, evidence_id: int, author: str, reason: str) -> ReviewAction | None:
        """Reject an evidence record (reason required)."""
        return self._apply_action(evidence_id, "reject", author, reason)

    def override_score(
        self,
        evidence_id: int,
        author: str,
        new_score: float,
        reason: str,
    ) -> ReviewAction | None:
        """Override the final fragment score of an evidence record."""
        session = get_sync_session()
        try:
            evidence = session.get(PairEvidence, evidence_id)
            if not evidence:
                return None

            old_value = {"final_fragment_score": evidence.final_fragment_score}
            new_value = {"final_fragment_score": new_score}

            evidence.final_fragment_score = new_score
            evidence.review_status = "overridden"

            action = ReviewAction(
                target_type="pair_evidence",
                target_id=evidence_id,
                action="override",
                old_value_json=old_value,
                new_value_json=new_value,
                reason=reason,
                author=author,
            )
            session.add(action)
            session.commit()
            session.refresh(action)
            logger.info("Score overridden for evidence %d by %s", evidence_id, author)
            return action
        finally:
            session.close()

    def bulk_approve(self, evidence_ids: list[int], author: str) -> int:
        """Bulk approve multiple evidence records. Returns count of approved."""
        count = 0
        for eid in evidence_ids:
            if self._apply_action(eid, "approve", author, None):
                count += 1
        return count

    def get_review_stats(self) -> dict:
        """Get review statistics."""
        session = get_sync_session()
        try:
            result = (
                session.query(PairEvidence.review_status, func.count(PairEvidence.id))
                .group_by(PairEvidence.review_status)
                .all()
            )
            return dict(result)
        finally:
            session.close()

    def get_review_history(
        self, target_type: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[ReviewAction]:
        """Get review action audit trail."""
        session = get_sync_session()
        try:
            query = session.query(ReviewAction).order_by(ReviewAction.created_at.desc())
            if target_type:
                query = query.filter_by(target_type=target_type)
            return query.offset(offset).limit(limit).all()
        finally:
            session.close()

    def _apply_action(
        self, evidence_id: int, action_type: str, author: str, reason: str | None
    ) -> ReviewAction | None:
        """Apply a review action to an evidence record."""
        session = get_sync_session()
        try:
            evidence = session.get(PairEvidence, evidence_id)
            if not evidence:
                return None

            old_status = evidence.review_status
            new_status = "approved" if action_type == "approve" else "rejected"
            evidence.review_status = new_status

            action = ReviewAction(
                target_type="pair_evidence",
                target_id=evidence_id,
                action=action_type,
                old_value_json={"review_status": old_status},
                new_value_json={"review_status": new_status},
                reason=reason,
                author=author,
            )
            session.add(action)
            session.commit()
            session.refresh(action)
            logger.info("Evidence %d %s by %s", evidence_id, action_type, author)
            return action
        finally:
            session.close()
