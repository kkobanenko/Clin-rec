#!/usr/bin/env python3
"""
End-to-end smoke test for PR/TZ validation.

Verifies:
1. POST /sync/full → creates pipeline run
2. GET /runs/{run_id} → polls until completion, captures stats_json
3. GET /documents?page=1 → validates documents populated
4. GET /documents/{id}/content → checks content structure
5. GET /documents/{id}/fragments → checks fragment parsing
6. GET /matrix/pair-evidence?document_version_id=... → checks downstream candidate readiness
7. GET /matrix/cell → checks matrix consistency when an active scoring model exists
"""

import sys
import time
import json
import argparse
from pathlib import Path

import httpx


BASE_URL = "http://127.0.0.1:8000"
POLL_INTERVAL = 2
DEFAULT_STRUCTURAL_POLL_TIMEOUT = 120
DEFAULT_QUALITY_POLL_TIMEOUT = 300
MAX_RETRIES = 3
REQUIRED_STATS_KEYS = {
    "discovery_service_version",
    "run_type",
    "wall_time_seconds",
    "total_discovered",
    "duplicates_detected",
    "coverage_percent",
}

VALID_MODES = {"structural", "quality"}


def log(msg: str):
    """Print log message with timestamp."""
    print(f"[E2E] {msg}")


def retry_request(method: str, url: str, **kwargs) -> httpx.Response:
    """Retry HTTP request up to MAX_RETRIES times."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=30, trust_env=False) as client:
                if method.upper() == "GET":
                    resp = client.get(url, **kwargs)
                elif method.upper() == "POST":
                    resp = client.post(url, **kwargs)
                else:
                    raise ValueError(f"Unknown method {method}")
            
            # Log full error response if status indicates failure
            if resp.status_code >= 400:
                try:
                    error_body = resp.json()
                except Exception:
                    error_body = resp.text[:500]
                log(f"  [DEBUG] HTTP {resp.status_code} response: {error_body}")
            
            resp.raise_for_status()
            return resp
        except Exception as e:
            log(f"Attempt {attempt}/{MAX_RETRIES} failed: {str(e)[:200]}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2)
    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts")


def test_health():
    """Verify API is healthy."""
    log("1/6: Testing /health endpoint")
    try:
        resp = retry_request("GET", f"{BASE_URL}/health")
        assert resp.status_code == 200
        log("  ✓ API is healthy")
        return True
    except Exception as e:
        log(f"  ✗ Health check failed: {e}")
        log(f"\n⚠️  API not available at {BASE_URL}")
        log("   Try: docker compose up -d && docker compose logs -f crin_app")
        log("   Or:  .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return False


def test_sync_full() -> dict | None:
    """Trigger POST /sync/full and return run details."""
    log("2/6: Triggering POST /sync/full")
    try:
        resp = retry_request("POST", f"{BASE_URL}/sync/full")
        assert resp.status_code == 202
        data = resp.json()
        assert "run_id" in data
        run_id = data["run_id"]
        log(f"  ✓ Pipeline run created: {run_id}")
        return {"run_id": run_id}
    except Exception as e:
        log(f"  ✗ Sync trigger failed: {e}")
        return None


def poll_run_completion(run_id: int, poll_timeout: int) -> dict | None:
    """Poll GET /runs/{run_id} until completion."""
    log(f"3/6: Polling run {run_id} for completion (timeout={poll_timeout}s)")
    start_time = time.time()

    while time.time() - start_time < poll_timeout:
        try:
            resp = retry_request("GET", f"{BASE_URL}/runs/{run_id}")
            assert resp.status_code == 200
            run = resp.json()
            status = run.get("status")

            if status in ("pending", "running"):
                elapsed = int(time.time() - start_time)
                log(f"  ⏳ Status: {status} ({elapsed}s elapsed)")
                time.sleep(POLL_INTERVAL)
                continue

            if status in ("completed", "failed"):
                log(f"  ✓ Run finished with status: {status}")
                return run

            log(f"  ? Unknown status: {status}")
            return run

        except Exception as e:
            log(f"  ✗ Poll failed: {e}")
            time.sleep(POLL_INTERVAL)

    log(f"  ✗ Timeout exceeded after {poll_timeout}s")
    log("  [HINT] Queue may be busy with long-running fetch/normalize tasks; retry with a higher --poll-timeout.")
    return None


def test_documents_list() -> dict | None:
    """Fetch GET /documents?page=1 and validate presence."""
    log("4/6: Testing GET /documents?page=1")
    try:
        resp = retry_request("GET", f"{BASE_URL}/documents?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", [])
        total = data.get("total", 0)
        log(f"  ✓ Documents retrieved: {len(items)} items, {total} total")
        if items:
            first_doc = items[0]
            log(f"    Sample: ID={first_doc.get('id')}, title={first_doc.get('title', 'N/A')[:50]}")
            return first_doc
        return None
    except Exception as e:
        log(f"  ✗ Documents fetch failed: {e}")
        return None


def test_document_content(doc_id: int) -> dict | None:
    """Fetch GET /documents/{id}/content and validate structure."""
    log(f"5/6: Testing GET /documents/{doc_id}/content")
    try:
        resp = retry_request("GET", f"{BASE_URL}/documents/{doc_id}/content")
        assert resp.status_code == 200
        data = resp.json()
        sections = data.get("sections", [])
        log(f"  ✓ Content retrieved: {len(sections)} sections")
        pipeline_outcome = data.get("pipeline_outcome") or {}
        if pipeline_outcome:
            log(
                f"    Pipeline outcome: stage={pipeline_outcome.get('stage')} "
                f"status={pipeline_outcome.get('status')} reason={pipeline_outcome.get('reason_code')}"
            )
        if sections:
            first_section = sections[0]
            log(
                f"    Sample section: title={first_section.get('section_title', 'N/A')[:50]}, "
                f"order={first_section.get('section_order')}"
            )
        return data
    except Exception as e:
        log(f"  ✗ Content fetch failed: {e}")
        return None


def test_document_fragments(doc_id: int) -> dict | None:
    """Fetch GET /documents/{id}/fragments and validate structure."""
    log(f"6/6: Testing GET /documents/{doc_id}/fragments")
    try:
        resp = retry_request("GET", f"{BASE_URL}/documents/{doc_id}/fragments?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("fragments", [])
        total = data.get("total", 0)
        log(f"  ✓ Fragments retrieved: {len(items)} items, {total} total")
        pipeline_outcome = data.get("pipeline_outcome") or {}
        if pipeline_outcome:
            log(
                f"    Pipeline outcome: stage={pipeline_outcome.get('stage')} "
                f"status={pipeline_outcome.get('status')} reason={pipeline_outcome.get('reason_code')}"
            )
        if items:
            first_frag = items[0]
            log(f"    Sample: type={first_frag.get('fragment_type')}, "
                f"text_len={len(first_frag.get('fragment_text', ''))}")
        return data
    except Exception as e:
        log(f"  ✗ Fragments fetch failed: {e}")
        return None


def test_pair_evidence(version_id: int) -> dict | None:
    """Fetch GET /matrix/pair-evidence for a specific document version."""
    log(f"7/7: Testing GET /matrix/pair-evidence for version {version_id}")
    try:
        resp = retry_request(
            "GET",
            f"{BASE_URL}/matrix/pair-evidence?document_version_id={version_id}&page=1&page_size=10",
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", [])
        total = data.get("total", 0)
        log(f"  ✓ Pair evidence retrieved: {len(items)} items, {total} total")
        if items:
            sample = items[0]
            log(
                f"    Sample pair evidence: from={sample.get('molecule_from_id')} "
                f"to={sample.get('molecule_to_id')} relation={sample.get('relation_type')}"
            )
        return data
    except Exception as e:
        log(f"  ✗ Pair evidence fetch failed: {e}")
        return None


def get_active_scoring_model() -> dict | None:
    """Fetch scoring models and return the active one if present."""
    try:
        resp = retry_request("GET", f"{BASE_URL}/matrix/models")
        assert resp.status_code == 200
        items = resp.json()
        return next((item for item in items if item.get("is_active") is True), None)
    except Exception as e:
        log(f"  ✗ Active scoring model lookup failed: {e}")
        return None


def test_matrix_cell(model_version_id: int, molecule_from_id: int, molecule_to_id: int) -> dict | None:
    """Fetch GET /matrix/cell for a specific scored pair."""
    log(
        f"8/8: Testing GET /matrix/cell for pair {molecule_from_id}->{molecule_to_id} "
        f"under model {model_version_id}"
    )
    try:
        resp = retry_request(
            "GET",
            f"{BASE_URL}/matrix/cell?molecule_from_id={molecule_from_id}&molecule_to_id={molecule_to_id}&model_version_id={model_version_id}",
        )
        assert resp.status_code == 200
        data = resp.json()
        cell = data.get("cell") or {}
        evidence = data.get("evidence") or []
        log(
            f"  ✓ Matrix cell retrieved: score={cell.get('substitution_score')} "
            f"confidence={cell.get('confidence_score')} evidence={len(evidence)}"
        )
        return data
    except Exception as e:
        log(f"  ✗ Matrix cell fetch failed: {e}")
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CR Intelligence Platform E2E smoke")
    parser.add_argument(
        "--mode",
        choices=sorted(VALID_MODES),
        default="structural",
        help="Smoke mode: structural validates lifecycle/contracts, quality also requires non-empty content.",
    )
    parser.add_argument(
        "--poll-timeout",
        type=int,
        default=None,
        help="Override polling timeout in seconds. Defaults to 120 for structural and 300 for quality.",
    )
    return parser.parse_args()


def main():
    """Run full E2E smoke test."""
    args = parse_args()
    mode = args.mode
    poll_timeout = args.poll_timeout
    if poll_timeout is None:
        poll_timeout = (
            DEFAULT_QUALITY_POLL_TIMEOUT if mode == "quality" else DEFAULT_STRUCTURAL_POLL_TIMEOUT
        )
    log("=" * 60)
    log(f"START: End-to-End Smoke Test for PRD/TZ (mode={mode})")
    log("=" * 60)

    results = {}

    # 1. Health check
    if not test_health():
        log("\n❌ API not available. Cannot proceed.")
        sys.exit(1)

    # 2. Trigger sync
    sync_result = test_sync_full()
    if not sync_result:
        log("\n❌ Sync trigger failed. Aborting.")
        sys.exit(1)
    results["sync"] = sync_result

    # 3. Poll for completion
    run_id = sync_result["run_id"]
    run_details = poll_run_completion(run_id, poll_timeout)
    if not run_details:
        log("\n❌ Run polling timeout. Aborting.")
        sys.exit(1)
    results["run"] = run_details

    # Print stats_json
    stats = run_details.get("stats_json") or {}
    log(f"\n📊 Run Statistics:")
    log(f"  Status: {run_details.get('status')}")
    log(f"  Discovered: {run_details.get('discovered_count', 'N/A')}")
    log(f"  Fetched: {run_details.get('fetched_count', 'N/A')}")
    log(f"  Strategy: {stats.get('strategy', 'N/A')}")
    log(f"  API Records: {stats.get('api_records', 'N/A')}")
    log(f"  Total Discovered: {stats.get('total_discovered', 'N/A')}")
    missing_stats_keys = sorted(REQUIRED_STATS_KEYS - set(stats.keys()))
    if missing_stats_keys:
        log(f"  [ERROR] stats_json missing required fields: {', '.join(missing_stats_keys)}")
        log("  [HINT] Ensure API/worker run aligned versions and discovery v2 metrics are enabled.")
    if stats.get("strategy") in (None, "unknown", "N/A") and stats.get("total_discovered", 0) == 0:
        log("  [HINT] Discovery found 0 records with unknown strategy.")
        log("  [HINT] Check worker logs and API reachability to apicr.minzdrav.gov.ru.")

    # 4. Fetch documents
    first_doc = test_documents_list()
    if not first_doc:
        log("\n⚠️  No documents found. Skipping content/fragment tests.")
        results["documents"] = None
        results["content"] = None
        results["fragments"] = None
    else:
        doc_id = first_doc.get("id")
        results["documents"] = first_doc

        # 5. Fetch content
        content = test_document_content(doc_id)
        results["content"] = content

        # 6. Fetch fragments
        fragments = test_document_fragments(doc_id)
        results["fragments"] = fragments

        pair_evidence = None
        matrix_cell = None
        version_id = (content or {}).get("version_id")
        if mode == "quality" and version_id:
            pair_evidence = test_pair_evidence(version_id)
            active_model = get_active_scoring_model()
            evidence_items = (pair_evidence or {}).get("items") or []
            if active_model and evidence_items:
                first_evidence = evidence_items[0]
                matrix_cell = test_matrix_cell(
                    active_model["id"],
                    first_evidence["molecule_from_id"],
                    first_evidence["molecule_to_id"],
                )
        results["pair_evidence"] = pair_evidence
        results["matrix_cell"] = matrix_cell

    # Summary
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    status = run_details.get("status")
    discovered = run_details.get("discovered_count", 0)
    docs_total = 0
    if results.get("documents"):
        docs_total = 1

    content_sections = len((results.get("content") or {}).get("sections", []))
    fragments_total = (results.get("fragments") or {}).get("total", 0)
    pair_evidence_total = (results.get("pair_evidence") or {}).get("total", 0)
    matrix_cell_present = bool((results.get("matrix_cell") or {}).get("cell"))
    content_outcome = (results.get("content") or {}).get("pipeline_outcome") or {}
    quality_pass = True
    if mode == "quality" and discovered > 0:
        active_model = get_active_scoring_model()
        matrix_ok = True if active_model is None else matrix_cell_present
        quality_pass = bool(content_sections > 0 and fragments_total > 0 and pair_evidence_total > 0 and matrix_ok)

    if status == "completed" and not missing_stats_keys and (mode != "quality" or quality_pass):
        log("✅ E2E Test PASSED")
        if mode == "structural":
            log("ℹ️  Structural smoke validated lifecycle, routing, and observability contract")
        else:
            log("ℹ️  Quality smoke validated non-empty content, fragments, and downstream pair evidence for checked document")
        if discovered == 0:
            log("ℹ️  Completed run with discovered_count=0 is valid for structural smoke checks")
        if docs_total == 0:
            log("ℹ️  No documents in this run context; content/fragment checks may be skipped")
            if mode == "quality" and discovered > 0:
                log("❌ Quality smoke requires at least one checked document when discovered_count > 0")
                sys.exit(1)
    elif status == "completed":
        if missing_stats_keys:
            log("❌ E2E Test FAILED: completed run missing required stats_json fields")
        elif mode == "quality":
            log("❌ E2E Test FAILED: quality gate did not pass")
            log(
                "ℹ️  Quality details: "
                f"sections={content_sections}, fragments={fragments_total}, pair_evidence={pair_evidence_total}, matrix_cell={matrix_cell_present}, "
                f"outcome_stage={content_outcome.get('stage')}, "
                f"outcome_status={content_outcome.get('status')}, "
                f"reason={content_outcome.get('reason_code')}"
            )
        else:
            log("❌ E2E Test FAILED: completed run failed structural expectations")
        sys.exit(1)
    else:
        log("❌ E2E Test FAILED: Check logs above")
        sys.exit(1)

    # Save results to JSON
    output_file = Path("smoke_test_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    log(f"\n📁 Results saved to: {output_file}")

    log("=" * 60)


if __name__ == "__main__":
    main()
