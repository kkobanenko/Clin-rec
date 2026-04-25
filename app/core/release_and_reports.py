"""Release governance and output management models."""

from datetime import datetime
from typing import Dict, Optional


class OutputReleaseManager:
    """Manage output release workflow."""
    
    VALID_STATUSES = {"draft", "pending_review", "approved", "rejected", "released"}
    
    @staticmethod
    def create_release_request(
        output_id: int,
        reviewer_id: str,
        notes: Optional[str] = None,
    ) -> Dict:
        """Create output release request."""
        return {
            "output_id": output_id,
            "reviewer_id": reviewer_id,
            "notes": notes,
            "requested_at": datetime.now().isoformat(),
            "status": "requested",
        }
    
    @staticmethod
    def approve_release(request_id: int, approved_by: str) -> Dict:
        """Approve release request."""
        return {
            "request_id": request_id,
            "approved_by": approved_by,
            "approved_at": datetime.now().isoformat(),
            "status": "approved",
        }
    
    @staticmethod
    def complete_release(output_id: int, released_by: str) -> Dict:
        """Complete release process."""
        return {
            "output_id": output_id,
            "released_by": released_by,
            "released_at": datetime.now().isoformat(),
            "status": "released",
        }


class MockPipelineRunner:
    """Mock pipeline runner for testing."""
    
    async def discover_documents(self) -> int:
        """Mock discovery execution."""
        return 23
    
    async def fetch_artifacts(self) -> int:
        """Mock artifact fetching."""
        return 22
    
    async def normalize_documents(self) -> int:
        """Mock document normalization."""
        return 22
    
    async def extract_entities(self) -> int:
        """Mock entity extraction."""
        return 20
    
    async def score_evidence(self) -> int:
        """Mock evidence scoring."""
        return 20


class ReportGenerator:
    """Generate pilot reports and summaries."""
    
    @staticmethod
    def generate_p0_report(metrics: Dict) -> Dict:
        """Generate P0 completion report."""
        return {
            "report_type": "P0_completion",
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "status": "complete",
        }
    
    @staticmethod
    def generate_p1_report(pilot_results: Dict) -> Dict:
        """Generate P1 pilot report."""
        return {
            "report_type": "P1_pilot",
            "timestamp": datetime.now().isoformat(),
            "results": pilot_results,
            "recommendations": [],
            "status": "complete",
        }
    
    @staticmethod
    def generate_p2_report(completeness_data: Dict) -> Dict:
        """Generate P2 completeness report."""
        return {
            "report_type": "P2_completeness",
            "timestamp": datetime.now().isoformat(),
            "data": completeness_data,
            "coverage_pct": completeness_data.get("coverage_pct", 0),
            "status": "complete",
        }
