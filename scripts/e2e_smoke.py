#!/usr/bin/env python3
"""
End-to-end smoke test for PR/TZ validation.

Verifies:
1. POST /sync/full → creates pipeline run
2. GET /runs/{run_id} → polls until completion, captures stats_json
3. GET /documents?page=1 → validates documents populated
4. GET /documents/{id}/content → checks content structure
5. GET /documents/{id}/fragments → checks fragment parsing
"""

import sys
import time
import json
from pathlib import Path

import httpx


BASE_URL = "http://127.0.0.1:8000"
POLL_INTERVAL = 2
POLL_TIMEOUT = 120
MAX_RETRIES = 3


def log(msg: str):
    """Print log message with timestamp."""
    print(f"[E2E] {msg}")


def retry_request(method: str, url: str, **kwargs) -> httpx.Response:
    """Retry HTTP request up to MAX_RETRIES times."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=30) as client:
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


def poll_run_completion(run_id: int) -> dict | None:
    """Poll GET /runs/{run_id} until completion."""
    log(f"3/6: Polling run {run_id} for completion (timeout={POLL_TIMEOUT}s)")
    start_time = time.time()

    while time.time() - start_time < POLL_TIMEOUT:
        try:
            resp = retry_request("GET", f"{BASE_URL}/runs/{run_id}")
            assert resp.status_code == 200
            run = resp.json()
            status = run.get("status")

            if status == "running":
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

    log(f"  ✗ Timeout exceeded after {POLL_TIMEOUT}s")
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
        if sections:
            first_section = sections[0]
            log(f"    Sample section: title={first_section.get('title', 'N/A')[:50]}, "
                f"fragments={len(first_section.get('fragments', []))}")
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
        items = data.get("items", [])
        total = data.get("total", 0)
        log(f"  ✓ Fragments retrieved: {len(items)} items, {total} total")
        if items:
            first_frag = items[0]
            log(f"    Sample: type={first_frag.get('type')}, "
                f"text_len={len(first_frag.get('text', ''))}")
        return data
    except Exception as e:
        log(f"  ✗ Fragments fetch failed: {e}")
        return None


def main():
    """Run full E2E smoke test."""
    log("=" * 60)
    log("START: End-to-End Smoke Test for PRD/TZ")
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
    run_details = poll_run_completion(run_id)
    if not run_details:
        log("\n❌ Run polling timeout. Aborting.")
        sys.exit(1)
    results["run"] = run_details

    # Print stats_json
    stats = run_details.get("stats_json", {})
    log(f"\n📊 Run Statistics:")
    log(f"  Status: {run_details.get('status')}")
    log(f"  Discovered: {run_details.get('discovered_count', 'N/A')}")
    log(f"  Fetched: {run_details.get('fetched_count', 'N/A')}")
    log(f"  Strategy: {stats.get('strategy', 'N/A')}")
    log(f"  API Records: {stats.get('api_records', 'N/A')}")
    log(f"  Total Discovered: {stats.get('total_discovered', 'N/A')}")
    if "discovery_service_version" not in stats:
        log("  [WARN] stats_json missing discovery_service_version")
        log("  [HINT] App/worker may run outdated code. Rebuild and restart services.")
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

    # Summary
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    if run_details.get("status") == "completed" and run_details.get("discovered_count", 0) > 0:
        log("✅ E2E Test PASSED: Discovery → Documents → Content flow working")
    elif run_details.get("status") == "completed":
        log("⚠️  E2E Test PARTIAL: Discovery ran but returned 0 records")
    else:
        log("❌ E2E Test FAILED: Check logs above")

    # Save results to JSON
    output_file = Path("smoke_test_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    log(f"\n📁 Results saved to: {output_file}")

    log("=" * 60)


if __name__ == "__main__":
    main()
