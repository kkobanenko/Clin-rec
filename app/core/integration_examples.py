"""Integration examples and quick-start guides."""

from typing import Dict, List


class QuickStartGuide:
    """Quick-start guide for operators."""
    
    @staticmethod
    def get_setup_instructions() -> Dict:
        """Get setup instructions."""
        return {
            "title": "CR Intelligence Platform - Quick Start",
            "version": "2.1",
            "prerequisites": [
                "Docker and Docker Compose installed",
                "4GB RAM available",
                "20GB disk space for artifacts",
                "PostgreSQL (optional, included in Docker)",
            ],
            "steps": [
                {
                    "step": 1,
                    "name": "Clone Repository",
                    "command": "git clone <repo> && cd Clin-rec",
                },
                {
                    "step": 2,
                    "name": "Start Docker Stack",
                    "command": "docker compose up -d",
                },
                {
                    "step": 3,
                    "name": "Check Health",
                    "command": "curl http://localhost:8000/health",
                },
                {
                    "step": 4,
                    "name": "Open UI",
                    "command": "open http://localhost:8501",
                },
            ],
            "estimated_time": "5 minutes",
        }
    
    @staticmethod
    def get_common_workflows() -> List[Dict]:
        """Get common operator workflows."""
        return [
            {
                "workflow": "Browse Documents",
                "steps": [
                    "Navigate to Documents page",
                    "View document list with metadata",
                    "Click document to view artifacts",
                ],
                "time": "< 1 minute",
            },
            {
                "workflow": "Review Evidence",
                "steps": [
                    "Navigate to Evidence page",
                    "Use pagination to browse evidence",
                    "Filter by relation type or review status",
                    "Provide feedback on accuracy",
                ],
                "time": "5-10 minutes",
            },
            {
                "workflow": "Download Artifacts",
                "steps": [
                    "Find document in Documents page",
                    "Click Download button",
                    "Select artifact format (PDF/JSON/HTML)",
                ],
                "time": "< 1 minute",
            },
        ]


class ExampleUseCases:
    """Example use cases for the platform."""
    
    @staticmethod
    def get_clinical_trial_workflow() -> Dict:
        """Get clinical trial workflow example."""
        return {
            "title": "Clinical Trial Eligibility Assessment",
            "description": "Automatically extract eligibility criteria and molecular targets from trial documents",
            "process": [
                "Upload clinical trial protocols (PDF)",
                "System extracts inclusion/exclusion criteria",
                "System maps molecular targets to indication",
                "Evidence links criteria to supporting data",
                "Operator reviews and validates extraction",
                "Export structured eligibility criteria",
            ],
            "time_saved": "70% reduction in manual review time",
            "accuracy": ">95% for structured criteria extraction",
        }
    
    @staticmethod
    def get_regulatory_compliance_workflow() -> Dict:
        """Get regulatory compliance workflow."""
        return {
            "title": "Regulatory Requirement Tracking",
            "description": "Track regulatory requirements across documents and monitor compliance",
            "process": [
                "Ingest regulatory guidance documents",
                "Extract requirement statements",
                "Link requirements to internal policies",
                "Track compliance across organization",
                "Generate compliance reports",
            ],
            "compliance_coverage": ">90% of regulatory requirements tracked",
            "reporting_frequency": "Monthly automated reports",
        }


class APIQuickReference:
    """API quick reference for developers."""
    
    @staticmethod
    def get_api_endpoints() -> Dict:
        """Get API endpoints reference."""
        return {
            "base_url": "http://localhost:8000",
            "health": {
                "endpoint": "GET /health",
                "description": "System health check",
            },
            "documents": {
                "list": "GET /documents?page=1&page_size=50",
                "get": "GET /documents/{id}",
                "create": "POST /documents",
            },
            "evidence": {
                "list": "GET /matrix/pair-evidence?page=1&relation_type=interaction&min_score=0.7",
                "get": "GET /evidence/{id}",
                "create_feedback": "POST /evidence/{id}/feedback",
            },
            "monitoring": {
                "health": "GET /health",
                "metrics": "GET /metrics",
            },
        }
    
    @staticmethod
    def get_curl_examples() -> List[str]:
        """Get curl examples."""
        return [
            "# Check system health",
            "curl -s http://localhost:8000/health | jq .",
            "",
            "# Get documents",
            "curl -s 'http://localhost:8000/documents?page=1&page_size=10' | jq .",
            "",
            "# Get evidence with filtering",
            "curl -s 'http://localhost:8000/matrix/pair-evidence?relation_type=interaction' | jq .",
        ]
