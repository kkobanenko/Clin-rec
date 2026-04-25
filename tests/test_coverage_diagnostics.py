"""Tests for coverage diagnostics."""

from app.core.coverage_diagnostics import (
    calculate_document_coverage,
    correlation_evidence_to_artifact,
    validate_evidence_pipeline_completeness,
    handle_missing_artifact_gracefully,
    correlate_error_with_pipeline_stage,
)


def test_coverage_calculation():
    """Test coverage metrics calculation."""
    result = calculate_document_coverage(100, 95, 92)
    assert result['total_documents'] == 100
    assert result['artifact_coverage_pct'] == 95.0
    assert result['evidence_coverage_pct'] == 92.0


def test_correlation_metrics():
    """Test correlation calculation."""
    result = correlation_evidence_to_artifact(1000, 100)
    assert result['evidence_count'] == 1000
    assert result['evidence_per_artifact'] == 10.0


def test_pipeline_completeness():
    """Test pipeline completeness validation."""
    result = validate_evidence_pipeline_completeness(
        discovered=100,
        fetched=99,
        normalized=98,
        extracted=97,
        scored=96
    )
    assert result['stage_discovery']['pct'] == 100
    assert result['stage_fetch']['pct'] == 99.0


def test_missing_artifact_message():
    """Test missing artifact error message."""
    result = handle_missing_artifact_gracefully("missing")
    assert 'message' in result
    assert 'action' in result


def test_error_stage_correlation():
    """Test error to pipeline stage correlation."""
    stage = correlate_error_with_pipeline_stage("Failed to fetch artifact from S3")
    assert stage == "fetch"
    
    stage = correlate_error_with_pipeline_stage("Entity extraction timeout")
    assert stage == "extract"
