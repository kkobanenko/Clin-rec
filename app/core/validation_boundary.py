"""Validation and error boundary utilities."""

from typing import Any, Dict, Tuple


def validate_artifact_data(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate artifact data completeness.
    
    Args:
        artifact: Artifact dictionary
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['id', 'document_version_id', 'artifact_type', 'raw_path', 'content_hash']
    
    for field in required_fields:
        if field not in artifact:
            return False, f"Missing required field: {field}"
    
    if not artifact.get('raw_path'):
        return False, "Artifact path is empty"
    
    return True, ""


def validate_evidence_data(evidence: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate evidence record data.
    
    Args:
        evidence: Evidence record
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['id', 'context_id', 'molecule_from_id', 'molecule_to_id', 'relation_type']
    
    for field in required_fields:
        if field not in evidence:
            return False, f"Missing required field: {field}"
    
    return True, ""


def safe_get_nested(data: Dict, key_path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.
    
    Args:
        data: Dictionary to access
        key_path: Dot-separated path (e.g., "items.0.name")
        default: Default value if path not found
    
    Returns:
        Value at path or default
    """
    try:
        keys = key_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list):
                try:
                    value = value[int(key)]
                except (ValueError, IndexError):
                    return default
            else:
                return default
        return value if value is not None else default
    except Exception:
        return default


def create_error_boundary_response(error: Exception, context: Dict = None) -> Dict:
    """Create error boundary response for API.
    
    Args:
        error: Exception that occurred
        context: Optional context information
    
    Returns:
        Error response dictionary
    """
    return {
        "error": str(error),
        "error_type": type(error).__name__,
        "context": context or {},
        "status": "error",
    }


def validate_pagination_params(page: int, page_size: int) -> Tuple[bool, int, int]:
    """Validate and normalize pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page
    
    Returns:
        (is_valid, normalized_page, normalized_page_size)
    """
    # Validate page
    if page < 1:
        page = 1
    
    # Validate page size
    if page_size < 1:
        page_size = 50
    if page_size > 500:
        page_size = 500
    
    return True, page, page_size
