"""Tests for governance iteration journal service."""

from __future__ import annotations

from app.services.governance_iteration_journal import GovernanceIterationJournalService


def test_iteration_journal_summary():
    svc = GovernanceIterationJournalService()
    rep = svc.summarize(
        [
            {
                "iteration": 1,
                "started_at": "2026-04-30 23:00:00",
                "completed_at": "2026-04-30 23:10:00",
                "scope": "digest",
                "outcome": "completed",
            },
            {
                "iteration": 2,
                "started_at": "2026-04-30 23:10:00",
                "completed_at": "2026-04-30 23:20:00",
                "scope": "normalizer",
                "outcome": "failed",
            },
        ]
    )
    assert rep["total"] == 2
    assert rep["completed"] == 1
    assert rep["failed"] == 1
