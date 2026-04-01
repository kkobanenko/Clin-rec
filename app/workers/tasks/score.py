from app.workers.celery_app import celery_app
from app.services.scoring.engine import ScoringEngine


@celery_app.task(name="app.workers.tasks.score.score_pairs", queue="score")
def score_pairs(model_version_id: int):
    engine = ScoringEngine()
    engine.score_all(model_version_id=model_version_id)


@celery_app.task(name="app.workers.tasks.score.build_matrix", queue="score")
def build_matrix(model_version_id: int, scope_type: str = "global"):
    from app.services.matrix_builder import MatrixBuilder
    builder = MatrixBuilder()
    builder.build(model_version_id=model_version_id, scope_type=scope_type)
