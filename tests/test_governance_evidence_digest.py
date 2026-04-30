"""Tests for governance evidence digest service."""

from __future__ import annotations

from app.services.governance_evidence_digest import GovernanceEvidenceDigestService


def test_digest_strong_verdict():
    svc = GovernanceEvidenceDigestService()
    report = svc.build_digest(
        [
            {"source": "score", "title": "Score", "status": "pass", "weight": 0.5},
            {"source": "trends", "title": "Trends", "status": "pass", "weight": 0.5},
        ]
    )
    assert report.verdict == "strong"


def test_digest_moderate_verdict():
    svc = GovernanceEvidenceDigestService()
    report = svc.build_digest(
        [
            {"source": "score", "title": "Score", "status": "warn", "weight": 0.5},
            {"source": "trends", "title": "Trends", "status": "pass", "weight": 0.5},
        ]
    )
    assert report.verdict in {"moderate", "strong"}


def test_digest_markdown_contains_sections():
    svc = GovernanceEvidenceDigestService()
    report = svc.build_digest(
        [
            {"source": "score", "title": "Score", "status": "fail", "weight": 1.0},
        ]
    )
    md = report.to_markdown()
    assert "# Governance Evidence Digest" in md
    assert "## Entries" in md
