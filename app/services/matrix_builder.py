"""Matrix builder — aggregates PairContextScores into MatrixCells."""

import logging
from collections import defaultdict

from app.core.sync_database import get_sync_session
from app.models.evidence import MatrixCell, PairContextScore
from app.models.clinical import ClinicalContext
from app.models.molecule import Molecule

logger = logging.getLogger(__name__)


class MatrixBuilder:
    def _build_matrix_explanation(self, context_scores: list[PairContextScore]) -> dict:
        return {
            "contexts": [
                {
                    "pair_context_score_id": s.id,
                    "context_id": s.context_id,
                    "substitution_score": s.substitution_score,
                    "confidence_score": s.confidence_score,
                    "evidence_count": s.evidence_count,
                    "evidence_ids": (s.explanation_json or {}).get("evidence_ids", []),
                    "fragment_ids": (s.explanation_json or {}).get("fragment_ids", []),
                }
                for s in context_scores
            ],
            "pair_context_score_ids": [s.id for s in context_scores if getattr(s, "id", None) is not None],
            "aggregation": "mean",
        }

    def build(self, model_version_id: int, scope_type: str = "global", scope_id: str | None = None) -> int:
        """Build or rebuild matrix cells from pair context scores.

        Returns number of matrix cells created/updated.
        """
        session = get_sync_session()
        try:
            query = session.query(PairContextScore).filter_by(model_version_id=model_version_id)

            if scope_type == "disease" and scope_id:
                # Filter by disease context
                context_ids = [
                    c.id for c in session.query(ClinicalContext).filter(
                        ClinicalContext.disease_name == scope_id
                    ).all()
                ]
                if context_ids:
                    query = query.filter(PairContextScore.context_id.in_(context_ids))
                else:
                    return 0

            scores = query.all()

            # Group by (from, to) pair
            grouped: dict[tuple[int, int], list[PairContextScore]] = defaultdict(list)
            for s in scores:
                grouped[(s.molecule_from_id, s.molecule_to_id)].append(s)

            count = 0
            for (mol_from, mol_to), context_scores in grouped.items():
                sub_scores = [s.substitution_score for s in context_scores if s.substitution_score is not None]
                conf_scores = [s.confidence_score for s in context_scores if s.confidence_score is not None]
                evidence_counts = sum(s.evidence_count for s in context_scores)

                if not sub_scores:
                    continue

                # Global aggregation: weighted average across contexts
                global_sub = sum(sub_scores) / len(sub_scores)
                global_conf = sum(conf_scores) / len(conf_scores) if conf_scores else 0.5

                # Build explanation
                explanation = self._build_matrix_explanation(context_scores)

                # Get molecule names for short explanation
                mol_from_obj = session.get(Molecule, mol_from)
                mol_to_obj = session.get(Molecule, mol_to)
                explanation_short = (
                    f"{mol_from_obj.inn_ru if mol_from_obj else mol_from} → "
                    f"{mol_to_obj.inn_ru if mol_to_obj else mol_to}: "
                    f"score={global_sub:.2f}, confidence={global_conf:.2f}, "
                    f"contexts={len(context_scores)}"
                )

                # Upsert matrix cell
                existing = (
                    session.query(MatrixCell)
                    .filter_by(
                        model_version_id=model_version_id,
                        scope_type=scope_type,
                        scope_id=scope_id,
                        molecule_from_id=mol_from,
                        molecule_to_id=mol_to,
                    )
                    .first()
                )

                if existing:
                    existing.substitution_score = round(global_sub, 4)
                    existing.confidence_score = round(global_conf, 4)
                    existing.contexts_count = len(context_scores)
                    existing.supporting_evidence_count = evidence_counts
                    existing.explanation_short = explanation_short
                    existing.explanation_json = explanation
                else:
                    cell = MatrixCell(
                        model_version_id=model_version_id,
                        scope_type=scope_type,
                        scope_id=scope_id,
                        molecule_from_id=mol_from,
                        molecule_to_id=mol_to,
                        substitution_score=round(global_sub, 4),
                        confidence_score=round(global_conf, 4),
                        contexts_count=len(context_scores),
                        supporting_evidence_count=evidence_counts,
                        explanation_short=explanation_short,
                        explanation_json=explanation,
                    )
                    session.add(cell)

                count += 1

            session.commit()
            logger.info("Built %d matrix cells for model %d, scope %s", count, model_version_id, scope_type)
            return count

        finally:
            session.close()
