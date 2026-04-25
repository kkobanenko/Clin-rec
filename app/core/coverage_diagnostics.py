"""Coverage diagnostics helpers for artifact and evidence tracking."""


def calculate_document_coverage(total_documents: int, with_artifacts: int, with_evidence: int) -> dict:
    """Calculate coverage metrics for document corpus.
    
    Args:
        total_documents: Total document count
        with_artifacts: Documents with valid local artifacts
        with_evidence: Documents with extracted evidence
    
    Returns:
        Coverage metrics dictionary
    """
    return {
        "total_documents": total_documents,
        "artifact_coverage_pct": (with_artifacts / total_documents * 100) if total_documents else 0,
        "evidence_coverage_pct": (with_evidence / total_documents * 100) if total_documents else 0,
        "missing_artifacts": total_documents - with_artifacts,
        "missing_evidence": total_documents - with_evidence,
    }


def correlation_evidence_to_artifact(evidence_count: int, artifact_count: int) -> dict:
    """Calculate correlation between evidence and artifacts.
    
    Args:
        evidence_count: Total evidence records
        artifact_count: Total artifacts
    
    Returns:
        Correlation metrics
    """
    return {
        "evidence_count": evidence_count,
        "artifact_count": artifact_count,
        "evidence_per_artifact": (evidence_count / artifact_count) if artifact_count else 0,
        "artifacts_per_evidence": (artifact_count / evidence_count) if evidence_count else 0,
    }


def validate_evidence_pipeline_completeness(
    discovered: int,
    fetched: int,
    normalized: int,
    extracted: int,
    scored: int,
) -> dict:
    """Validate that pipeline stages completed correctly.
    
    Args:
        discovered: Documents discovered
        fetched: Documents with artifacts fetched
        normalized: Documents normalized
        extracted: Documents with entities extracted
        scored: Documents scored
    
    Returns:
        Completeness report
    """
    return {
        "stage_discovery": {"total": discovered, "pct": 100},
        "stage_fetch": {"total": fetched, "pct": (fetched / discovered * 100) if discovered else 0},
        "stage_normalize": {"total": normalized, "pct": (normalized / discovered * 100) if discovered else 0},
        "stage_extract": {"total": extracted, "pct": (extracted / discovered * 100) if discovered else 0},
        "stage_score": {"total": scored, "pct": (scored / discovered * 100) if discovered else 0},
        "pipeline_healthy": all([
            fetched / discovered >= 0.95 if discovered else False,
            normalized / discovered >= 0.95 if discovered else False,
            extracted / discovered >= 0.90 if discovered else False,
        ])
    }


def handle_missing_artifact_gracefully(error_type: str) -> dict:
    """Generate helpful message for missing artifact error.
    
    Args:
        error_type: Type of error (missing, corrupted, unvalidated)
    
    Returns:
        User-friendly error message dict
    """
    messages = {
        "missing": {
            "title": "Artifact Not Yet Available",
            "message": "This document's source artifact hasn't been fetched yet. Run full discovery to retrieve it.",
            "action": "Run Discovery Pipeline",
            "severity": "info",
        },
        "corrupted": {
            "title": "Artifact Validation Failed",
            "message": "This artifact failed validation (hash mismatch or format error). It will be re-fetched on next sync.",
            "action": "Trigger Re-fetch",
            "severity": "warning",
        },
        "unvalidated": {
            "title": "Artifact Pending Validation",
            "message": "This artifact was fetched but hasn't passed validation yet. Check logs for details.",
            "action": "View Logs",
            "severity": "warning",
        },
    }
    return messages.get(error_type, messages["missing"])


def correlate_error_with_pipeline_stage(error_msg: str) -> str:
    """Identify which pipeline stage likely caused the error.
    
    Args:
        error_msg: Error message
    
    Returns:
        Likely pipeline stage
    """
    if "discovery" in error_msg.lower():
        return "discovery"
    if "fetch" in error_msg.lower() or "download" in error_msg.lower():
        return "fetch"
    if "normalize" in error_msg.lower() or "section" in error_msg.lower():
        return "normalize"
    if "extract" in error_msg.lower() or "entity" in error_msg.lower():
        return "extract"
    if "score" in error_msg.lower() or "evidence" in error_msg.lower():
        return "score"
    return "unknown"
