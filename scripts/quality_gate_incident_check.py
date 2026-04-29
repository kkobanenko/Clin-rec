#!/usr/bin/env python3
"""CLI check for quality gate incident escalation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check quality gate incident escalation report")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--max-versions", type=int, default=100)
    parser.add_argument("--high-skip-threshold", type=float, default=0.8)
    parser.add_argument("--max-avg-skip-rate", type=float, default=0.75)
    parser.add_argument("--min-candidate-pairs", type=int, default=1)
    parser.add_argument("--spool-dir", default=os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"))
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--fail-on-high", action="store_true")
    parser.add_argument("--allow-info", action="store_true")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true")
    return parser


def _fetch_report(*, api_base: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
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
        payload = _fetch_report(api_base=args.api_base, params=params, timeout=args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"incident check: API request failed: {exc}", file=sys.stderr)
        return 2

    should_escalate = bool(payload.get("should_escalate"))
    severity = str(payload.get("severity") or "unknown")
    reason = str(payload.get("reason") or "")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    print(f"incident check: should_escalate={should_escalate} severity={severity}")
    if reason:
        print(f"incident check: reason={reason}")

    if severity == "critical":
        print("incident check: FAILED (critical escalation)", file=sys.stderr)
        return 1
    if severity == "high" and args.fail_on_high:
        print("incident check: FAILED (high escalation policy)", file=sys.stderr)
        return 1
    if severity == "info" and not should_escalate and args.allow_info:
        print("incident check: OK (info accepted by policy)")
        return 0
    if not should_escalate:
        print("incident check: OK")
        return 0
    if severity == "high":
        print("incident check: WARN (high escalation but not configured to fail)")
        return 0

    print("incident check: FAILED (unknown escalation state)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
