"""Tests for EvidenceService pagination support."""

from app.services.evidence import EvidenceService


def test_evidence_service_has_pagination_methods():
    """Test that EvidenceService supports pagination."""
    service = EvidenceService()
    assert hasattr(service, 'get_evidence_paginated')
    assert callable(service.get_evidence_paginated)


def test_evidence_service_has_counter_methods():
    """Test that EvidenceService has counting methods."""
    service = EvidenceService()
    assert hasattr(service, 'count_evidence_for_context')
    assert hasattr(service, 'count_evidence_for_document')
