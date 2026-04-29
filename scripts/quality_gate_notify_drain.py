#!/usr/bin/env python3
"""Drain local quality gate notification queue to webhook."""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx

from scripts.quality_gate_delivery_queue import list_queue_files, load_payload, remove_payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Drain queued quality gate notifications")
    parser.add_argument("--webhook-url", default=os.getenv("QUALITY_GATE_WEBHOOK_URL", ""))
    parser.add_argument("--spool-dir", default=".artifacts/quality_gate_notify_queue")
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--allow-missing-webhook", action="store_true")
    parser.add_argument("--soft-fail", action="store_true", help="Always return 0 on delivery errors")
    return parser


def _post_with_retries(*, webhook_url: str, payload: dict, retries: int, timeout: float) -> None:
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
    raise RuntimeError(f"drain delivery failed after {retries + 1} attempts: {last_error}")


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    webhook_url = (args.webhook_url or "").strip()
    if not webhook_url:
        if args.allow_missing_webhook:
            print("quality-gate drain: webhook URL missing; skipping")
            return 0
        print("quality-gate drain: webhook URL missing", file=sys.stderr)
        return 2

    queue_files = list_queue_files(args.spool_dir)
    if not queue_files:
        print("quality-gate drain: queue is empty")
        return 0

    processed = 0
    delivered = 0
    failed = 0
    for queue_file in queue_files[: max(0, args.max_items)]:
        processed += 1
        try:
            payload = load_payload(queue_file)
            _post_with_retries(
                webhook_url=webhook_url,
                payload=payload,
                retries=max(0, args.retries),
                timeout=args.timeout,
            )
            remove_payload(queue_file)
            delivered += 1
            print(f"quality-gate drain: delivered {queue_file.name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"quality-gate drain: failed {queue_file.name}: {exc}", file=sys.stderr)
            break

    print(
        f"quality-gate drain summary: processed={processed} delivered={delivered} failed={failed}"
    )

    if failed > 0 and not args.soft_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
