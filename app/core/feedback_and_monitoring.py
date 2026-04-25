"""Operator feedback workflow management."""

from datetime import datetime
from typing import Dict, Optional


class FeedbackCollector:
    """Collect operator feedback on outputs and evidence."""
    
    @staticmethod
    def create_feedback_record(
        operator_id: str,
        output_id: int,
        feedback_type: str,  # "validates", "missing_evidence", "incorrect", "out_of_scope"
        evidence_id: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> Dict:
        """Create feedback record.
        
        Args:
            operator_id: Operator identifier
            output_id: Output being reviewed
            feedback_type: Type of feedback
            evidence_id: Optional linked evidence
            comment: Optional comment
        
        Returns:
            Feedback record dictionary
        """
        return {
            "operator_id": operator_id,
            "output_id": output_id,
            "evidence_id": evidence_id,
            "feedback_type": feedback_type,
            "comment": comment,
            "created_at": datetime.now().isoformat(),
            "status": "pending_review",
        }
    
    @staticmethod
    def summarize_feedback(feedback_records: list) -> Dict:
        """Summarize feedback statistics.
        
        Args:
            feedback_records: List of feedback records
        
        Returns:
            Summary dictionary
        """
        counts = {
            "validates": 0,
            "missing_evidence": 0,
            "incorrect": 0,
            "out_of_scope": 0,
        }
        
        for record in feedback_records:
            ftype = record.get("feedback_type", "unknown")
            if ftype in counts:
                counts[ftype] += 1
        
        return {
            "total_feedback": len(feedback_records),
            "by_type": counts,
            "validation_rate": counts["validates"] / len(feedback_records) if feedback_records else 0,
        }


class MonitoringService:
    """Pipeline monitoring and metrics collection."""
    
    @staticmethod
    def record_pipeline_metric(metric_name: str, value: float, tags: Dict = None) -> Dict:
        """Record a pipeline metric.
        
        Args:
            metric_name: Name of metric
            value: Metric value
            tags: Optional tags for filtering
        
        Returns:
            Metric record
        """
        return {
            "name": metric_name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or {},
        }
    
    @staticmethod
    def create_pipeline_health_check() -> Dict:
        """Create health check report for pipeline.
        
        Returns:
            Health check dictionary
        """
        return {
            "status": "healthy",
            "components": {
                "discovery": {"status": "ok", "last_run": None},
                "fetch": {"status": "ok", "last_run": None},
                "normalize": {"status": "ok", "last_run": None},
                "extract": {"status": "ok", "last_run": None},
                "score": {"status": "ok", "last_run": None},
            },
            "checks_timestamp": datetime.now().isoformat(),
        }
    
    @staticmethod
    def detect_anomalies(metrics: list) -> list:
        """Detect anomalies in recent metrics.
        
        Args:
            metrics: List of metric records
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Placeholder anomaly detection logic
        for metric in metrics:
            if metric.get("value", 0) > 1000:
                anomalies.append({
                    "type": "high_value",
                    "metric": metric.get("name"),
                    "value": metric.get("value"),
                })
        
        return anomalies
