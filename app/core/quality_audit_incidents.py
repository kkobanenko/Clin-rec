"""Quality metrics and audit trail utilities."""

from datetime import datetime
from typing import Dict, List


class QualityMetrics:
    """Track quality metrics during pipeline execution."""
    
    @staticmethod
    def calculate_extraction_quality(
        total_entities: int,
        validated_entities: int,
    ) -> float:
        """Calculate entity extraction quality rate."""
        return (validated_entities / total_entities * 100) if total_entities else 0
    
    @staticmethod
    def calculate_evidence_confidence(
        evidence_records: List[Dict],
    ) -> float:
        """Calculate average evidence confidence."""
        if not evidence_records:
            return 0
        
        total_score = sum(e.get("final_fragment_score", 0) for e in evidence_records)
        return total_score / len(evidence_records)
    
    @staticmethod
    def calculate_pipeline_success_rate(
        total_documents: int,
        successfully_processed: int,
    ) -> float:
        """Calculate pipeline processing success rate."""
        return (successfully_processed / total_documents * 100) if total_documents else 0


class AuditTrail:
    """Immutable audit trail for operator actions."""
    
    @staticmethod
    def log_action(
        operator_id: str,
        action_type: str,  # "view", "download", "approve", "reject"
        resource_type: str,  # "document", "output", "evidence"
        resource_id: int,
        details: Dict = None,
    ) -> Dict:
        """Log an operator action."""
        return {
            "operator_id": operator_id,
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
    
    @staticmethod
    def generate_audit_report(
        operator_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict:
        """Generate audit report for operator."""
        return {
            "operator_id": operator_id,
            "period": {"start": start_date, "end": end_date},
            "actions_logged": 0,
            "generated_at": datetime.now().isoformat(),
        }


class IncidentDirectory:
    """Directory of known incidents and resolutions."""
    
    KNOWN_INCIDENTS = {
        "artifact_fetch_timeout": {
            "description": "Artifact fetch operation timed out",
            "resolution": "Check S3 connectivity and artifact size",
            "severity": "medium",
        },
        "entity_extraction_crash": {
            "description": "Entity extraction process crashed",
            "resolution": "Check document encoding and restart extraction",
            "severity": "high",
        },
        "database_connection_lost": {
            "description": "Database connection lost",
            "resolution": "Check PostgreSQL server status and connection pool",
            "severity": "critical",
        },
    }
    
    @staticmethod
    def lookup_incident(incident_id: str) -> Dict:
        """Look up incident resolution."""
        return IncidentDirectory.KNOWN_INCIDENTS.get(
            incident_id,
            {
                "description": "Unknown incident",
                "resolution": "Check application logs for details",
                "severity": "unknown",
            }
        )
    
    @staticmethod
    def create_incident_report(
        incident_id: str,
        timestamp: str,
        affected_resource: str,
    ) -> Dict:
        """Create incident report."""
        incident = IncidentDirectory.lookup_incident(incident_id)
        return {
            "incident_id": incident_id,
            "timestamp": timestamp,
            "affected_resource": affected_resource,
            "description": incident.get("description"),
            "resolution_steps": incident.get("resolution"),
            "severity": incident.get("severity"),
        }
