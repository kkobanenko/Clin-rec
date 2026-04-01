"""Release service — release gating, version management, and diff generation."""

import logging
from datetime import datetime

from sqlalchemy import func

from app.core.sync_database import get_sync_session
from app.models.evidence import MatrixCell, PairContextScore
from app.models.scoring import ScoringModelVersion
from app.models.pipeline import PipelineRun

logger = logging.getLogger(__name__)

# Minimum thresholds for release readiness
RELEASE_THRESHOLDS = {
    "min_evidence_count": 10,
    "min_reviewed_ratio": 0.8,
    "min_contexts": 3,
    "max_low_confidence_ratio": 0.2,
}


class ReleaseService:
    def check_readiness(self, model_version_id: int) -> dict:
        """Check if a model version is ready for release.

        Returns a checklist dict with pass/fail for each criterion.
        """
        session = get_sync_session()
        try:
            model = session.get(ScoringModelVersion, model_version_id)
            if not model:
                return {"ready": False, "error": "Model version not found"}

            # Count matrix cells
            cell_count = (
                session.query(func.count(MatrixCell.id))
                .filter_by(model_version_id=model_version_id)
                .scalar()
            )

            # Count low-confidence cells
            low_conf_count = (
                session.query(func.count(MatrixCell.id))
                .filter(
                    MatrixCell.model_version_id == model_version_id,
                    MatrixCell.confidence_score < 0.3,
                )
                .scalar()
            )

            # Count pair context scores
            pcs_count = (
                session.query(func.count(PairContextScore.id))
                .filter_by(model_version_id=model_version_id)
                .scalar()
            )

            low_conf_ratio = low_conf_count / cell_count if cell_count > 0 else 1.0

            checks = {
                "has_matrix_cells": cell_count > 0,
                "sufficient_evidence": pcs_count >= RELEASE_THRESHOLDS["min_evidence_count"],
                "low_confidence_acceptable": low_conf_ratio <= RELEASE_THRESHOLDS["max_low_confidence_ratio"],
                "cell_count": cell_count,
                "pcs_count": pcs_count,
                "low_confidence_ratio": round(low_conf_ratio, 4),
            }
            checks["ready"] = all([
                checks["has_matrix_cells"],
                checks["sufficient_evidence"],
                checks["low_confidence_acceptable"],
            ])

            return checks
        finally:
            session.close()

    def create_release(self, model_version_id: int, author: str) -> dict | None:
        """Mark a model version as released (set is_active flag)."""
        session = get_sync_session()
        try:
            readiness = self.check_readiness(model_version_id)
            if not readiness.get("ready"):
                logger.warning("Model %d not ready for release: %s", model_version_id, readiness)
                return None

            model = session.get(ScoringModelVersion, model_version_id)
            if not model:
                return None

            # Deactivate previous active version
            session.query(ScoringModelVersion).filter(
                ScoringModelVersion.is_active.is_(True),
                ScoringModelVersion.id != model_version_id,
            ).update({"is_active": False})

            model.is_active = True
            session.commit()

            logger.info("Released model version %d by %s", model_version_id, author)
            return {
                "model_version_id": model_version_id,
                "version_label": model.version_label,
                "released_by": author,
                "readiness": readiness,
            }
        finally:
            session.close()

    def diff_versions(self, old_version_id: int, new_version_id: int) -> dict:
        """Generate a diff between two model versions' matrix cells."""
        session = get_sync_session()
        try:
            old_cells = {
                (c.molecule_from_id, c.molecule_to_id, c.scope_type, c.scope_id): c
                for c in session.query(MatrixCell).filter_by(model_version_id=old_version_id).all()
            }
            new_cells = {
                (c.molecule_from_id, c.molecule_to_id, c.scope_type, c.scope_id): c
                for c in session.query(MatrixCell).filter_by(model_version_id=new_version_id).all()
            }

            added = []
            removed = []
            changed = []

            for key, new_cell in new_cells.items():
                if key not in old_cells:
                    added.append({
                        "from": key[0], "to": key[1],
                        "scope_type": key[2], "scope_id": key[3],
                        "score": new_cell.substitution_score,
                    })
                else:
                    old_cell = old_cells[key]
                    if abs(new_cell.substitution_score - old_cell.substitution_score) > 0.01:
                        changed.append({
                            "from": key[0], "to": key[1],
                            "scope_type": key[2], "scope_id": key[3],
                            "old_score": old_cell.substitution_score,
                            "new_score": new_cell.substitution_score,
                            "delta": round(new_cell.substitution_score - old_cell.substitution_score, 4),
                        })

            for key in old_cells:
                if key not in new_cells:
                    old_cell = old_cells[key]
                    removed.append({
                        "from": key[0], "to": key[1],
                        "scope_type": key[2], "scope_id": key[3],
                        "score": old_cell.substitution_score,
                    })

            return {
                "old_version_id": old_version_id,
                "new_version_id": new_version_id,
                "added": len(added),
                "removed": len(removed),
                "changed": len(changed),
                "details": {"added": added, "removed": removed, "changed": changed},
            }
        finally:
            session.close()
