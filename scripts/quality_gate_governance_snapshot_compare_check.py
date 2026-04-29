#!/usr/bin/env python3
"""CLI checker for governance snapshot compare."""

from __future__ import annotations

import argparse
import json
import sys

from app.services.quality_gate_governance_snapshot_compare import QualityGateGovernanceSnapshotCompareService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare governance snapshots")
    parser.add_argument("--baseline-file", required=True)
    parser.add_argument("--candidate-file", required=True)
    parser.add_argument("--fail-on-status", default="degrading", choices=["degrading", "none"])
    parser.add_argument("--json", action="store_true")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    service = QualityGateGovernanceSnapshotCompareService()

    try:
        report = service.compare(baseline_file=args.baseline_file, candidate_file=args.candidate_file)
    except Exception as exc:  # noqa: BLE001
        print(f"snapshot-compare check: FAILED: {exc}", file=sys.stderr)
        return 2

    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    print(
        "snapshot-compare check: "
        f"status={payload.get('status')} score_delta={payload.get('score_delta')} ratio_delta={payload.get('escalated_ratio_delta')}"
    )

    if args.fail_on_status == "degrading" and payload.get("status") == "degrading":
        print("snapshot-compare check: FAILED (degrading)", file=sys.stderr)
        return 1

    print("snapshot-compare check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
