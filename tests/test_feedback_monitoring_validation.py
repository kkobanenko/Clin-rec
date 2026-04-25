"""Tests for feedback, monitoring, and validation utilities."""


def test_feedback_collector():
    """Test feedback collector."""
    from app.core.feedback_and_monitoring import FeedbackCollector
    
    feedback = FeedbackCollector.create_feedback_record(
        operator_id="op1",
        output_id=1,
        feedback_type="validates",
    )
    
    assert feedback['operator_id'] == "op1"
    assert feedback['output_id'] == 1
    assert feedback['feedback_type'] == "validates"


def test_feedback_summary():
    """Test feedback summarization."""
    from app.core.feedback_and_monitoring import FeedbackCollector
    
    feedback_list = [
        {"feedback_type": "validates"},
        {"feedback_type": "validates"},
        {"feedback_type": "missing_evidence"},
    ]
    
    summary = FeedbackCollector.summarize_feedback(feedback_list)
    assert summary['total_feedback'] == 3
    assert summary['by_type']['validates'] == 2


def test_monitoring_health_check():
    """Test monitoring health check."""
    from app.core.feedback_and_monitoring import MonitoringService
    
    health = MonitoringService.create_pipeline_health_check()
    assert health['status'] in ['healthy', 'degraded', 'down']
    assert 'components' in health


def test_artifact_validation():
    """Test artifact validation."""
    from app.core.validation_boundary import validate_artifact_data
    
    # Invalid artifact
    is_valid, error = validate_artifact_data({})
    assert not is_valid
    assert 'required' in error.lower()
    
    # Valid artifact
    valid_artifact = {
        'id': 1,
        'document_version_id': 1,
        'artifact_type': 'html',
        'raw_path': 's3://bucket/artifact',
        'content_hash': 'abc123'
    }
    is_valid, error = validate_artifact_data(valid_artifact)
    assert is_valid


def test_safe_get_nested():
    """Test safe nested dictionary access."""
    from app.core.validation_boundary import safe_get_nested
    
    data = {"items": [{"name": "test"}]}
    
    result = safe_get_nested(data, "items.0.name")
    assert result == "test"
    
    result = safe_get_nested(data, "items.5.name", "default")
    assert result == "default"


def test_pagination_validation():
    """Test pagination parameter validation."""
    from app.core.validation_boundary import validate_pagination_params
    
    is_valid, page, page_size = validate_pagination_params(0, 1000)
    assert page == 1  # Should normalize to 1
    assert page_size == 500  # Should cap at 500
