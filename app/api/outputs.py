"""API аналитических outputs и output filing (TZ §17)."""


import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.knowledge import OutputRelease
from app.schemas.knowledge import (
    OutputFileBackBody,
    OutputFileRequest,
    OutputGenerateRequest,
    OutputReleaseRequest,
    OutputReleaseOut,
)
from app.schemas.pipeline import PaginatedResponse
from app.workers.tasks.kb import file_outputs as file_outputs_task
from app.workers.tasks.kb import generate_outputs as generate_outputs_task

router = APIRouter(prefix="/outputs", tags=["outputs"])


def _apply_review_status_filter(query, review_status: str):
    aliases = {
        "pending_review": ("pending_review", "pending", "needs_review"),
        "approved": ("approved", "accepted"),
        "released": ("released",),
    }
    values = aliases.get(review_status)
    if values:
        return query.where(OutputRelease.review_status.in_(values))
    return query.where(OutputRelease.review_status == review_status)


def _normalized_release_status(review_status: str | None) -> str:
    if review_status == "accepted":
        return "approved"
    if review_status == "pending":
        return "pending_review"
    return review_status or "pending_review"


@router.post("/generate", status_code=202)
async def generate_output(body: OutputGenerateRequest):
    """Постановка в очередь: worker создаёт строку output_release (черновик)."""
    async_result = generate_outputs_task.delay(
        output_type=body.output_type,
        title=body.title,
        scope_json=body.scope_json,
    )
    return {
        "task_id": async_result.id,
        "status": "queued",
        "output_type": body.output_type,
        "message": "generate_outputs queued — по готовности см. GET /outputs",
    }


@router.post("/file", status_code=202)
async def file_output(body: OutputFileRequest):
    """Output filing workflow: обновление статуса (обработка в worker)."""
    async_result = file_outputs_task.delay(body.output_id, body.file_back_status)
    return {"task_id": async_result.id, "status": "queued", "output_id": body.output_id}


@router.post("/memo", status_code=202)
async def generate_memo_alias(body: OutputGenerateRequest):
    """TZ §17: алиас POST /outputs/generate с output_type=memo."""
    async_result = generate_outputs_task.delay(
        output_type="memo",
        title=body.title,
        scope_json=body.scope_json,
    )
    return {
        "task_id": async_result.id,
        "status": "queued",
        "output_type": "memo",
        "message": "memo generation queued — см. GET /outputs",
    }


@router.post("/file-back/{output_id}", status_code=202)
async def file_back_alias(output_id: int, body: OutputFileBackBody):
    """TZ §17: алиас к POST /outputs/file с output_id в пути."""
    async_result = file_outputs_task.delay(output_id, body.file_back_status)
    return {"task_id": async_result.id, "status": "queued", "output_id": output_id}


@router.get("", response_model=PaginatedResponse)
async def list_outputs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    output_type: str | None = None,
    file_back_status: str | None = None,
    review_status: str | None = None,
    generator_version: str | None = None,
    released_only: bool = False,
    has_file_pointer: bool = False,
    artifact_id: int | None = None,
    search: str | None = Query(None, description="Подстрока в title или file_pointer (ILIKE)"),
):
    q = select(OutputRelease)
    count_q = select(func.count(OutputRelease.id))
    if output_type:
        q = q.where(OutputRelease.output_type == output_type)
        count_q = count_q.where(OutputRelease.output_type == output_type)
    if file_back_status:
        q = q.where(OutputRelease.file_back_status == file_back_status)
        count_q = count_q.where(OutputRelease.file_back_status == file_back_status)
    if review_status:
        q = _apply_review_status_filter(q, review_status)
        count_q = _apply_review_status_filter(count_q, review_status)
    if generator_version:
        q = q.where(OutputRelease.generator_version == generator_version)
        count_q = count_q.where(OutputRelease.generator_version == generator_version)
    if released_only:
        q = q.where(OutputRelease.released_at.is_not(None))
        count_q = count_q.where(OutputRelease.released_at.is_not(None))
    if has_file_pointer:
        q = q.where(OutputRelease.file_pointer.is_not(None))
        count_q = count_q.where(OutputRelease.file_pointer.is_not(None))
    if artifact_id is not None:
        q = q.where(OutputRelease.artifact_id == artifact_id)
        count_q = count_q.where(OutputRelease.artifact_id == artifact_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filt = or_(
            OutputRelease.title.ilike(term),
            OutputRelease.file_pointer.ilike(term),
            cast(OutputRelease.scope_json, Text).ilike(term),
        )
        q = q.where(filt)
        count_q = count_q.where(filt)
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(OutputRelease.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = [OutputReleaseOut.model_validate(r) for r in rows]
    pages = (total + page_size - 1) // page_size if page_size else 1
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get(
    "/candidate-diagnostics",
    summary="Recent candidate generation diagnostics summary",
)
async def get_candidate_diagnostics(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0.0, le=1.0),
    top_n: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return candidate diagnostics summary from recent successful extract events."""
    del db
    from app.services.candidate_diagnostics_report import CandidateDiagnosticsReportService

    svc = CandidateDiagnosticsReportService()
    report = svc.generate_report(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        top_n=top_n,
    )
    return report.to_dict()


@router.get(
    "/candidate-diagnostics/markdown",
    summary="Candidate diagnostics report as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_candidate_diagnostics_markdown(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0.0, le=1.0),
    top_n: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return candidate diagnostics report as Markdown text."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.candidate_diagnostics_report import CandidateDiagnosticsReportService

    svc = CandidateDiagnosticsReportService()
    report = svc.generate_report(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        top_n=top_n,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate",
    summary="Automated quality gate verdict for release readiness",
)
async def get_quality_gate(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0.0, le=1.0),
    max_avg_skip_rate: float = Query(0.75, ge=0.0, le=1.0),
    min_candidate_pairs: int = Query(1, ge=0, le=100000),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate quality gate verdict and evaluated rule set."""
    del db
    from app.services.quality_gate import QualityGateService

    svc = QualityGateService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
    )
    return report.to_dict()


@router.get(
    "/quality-gate/markdown",
    summary="Automated quality gate report as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_markdown(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0.0, le=1.0),
    max_avg_skip_rate: float = Query(0.75, ge=0.0, le=1.0),
    min_candidate_pairs: int = Query(1, ge=0, le=100000),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate quality gate verdict in markdown format."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate import QualityGateService

    svc = QualityGateService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate/queue-status",
    summary="Quality gate notification queue status",
)
async def get_quality_gate_queue_status(
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    db: AsyncSession = Depends(get_db),
):
    """Return queue status for quality gate notification spool."""
    del db
    from app.services.quality_gate_queue_status import QualityGateQueueStatusService

    svc = QualityGateQueueStatusService()
    report = svc.generate_report(
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        max_items=max_items,
    )
    return report.to_dict()


@router.get(
    "/quality-gate/queue-status/markdown",
    summary="Quality gate queue status as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_queue_status_markdown(
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    db: AsyncSession = Depends(get_db),
):
    """Return queue status report as Markdown."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate_queue_status import QualityGateQueueStatusService

    svc = QualityGateQueueStatusService()
    report = svc.generate_report(
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        max_items=max_items,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate/queue-policy",
    summary="Queue policy/SLO verdict for quality gate notification backlog",
)
async def get_quality_gate_queue_policy(
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    queue_size_warn: float = Query(20, ge=0),
    queue_size_fail: float = Query(100, ge=0),
    oldest_age_warn: float = Query(900, ge=0),
    oldest_age_fail: float = Query(3600, ge=0),
    total_size_warn: float = Query(1_000_000, ge=0),
    total_size_fail: float = Query(10_000_000, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return queue policy verdict derived from queue status metrics."""
    del db
    from app.services.quality_gate_queue_policy import QualityGateQueuePolicyService

    thresholds = {
        "queue_size_warn": queue_size_warn,
        "queue_size_fail": queue_size_fail,
        "oldest_age_warn": oldest_age_warn,
        "oldest_age_fail": oldest_age_fail,
        "total_size_warn": total_size_warn,
        "total_size_fail": total_size_fail,
    }
    svc = QualityGateQueuePolicyService(thresholds=thresholds)
    report = svc.evaluate(
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        max_items=max_items,
    )
    return report.to_dict()


@router.get(
    "/quality-gate/queue-policy/markdown",
    summary="Queue policy/SLO verdict as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_queue_policy_markdown(
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    queue_size_warn: float = Query(20, ge=0),
    queue_size_fail: float = Query(100, ge=0),
    oldest_age_warn: float = Query(900, ge=0),
    oldest_age_fail: float = Query(3600, ge=0),
    total_size_warn: float = Query(1_000_000, ge=0),
    total_size_fail: float = Query(10_000_000, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return queue policy verdict report as Markdown."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate_queue_policy import QualityGateQueuePolicyService

    thresholds = {
        "queue_size_warn": queue_size_warn,
        "queue_size_fail": queue_size_fail,
        "oldest_age_warn": oldest_age_warn,
        "oldest_age_fail": oldest_age_fail,
        "total_size_warn": total_size_warn,
        "total_size_fail": total_size_fail,
    }
    svc = QualityGateQueuePolicyService(thresholds=thresholds)
    report = svc.evaluate(
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        max_items=max_items,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate/incident",
    summary="Incident escalation report combining quality gate and queue policy",
)
async def get_quality_gate_incident(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0, le=1),
    max_avg_skip_rate: float = Query(0.75, ge=0, le=1),
    min_candidate_pairs: int = Query(1, ge=0, le=50),
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    db: AsyncSession = Depends(get_db),
):
    """Return escalation report for release incident handling."""
    del db
    from app.services.quality_gate_incident import QualityGateIncidentService

    svc = QualityGateIncidentService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        max_items=max_items,
    )
    return report.to_dict()


@router.get(
    "/quality-gate/incident/markdown",
    summary="Incident escalation report as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_incident_markdown(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0, le=1),
    max_avg_skip_rate: float = Query(0.75, ge=0, le=1),
    min_candidate_pairs: int = Query(1, ge=0, le=50),
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    db: AsyncSession = Depends(get_db),
):
    """Return escalation report as markdown."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate_incident import QualityGateIncidentService

    svc = QualityGateIncidentService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        max_items=max_items,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate/incident/registry",
    summary="Incident registry aggregate status",
)
async def get_quality_gate_incident_registry(
    max_items: int = Query(50, ge=1, le=500),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate incident registry report."""
    del db
    from app.services.quality_gate_incident_registry import QualityGateIncidentRegistryService

    svc = QualityGateIncidentRegistryService()
    report = svc.generate_report(
        registry_dir=registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"),
        max_items=max_items,
    )
    return report.to_dict()


@router.get(
    "/quality-gate/incident/registry/markdown",
    summary="Incident registry aggregate status as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_incident_registry_markdown(
    max_items: int = Query(50, ge=1, le=500),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate incident registry report in markdown format."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate_incident_registry import QualityGateIncidentRegistryService

    svc = QualityGateIncidentRegistryService()
    report = svc.generate_report(
        registry_dir=registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"),
        max_items=max_items,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate/incident/retention",
    summary="Incident registry retention policy evaluation",
)
async def get_quality_gate_incident_retention(
    max_items: int = Query(1000, ge=1, le=100000),
    max_age_days: int = Query(30, ge=1, le=3650),
    apply_changes: bool = Query(False, description="Apply retention cleanup if true"),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return retention policy outcome for incident registry."""
    del db
    from app.services.quality_gate_incident_retention import QualityGateIncidentRetentionService

    svc = QualityGateIncidentRetentionService()
    resolved_registry_dir = registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry")
    if apply_changes:
        report = svc.apply_policy(
            registry_dir=resolved_registry_dir,
            max_items=max_items,
            max_age_days=max_age_days,
        )
    else:
        report = svc.evaluate_policy(
            registry_dir=resolved_registry_dir,
            max_items=max_items,
            max_age_days=max_age_days,
        )
    return report.to_dict()


@router.get(
    "/quality-gate/incident/retention/markdown",
    summary="Incident registry retention policy as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_incident_retention_markdown(
    max_items: int = Query(1000, ge=1, le=100000),
    max_age_days: int = Query(30, ge=1, le=3650),
    apply_changes: bool = Query(False, description="Apply retention cleanup if true"),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return retention policy outcome for incident registry in markdown."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate_incident_retention import QualityGateIncidentRetentionService

    svc = QualityGateIncidentRetentionService()
    resolved_registry_dir = registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry")
    if apply_changes:
        report = svc.apply_policy(
            registry_dir=resolved_registry_dir,
            max_items=max_items,
            max_age_days=max_age_days,
        )
    else:
        report = svc.evaluate_policy(
            registry_dir=resolved_registry_dir,
            max_items=max_items,
            max_age_days=max_age_days,
        )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate/governance-score",
    summary="Aggregate governance score for release operations",
)
async def get_quality_gate_governance_score(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0, le=1),
    max_avg_skip_rate: float = Query(0.75, ge=0, le=1),
    min_candidate_pairs: int = Query(1, ge=0, le=50),
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return weighted governance score built from gate, queue, incident, and registry."""
    del db
    from app.services.quality_gate_governance_score import QualityGateGovernanceScoreService

    svc = QualityGateGovernanceScoreService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        registry_dir=registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"),
        max_items=max_items,
    )
    return report.to_dict()


@router.get(
    "/quality-gate/governance-score/markdown",
    summary="Governance score report as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_governance_score_markdown(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0, le=1),
    max_avg_skip_rate: float = Query(0.75, ge=0, le=1),
    min_candidate_pairs: int = Query(1, ge=0, le=50),
    max_items: int = Query(50, ge=1, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return governance score report in markdown."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate_governance_score import QualityGateGovernanceScoreService

    svc = QualityGateGovernanceScoreService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        registry_dir=registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"),
        max_items=max_items,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/quality-gate/governance-trends",
    summary="Governance trend analytics",
)
async def get_quality_gate_governance_trends(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0, le=1),
    max_avg_skip_rate: float = Query(0.75, ge=0, le=1),
    min_candidate_pairs: int = Query(1, ge=0, le=50),
    max_items: int = Query(50, ge=1, le=500),
    baseline_window: int = Query(10, ge=2, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return governance trend analytics relative to baseline window."""
    del db
    from app.services.quality_gate_governance_trends import QualityGateGovernanceTrendsService

    svc = QualityGateGovernanceTrendsService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        registry_dir=registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"),
        max_items=max_items,
        baseline_window=baseline_window,
    )
    return report.to_dict()


@router.get(
    "/quality-gate/governance-trends/markdown",
    summary="Governance trends report as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_quality_gate_governance_trends_markdown(
    max_versions: int = Query(100, ge=1, le=500),
    high_skip_threshold: float = Query(0.8, ge=0, le=1),
    max_avg_skip_rate: float = Query(0.75, ge=0, le=1),
    min_candidate_pairs: int = Query(1, ge=0, le=50),
    max_items: int = Query(50, ge=1, le=500),
    baseline_window: int = Query(10, ge=2, le=500),
    spool_dir: str | None = Query(None, description="Optional override for spool directory path"),
    registry_dir: str | None = Query(None, description="Optional override for incident registry directory"),
    db: AsyncSession = Depends(get_db),
):
    """Return governance trends report in markdown format."""
    del db
    from fastapi.responses import PlainTextResponse
    from app.services.quality_gate_governance_trends import QualityGateGovernanceTrendsService

    svc = QualityGateGovernanceTrendsService()
    report = svc.evaluate(
        max_versions=max_versions,
        high_skip_threshold=high_skip_threshold,
        max_avg_skip_rate=max_avg_skip_rate,
        min_candidate_pairs=min_candidate_pairs,
        spool_dir=spool_dir or os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"),
        registry_dir=registry_dir or os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"),
        max_items=max_items,
        baseline_window=baseline_window,
    )
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get("/{output_id}", response_model=OutputReleaseOut)
async def get_output(output_id: int, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(OutputRelease).where(OutputRelease.id == output_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Output not found")
    return OutputReleaseOut.model_validate(row)


@router.post("/{output_id}/release", response_model=OutputReleaseOut)
async def release_output(
    output_id: int,
    body: OutputReleaseRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(select(OutputRelease).where(OutputRelease.id == output_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Output not found")

    current_status = _normalized_release_status(row.review_status)
    if current_status == "released":
        return OutputReleaseOut.model_validate(row)
    if current_status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"Output cannot be released from review_status={current_status}",
        )

    actor = (body.author if body else None) or "system"
    row.review_status = "released"
    row.released_at = datetime.now(timezone.utc)
    scope = dict(row.scope_json or {})
    scope["release_audit"] = {
        "released_by": actor,
        "released_at": row.released_at.isoformat(),
        "release_action": "manual_release_endpoint",
    }
    row.scope_json = scope
    await db.commit()
    await db.refresh(row)
    return OutputReleaseOut.model_validate(row)


@router.get(
    "/release-evidence",
    summary="Generate current-head release evidence report",
)
async def get_release_evidence(
    include_state_counters: bool = True,
    max_sample_chains: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Return a structured JSON release evidence report for the current head.

    Includes artifact coverage, evidence density, sample traceability chains,
    and known limitations. Suitable for release documentation generation.
    Use `Accept: text/markdown` header (not enforced) to remind yourself
    to call `.to_markdown()` on the returned dict for a human-readable version.
    """
    from app.services.evidence_report import ReleaseEvidenceReportService

    svc = ReleaseEvidenceReportService()
    report = svc.generate_report(
        include_state_counters=include_state_counters,
        max_sample_chains=max_sample_chains,
    )
    return report.to_dict()


@router.get(
    "/release-evidence/markdown",
    summary="Generate release evidence report as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_release_evidence_markdown(
    db: AsyncSession = Depends(get_db),
):
    """Return release evidence report as a Markdown document."""
    from fastapi.responses import PlainTextResponse
    from app.services.evidence_report import ReleaseEvidenceReportService

    svc = ReleaseEvidenceReportService()
    report = svc.generate_report(include_state_counters=True)
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


@router.get(
    "/corpus-quality",
    summary="Corpus quality metrics: completeness, evidence richness, scoring readiness",
)
async def get_corpus_quality(
    db: AsyncSession = Depends(get_db),
):
    """Return a :class:`CorpusQualityReport` as JSON.

    Covers:
    * content_kind breakdown (text / html / table_like / image / unknown)
    * evidence richness (fragments with evidence, score coverage)
    * quality flags (warnings for image-heavy corpora, low evidence coverage, etc.)
    * overall health rating: healthy / degraded / critical / empty
    """
    from app.services.corpus_quality import CorpusQualityService

    svc = CorpusQualityService()
    report = svc.generate_report()
    return report.to_dict()


@router.get(
    "/corpus-quality/markdown",
    summary="Corpus quality report as Markdown",
    response_class=__import__("fastapi").responses.PlainTextResponse,
)
async def get_corpus_quality_markdown(
    db: AsyncSession = Depends(get_db),
):
    """Return corpus quality report as a Markdown document."""
    from fastapi.responses import PlainTextResponse
    from app.services.corpus_quality import CorpusQualityService

    svc = CorpusQualityService()
    report = svc.generate_report()
    return PlainTextResponse(content=report.to_markdown(), media_type="text/markdown")


