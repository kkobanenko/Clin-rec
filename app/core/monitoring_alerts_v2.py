"""Pipeline monitoring and health check utilities."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MonitoringServiceV2:
    """Enhanced pipeline monitoring."""
    
    @staticmethod
    def create_health_summary() -> Dict:
        """Create comprehensive health summary."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "uptime_hours": 0,
            "services": {
                "api": {"status": "up", "latency_ms": 50},
                "worker": {"status": "up", "tasks_processed": 0},
                "database": {"status": "up", "connections": 5},
                "storage": {"status": "up", "available_gb": 0},
            },
            "alerts": [],
        }
    
    @staticmethod
    def track_pipeline_metric(metric_name: str, value: float, threshold: Optional[float] = None) -> Dict:
        """Track pipeline metric with alerting."""
        alert = None
        if threshold and value > threshold:
            alert = {
                "level": "warning",
                "message": f"Metric {metric_name} exceeds threshold {threshold}",
            }
        
        return {
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "alert": alert,
        }
    
    @staticmethod
    def calculate_error_rate(total_operations: int, failed_operations: int) -> float:
        """Calculate error rate for operations."""
        return (failed_operations / total_operations * 100) if total_operations else 0
    
    @staticmethod
    def detect_performance_degradation(
        current_latency: float,
        baseline_latency: float,
        threshold_pct: float = 50.0,
    ) -> bool:
        """Detect if performance has degraded."""
        if baseline_latency == 0:
            return False
        
        degradation_pct = ((current_latency - baseline_latency) / baseline_latency) * 100
        return degradation_pct > threshold_pct


class AlertingService:
    """Service for pipeline alerting."""
    
    @staticmethod
    def create_alert(
        severity: str,  # "info", "warning", "critical"
        title: str,
        message: str,
        component: str,
    ) -> Dict:
        """Create alert."""
        return {
            "severity": severity,
            "title": title,
            "message": message,
            "component": component,
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False,
        }
    
    @staticmethod
    def resolve_alert(alert_id: str, resolution: str) -> Dict:
        """Resolve alert."""
        return {
            "alert_id": alert_id,
            "resolution": resolution,
            "resolved_at": datetime.now().isoformat(),
            "status": "resolved",
        }
