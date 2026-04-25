"""API error and response helpers."""

from typing import Any, Dict, Optional


class APIResponse:
    """Standard API response wrapper."""
    
    @staticmethod
    def success(data: Any, total: Optional[int] = None, message: str = "Success") -> Dict:
        """Create success response."""
        response = {
            "success": True,
            "message": message,
            "data": data,
        }
        if total is not None:
            response["total"] = total
        return response
    
    @staticmethod
    def error(code: str, message: str, status_code: int = 400) -> Dict:
        """Create error response."""
        return {
            "success": False,
            "error_code": code,
            "error_message": message,
            "status_code": status_code,
        }
    
    @staticmethod
    def paginated(items: list, page: int, page_size: int, total: int) -> Dict:
        """Create paginated response."""
        pages = (total + page_size - 1) // page_size if page_size else 1
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages,
        }


class ErrorCatalog:
    """Standardized error codes and messages."""
    
    ERRORS = {
        "DOCUMENT_NOT_FOUND": {"message": "Document not found", "status": 404},
        "ARTIFACT_NOT_FOUND": {"message": "Artifact not found", "status": 404},
        "INVALID_PAGINATION": {"message": "Invalid pagination parameters", "status": 400},
        "PIPELINE_ERROR": {"message": "Pipeline execution failed", "status": 500},
        "EXTRACTION_FAILED": {"message": "Entity extraction failed", "status": 500},
    }
    
    @staticmethod
    def get_error(code: str) -> Dict:
        """Get error by code."""
        return ErrorCatalog.ERRORS.get(code, {
            "message": "Unknown error",
            "status": 500
        })
