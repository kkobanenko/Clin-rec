#!/usr/bin/env python3
"""Send quality gate verdict to an external webhook endpoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

import httpx


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notify external webhook about quality gate verdict")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--webhook-url", default=os.getenv("QUALITY_GATE_WEBHOOK_URL", ""))
    parser.add_argument("--max-versions", type=int, default=100)
    parser.add_argument("--high-skip-threshold", type=float, default=0.8)
    parser.add_argument("--max-avg-skip-rate", type=float, default=0.75)
    parser.add_argument("--min-candidate-pairs", type=int, default=1)
    parser.add_argument("--runtime-profile", default=os.getenv("RUNTIME_PROFILE", "unknown"))
    parser.add_argument("--operator", default=os.getenv("OPERATOR_NAME", os.getenv("USER", "unknown")))
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-missing-webhook",
        action="store_true",
        help="Exit 0 when webhook URL is not provided",
    )
    return parser


def _fetch_gate_report(
    *,
    api_base: str,
    max_versions: int,
    high_skip_threshold: float,
    max_avg_skip_rate: float,
    min_candidate_pairs: int,
    timeout: float,
) -> dict[str, Any]:
    params = {
        "max_versions": max_versions,
        "high_skip_threshold": high_skip_threshold,
        "max_avg_skip_rate": max_avg_skip_rate,
        "min_candidate_pairs": min_candidate_pairs,
    }
    response = httpx.get(
        f"{api_base.rstrip('/')}/outputs/quality-gate",
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid quality gate response payload")
    return payload


def _build_notification_payload(
    *,
    gate_report: dict[str, Any],
    api_base: str,
    runtime_profile: str,
    operator: str,
) -> dict[str, Any]:
    verdict = str(gate_report.get("verdict") or "unknown")
    summary = str(gate_report.get("summary") or "")
    rules = gate_report.get("rules") if isinstance(gate_report.get("rules"), list) else []
    return {
        "event": "quality_gate_verdict",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_profile": runtime_profile,
        "operator": operator,
        "api_base": api_base,
        "verdict": verdict,
        "summary": summary,
        "rules_total": len(rules),
        "rules_failed": len([r for r in rules if isinstance(r, dict) and r.get("status") == "fail"]),
        "rules_warn": len([r for r in rules if isinstance(r, dict) and r.get("status") == "warn"]),
        "gate_report": gate_report,
    }


def _post_with_retries(
    *,
    webhook_url: str,
    payload: dict[str, Any],
    retries: int,
    timeout: float,
) -> None:
    attempt = 0
    last_error: Exception | None = None
    while attempt <= retries:
        attempt += 1
        try:
            response = httpx.post(webhook_url, json=payload, timeout=timeout)
            response.raise_for_status()
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt > retries:
                break
            time.sleep(0.5 * attempt)
    raise RuntimeError(f"Webhook notification failed after {retries + 1} attempts: {last_error}")


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    webhook_url = (args.webhook_url or "").strip()
    if not webhook_url:
        message = "quality-gate notify: webhook URL is missing"
        if args.allow_missing_webhook:
            print(f"{message}; skipping")
            return 0
        print(message, file=sys.stderr)
        return 2

    try:
        gate_report = _fetch_gate_report(
            api_base=args.api_base,
            max_versions=args.max_versions,
            high_skip_threshold=args.high_skip_threshold,
            max_avg_skip_rate=args.max_avg_skip_rate,
            min_candidate_pairs=args.min_candidate_pairs,
            timeout=args.timeout,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"quality-gate notify: cannot fetch gate report: {exc}", file=sys.stderr)
        return 2

    payload = _build_notification_payload(
        gate_report=gate_report,
        api_base=args.api_base,
        runtime_profile=args.runtime_profile,
        operator=args.operator,
    )

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        _post_with_retries(
            webhook_url=webhook_url,
            payload=payload,
            retries=max(0, args.retries),
            timeout=args.timeout,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"quality-gate notify: webhook post failed: {exc}", file=sys.stderr)
        return 1

    print(
        "quality-gate notify: sent "
        f"verdict={payload.get('verdict')} "
        f"failed_rules={payload.get('rules_failed')} warn_rules={payload.get('rules_warn')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())