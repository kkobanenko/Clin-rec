#!/usr/bin/env python3
"""CLI checker for governance trends."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check governance trends")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--max-versions", type=int, default=100)
    parser.add_argument("--high-skip-threshold", type=float, default=0.8)
    parser.add_argument("--max-avg-skip-rate", type=float, default=0.75)
    parser.add_argument("--min-candidate-pairs", type=int, default=1)
    parser.add_argument("--spool-dir", default=os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"))
    parser.add_argument("--registry-dir", default=os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"))
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--baseline-window", type=int, default=10)
    parser.add_argument("--fail-on-status", default="degrading", choices=["degrading", "none"])
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true")
    return parser


def _fetch_report(*, api_base: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    response = httpx.get(
        f"{api_base.rstrip('/')}/outputs/quality-gate/governance-trends",
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("governance-trends endpoint returned non-object payload")
    return payload


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    params = {
        "max_versions": args.max_versions,
        "high_skip_threshold": args.high_skip_threshold,
        "max_avg_skip_rate": args.max_avg_skip_rate,
        "min_candidate_pairs": args.min_candidate_pairs,
        "spool_dir": args.spool_dir,
        "registry_dir": args.registry_dir,
        "max_items": args.max_items,
        "baseline_window": args.baseline_window,
    }

    try:
        payload = _fetch_report(api_base=args.api_base, params=params, timeout=args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"governance-trends check: API request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    status = str(payload.get("status") or "unknown")
    score_delta = float(payload.get("score_delta") or 0.0)
    ratio_delta = float(payload.get("escalated_ratio_delta") or 0.0)
    print(
        "governance-trends check: "
        f"status={status} score_delta={score_delta:.2f} escalated_ratio_delta={ratio_delta:.4f}"
    )

    if args.fail_on_status == "degrading" and status == "degrading":
        print("governance-trends check: FAILED (degrading trend)", file=sys.stderr)
        return 1

    print("governance-trends check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
