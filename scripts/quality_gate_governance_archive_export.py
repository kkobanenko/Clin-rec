#!/usr/bin/env python3
"""Export governance archive bundle to tar.gz."""

from __future__ import annotations

import argparse
import json
import os
import sys

from app.services.quality_gate_governance_archive import QualityGateGovernanceArchiveService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export governance archive bundle")
    parser.add_argument("--output-dir", default=os.getenv("QUALITY_GATE_GOVERNANCE_ARCHIVE_DIR", ".artifacts/quality_gate_governance_archive"))
    parser.add_argument("--max-versions", type=int, default=100)
    parser.add_argument("--high-skip-threshold", type=float, default=0.8)
    parser.add_argument("--max-avg-skip-rate", type=float, default=0.75)
    parser.add_argument("--min-candidate-pairs", type=int, default=1)
    parser.add_argument("--spool-dir", default=os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"))
    parser.add_argument("--registry-dir", default=os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"))
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--baseline-window", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    service = QualityGateGovernanceArchiveService()

    try:
        report = service.export_archive(
            output_dir=args.output_dir,
            max_versions=args.max_versions,
            high_skip_threshold=args.high_skip_threshold,
            max_avg_skip_rate=args.max_avg_skip_rate,
            min_candidate_pairs=args.min_candidate_pairs,
            spool_dir=args.spool_dir,
            registry_dir=args.registry_dir,
            max_items=args.max_items,
            baseline_window=args.baseline_window,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"governance-archive export: FAILED: {exc}", file=sys.stderr)
        return 1

    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    print(
        "governance-archive export: OK "
        f"archive_path={payload.get('archive_path')} file_count={payload.get('file_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
