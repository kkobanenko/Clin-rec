from celery import current_task

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion
from app.models.scoring import ScoringModelVersion
from app.services.candidate_engine import CandidateEngine
from app.services.matrix_builder import MatrixBuilder
from app.services.scoring.engine import ScoringEngine
from app.workers.celery_app import celery_app
from app.services.extraction.pipeline import ExtractionPipeline
from app.services.pipeline_event_log import write_pipeline_event


@celery_app.task(name="app.workers.tasks.extract.extract_document", queue="extract")
def extract_document(version_id: int):
    session = get_sync_session()
    version = session.get(DocumentVersion, version_id)
    session.close()
    registry_id = version.registry_id if version else None
    task_id = getattr(getattr(current_task, "request", None), "id", None)
    if registry_id is not None:
        write_pipeline_event(
            document_registry_id=registry_id,
            document_version_id=version_id,
            celery_task_id=task_id,
            stage="extract",
            status="start",
            message="Started extract stage",
            detail_json={"version_id": version_id},
        )
    pipeline = ExtractionPipeline()
    try:
        extraction_result = pipeline.extract(version_id=version_id)
        candidate_pairs_count = CandidateEngine().generate_pairs(version_id=version_id)
        score_contexts_count = 0
        matrix_cells_count = 0
        active_model_version_id = None
        scoring_session = get_sync_session()
        try:
            active_model = (
                scoring_session.query(ScoringModelVersion)
                .filter(ScoringModelVersion.is_active.is_(True))
                .order_by(ScoringModelVersion.created_at.desc(), ScoringModelVersion.id.desc())
                .first()
            )
            if active_model is not None:
                active_model_version_id = active_model.id
                score_contexts_count = ScoringEngine().score_all(model_version_id=active_model.id)
                matrix_cells_count = MatrixBuilder().build(model_version_id=active_model.id, scope_type="global")
        finally:
            scoring_session.close()
        if registry_id is not None:
            write_pipeline_event(
                document_registry_id=registry_id,
                document_version_id=version_id,
                celery_task_id=task_id,
                stage="extract",
                status="success",
                message="Extract stage finished successfully",
                detail_json={
                    "version_id": version_id,
                    "mnn_count": extraction_result.mnn_count,
                    "uur_udd_count": extraction_result.uur_udd_count,
                    "relation_count": extraction_result.relation_count,
                    "context_count": extraction_result.context_count,
                    "mnn_molecule_ids": list(extraction_result.mnn_molecule_ids),
                    "candidate_pairs_count": candidate_pairs_count,
                    "active_model_version_id": active_model_version_id,
                    "score_contexts_count": score_contexts_count,
                    "matrix_cells_count": matrix_cells_count,
                },
            )
    except Exception as exc:
        if registry_id is not None:
            write_pipeline_event(
                document_registry_id=registry_id,
                document_version_id=version_id,
                celery_task_id=task_id,
                stage="extract",
                status="failed",
                message="Extract stage raised an exception",
                detail_json={"reason_code": "extract_exception", "error": str(exc)},
            )
        raise
