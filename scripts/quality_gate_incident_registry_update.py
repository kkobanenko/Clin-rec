#!/usr/bin/env python3
"""Fetch incident report and persist it into local registry."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx

from app.services.quality_gate_incident_registry import QualityGateIncidentRegistryService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persist quality gate incident report into local registry")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--max-versions", type=int, default=100)
    parser.add_argument("--high-skip-threshold", type=float, default=0.8)
    parser.add_argument("--max-avg-skip-rate", type=float, default=0.75)
    parser.add_argument("--min-candidate-pairs", type=int, default=1)
    parser.add_argument("--spool-dir", default=os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"))
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--registry-dir", default=os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"))
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--source", default="release_ready_check")
    parser.add_argument("--json", action="store_true")
    return parser


def _fetch_incident_report(*, api_base: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    response = httpx.get(
        f"{api_base.rstrip('/')}/outputs/quality-gate/incident",
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("incident endpoint returned non-object payload")
    return payload


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    params = {
        "max_versions": args.max_versions,
        "high_skip_threshold": args.high_skip_threshold,
        "max_avg_skip_rate": args.max_avg_skip_rate,
        "min_candidate_pairs": args.min_candidate_pairs,
        "spool_dir": args.spool_dir,
        "max_items": args.max_items,
    }

    try:
        incident = _fetch_incident_report(api_base=args.api_base, params=params, timeout=args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"incident-registry update: cannot fetch incident report: {exc}", file=sys.stderr)
        return 2

    service = QualityGateIncidentRegistryService()
    try:
        record_path = service.append_incident(
            registry_dir=args.registry_dir,
            incident=incident,
            source=args.source,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"incident-registry update: persist failed: {exc}", file=sys.stderr)
        return 1

    report = service.generate_report(registry_dir=args.registry_dir, max_items=args.max_items)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))

    print(
        "incident-registry update: persisted "
        f"severity={incident.get('severity')} "
        f"should_escalate={incident.get('should_escalate')} "
        f"path={record_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
