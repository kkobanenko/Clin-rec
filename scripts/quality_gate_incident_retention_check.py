#!/usr/bin/env python3
"""Retention check and optional cleanup for incident registry."""

from __future__ import annotations

import argparse
import json
import os
import sys

from app.services.quality_gate_incident_retention import QualityGateIncidentRetentionService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Incident registry retention check")
    parser.add_argument(
        "--registry-dir",
        default=os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"),
    )
    parser.add_argument("--max-items", type=int, default=int(os.getenv("QUALITY_GATE_INCIDENT_RETENTION_MAX_ITEMS", "1000")))
    parser.add_argument("--max-age-days", type=int, default=int(os.getenv("QUALITY_GATE_INCIDENT_RETENTION_MAX_AGE_DAYS", "30")))
    parser.add_argument("--apply", action="store_true", help="Apply retention cleanup instead of dry-run")
    parser.add_argument("--fail-on-removals", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    service = QualityGateIncidentRetentionService()

    try:
        if args.apply:
            report = service.apply_policy(
                registry_dir=args.registry_dir,
                max_items=args.max_items,
                max_age_days=args.max_age_days,
            )
        else:
            report = service.evaluate_policy(
                registry_dir=args.registry_dir,
                max_items=args.max_items,
                max_age_days=args.max_age_days,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"incident-retention check: failed: {exc}", file=sys.stderr)
        return 2

    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    print(
        "incident-retention check: "
        f"before={payload.get('total_items_before')} "
        f"after={payload.get('total_items_after')} "
        f"removed={payload.get('removed_items')} "
        f"dry_run={payload.get('dry_run')}"
    )

    if args.fail_on_removals and int(payload.get("removed_items") or 0) > 0:
        print("incident-retention check: FAILED (removals required)", file=sys.stderr)
        return 1

    print("incident-retention check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
