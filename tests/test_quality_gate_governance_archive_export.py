"""Tests for scripts/quality_gate_governance_archive_export.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_governance_archive_export


class _Report:
    def to_dict(self):
        return {
            "archive_path": "/tmp/archive.tar.gz",
            "file_count": 4,
        }


def test_archive_export_script_ok(capsys):
    with patch(
        "scripts.quality_gate_governance_archive_export.QualityGateGovernanceArchiveService.export_archive",
        return_value=_Report(),
    ):
        code = quality_gate_governance_archive_export.run(["--output-dir", "/tmp/a"])
    assert code == 0


def test_archive_export_script_fail(capsys):
    with patch(
        "scripts.quality_gate_governance_archive_export.QualityGateGovernanceArchiveService.export_archive",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_governance_archive_export.run(["--output-dir", "/tmp/a"])
    assert code == 1
