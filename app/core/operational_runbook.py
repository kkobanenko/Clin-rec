"""Operational runbook and procedure utilities."""

from typing import Dict, List, Optional


class OperationalRunbook:
    """Standard operational procedures."""
    
    PROCEDURES = {
        "emergency_shutdown": {
            "title": "Emergency Shutdown",
            "steps": [
                "Stop all workers: docker-compose stop worker",
                "Drain pending tasks: docker-compose logs worker | grep 'task'",
                "Backup database emergency: pg_dump > emergency.sql",
                "Shutdown API: docker-compose stop app",
                "Verify shutdown: docker-compose ps",
            ],
            "rollback": "docker-compose up -d",
        },
        "database_recovery": {
            "title": "Database Recovery",
            "steps": [
                "Check PostgreSQL health: psql -c 'SELECT version();'",
                "Identify corruption: pg_dump --schema-only | head -100",
                "Restore from backup if needed",
                "Verify integrity: python scripts/verify_db_integrity.py",
            ],
            "duration_minutes": 30,
        },
        "artifact_cleanup": {
            "title": "Clean Old Artifacts",
            "steps": [
                "Identify artifacts >30 days old",
                "Backup to cold storage",
                "Delete from MinIO",
                "Verify deletion",
            ],
            "duration_minutes": 60,
        },
    }
    
    @staticmethod
    def get_procedure(procedure_id: str) -> Dict:
        """Get operational procedure."""
        return OperationalRunbook.PROCEDURES.get(
            procedure_id,
            {"title": "Unknown", "steps": [], "duration_minutes": 0}
        )
    
    @staticmethod
    def start_procedure_execution(procedure_id: str, executed_by: str) -> Dict:
        """Start executing procedure."""
        return {
            "procedure_id": procedure_id,
            "executed_by": executed_by,
            "started_at": __import__('datetime').datetime.now().isoformat(),
            "status": "in_progress",
            "steps_completed": 0,
        }
    
    @staticmethod
    def complete_procedure(execution_id: str, notes: Optional[str] = None) -> Dict:
        """Complete procedure execution."""
        return {
            "execution_id": execution_id,
            "status": "completed",
            "completed_at": __import__('datetime').datetime.now().isoformat(),
            "notes": notes,
        }


class PerformanceBaseline:
    """Track performance baselines for anomaly detection."""
    
    @staticmethod
    def set_baseline(metric_name: str, baseline_value: float) -> Dict:
        """Set performance baseline."""
        return {
            "metric": metric_name,
            "baseline_value": baseline_value,
            "set_at": __import__('datetime').datetime.now().isoformat(),
        }
    
    @staticmethod
    def compare_to_baseline(metric_name: str, current_value: float, baseline_value: float) -> Dict:
        """Compare metric to baseline."""
        variance_pct = ((current_value - baseline_value) / baseline_value * 100) if baseline_value else 0
        status = "ok" if abs(variance_pct) < 10 else "warning" if abs(variance_pct) < 25 else "critical"
        
        return {
            "metric": metric_name,
            "current_value": current_value,
            "baseline_value": baseline_value,
            "variance_pct": variance_pct,
            "status": status,
        }
