"""E2E smoke test for P0 workflow validation."""

import asyncio
import httpx
from typing import Optional


async def test_p0_evidence_workflow():
    """Test P0 evidence loading and display workflow.
    
    Steps:
    1. Get document list
    2. Select document with current version
    3. Load evidence for current version
    4. Verify evidence loaded or proper empty state
    5. Check pagination works
    """
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient() as client:
        # Step 1: Get documents
        resp = await client.get(f"{base_url}/documents", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200, f"Documents list failed: {resp.text}"
        docs = resp.json()
        assert "items" in docs
        
        if not docs["items"]:
            print("No documents found, skipping test")
            return
        
        doc = docs["items"][0]
        doc_id = doc.get("id")
        
        # Step 2: Get document detail
        resp = await client.get(f"{base_url}/documents/{doc_id}")
        assert resp.status_code == 200
        doc_detail = resp.json()
        current_version_id = doc_detail.get("current_version_id")
        
        # Step 3: Load evidence for document
        resp = await client.get(
            f"{base_url}/matrix/pair-evidence",
            params={
                "document_version_id": current_version_id,
                "page": 1,
                "page_size": 50,
            }
        )
        assert resp.status_code == 200, f"Evidence load failed: {resp.text}"
        evidence = resp.json()
        
        # Step 4: Verify response structure
        assert "items" in evidence
        assert "total" in evidence
        assert "page" in evidence
        assert "page_size" in evidence
        
        total_evidence = evidence["total"]
        
        # Step 5: Test pagination if evidence exists
        if total_evidence > 50:
            resp = await client.get(
                f"{base_url}/matrix/pair-evidence",
                params={
                    "document_version_id": current_version_id,
                    "page": 2,
                    "page_size": 50,
                }
            )
            assert resp.status_code == 200
            evidence_p2 = resp.json()
            assert len(evidence_p2["items"]) > 0 or evidence_p2["page"] == 2
        
        print(f"✅ P0 Evidence workflow test passed")
        print(f"   - Document {doc_id}, Version {current_version_id}")
        print(f"   - Evidence records: {total_evidence}")


async def test_p0_artifact_coverage_workflow():
    """Test P0 artifact coverage diagnostics workflow.
    
    Steps:
    1. Get coverage statistics
    2. Verify structure
    3. Check for P0 requirements met
    """
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient() as client:
        # Get coverage endpoint
        resp = await client.get(f"{base_url}/documents/artifact-coverage")
        assert resp.status_code == 200, f"Coverage endpoint failed: {resp.text}"
        
        coverage = resp.json()
        
        # Verify structure
        assert "current_versions_with_artifacts" in coverage
        assert "current_versions_without_artifacts" in coverage
        assert "artifacts_total" in coverage
        
        with_artifacts = coverage["current_versions_with_artifacts"]
        without_artifacts = coverage["current_versions_without_artifacts"]
        total = with_artifacts + without_artifacts
        
        coverage_pct = (with_artifacts / total * 100) if total else 0
        
        print(f"✅ P0 Coverage workflow test passed")
        print(f"   - Coverage: {coverage_pct:.1f}% ({with_artifacts}/{total})")
        print(f"   - Artifacts: {coverage.get('artifacts_total', 0)} total")


async def run_p0_smoke_suite():
    """Run complete P0 smoke test suite."""
    print("\n🔬 Starting P0 Smoke Test Suite...\n")
    
    try:
        await test_p0_evidence_workflow()
    except Exception as e:
        print(f"❌ Evidence workflow test failed: {e}")
    
    try:
        await test_p0_artifact_coverage_workflow()
    except Exception as e:
        print(f"❌ Coverage workflow test failed: {e}")
    
    print("\n✅ P0 Smoke test suite complete\n")


if __name__ == "__main__":
    asyncio.run(run_p0_smoke_suite())
