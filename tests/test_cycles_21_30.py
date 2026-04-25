"""Tests for release, quality, and API response utilities (cycles 21-30)."""


def test_output_release_manager():
    """Test output release management."""
    from app.core.release_and_reports import OutputReleaseManager
    
    release_req = OutputReleaseManager.create_release_request(1, "reviewer1")
    assert release_req['output_id'] == 1
    assert release_req['status'] == 'requested'


def test_report_generators():
    """Test report generation."""
    from app.core.release_and_reports import ReportGenerator
    
    metrics = {"coverage": 95}
    p0_report = ReportGenerator.generate_p0_report(metrics)
    assert p0_report['report_type'] == 'P0_completion'


def test_quality_metrics():
    """Test quality metrics calculation."""
    from app.core.quality_audit_incidents import QualityMetrics
    
    quality = QualityMetrics.calculate_extraction_quality(100, 95)
    assert quality == 95.0


def test_audit_trail_logging():
    """Test audit trail logging."""
    from app.core.quality_audit_incidents import AuditTrail
    
    log = AuditTrail.log_action("op1", "view", "document", 1)
    assert log['operator_id'] == "op1"
    assert log['action_type'] == "view"


def test_incident_lookup():
    """Test incident directory lookup."""
    from app.core.quality_audit_incidents import IncidentDirectory
    
    incident = IncidentDirectory.lookup_incident("artifact_fetch_timeout")
    assert 'resolution' in incident


def test_api_response_helpers():
    """Test API response generation."""
    from app.core.api_responses import APIResponse
    
    success_resp = APIResponse.success({"key": "value"})
    assert success_resp['success'] is True
    
    error_resp = APIResponse.error("NOT_FOUND", "Resource not found")
    assert error_resp['success'] is False


def test_error_catalog():
    """Test error catalog."""
    from app.core.api_responses import ErrorCatalog
    
    error = ErrorCatalog.get_error("DOCUMENT_NOT_FOUND")
    assert error['status'] == 404
